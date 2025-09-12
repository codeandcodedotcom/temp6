# import time
# import requests
# import jwt
# from jwt.algorithms import RSAAlgorithm
# from flask import request, jsonify
# from functools import wraps
# from app.config import Config
# from app.utils.logger import get_logger

# logger = get_logger(__name__)

# JWKS_CACHE = {"keys": None, "last_fetched": 0}


# def _get_jwks():
#     """
#     Fetch and cache JWKS (public signing keys) from Microsoft Entra.
#     """
#     now = time.time()
#     if JWKS_CACHE["keys"] and (now - JWKS_CACHE["last_fetched"]) < 3600:
#         return JWKS_CACHE["keys"]

#     resp = requests.get(Config.ENTRA_JWKS_URL, timeout=5)
#     resp.raise_for_status()
#     jwks = resp.json()
#     JWKS_CACHE["keys"] = jwks
#     JWKS_CACHE["last_fetched"] = now
#     return jwks


# def _validate_jwt(token: str):
#     """
#     Validate a JWT access token from Microsoft Entra.
#     - Verifies signature against JWKS
#     - Checks issuer, audience, expiry
#     """
#     # Decode header to find which key ID (kid) signed this token
#     unverified_header = jwt.get_unverified_header(token)

#     jwks = _get_jwks()
#     key = None
#     for jwk in jwks.get("keys", []):
#         if jwk["kid"] == unverified_header["kid"]:
#             key = RSAAlgorithm.from_jwk(jwk)
#             break

#     if key is None:
#         raise Exception("Unable to find matching JWK for token")

#     decoded = jwt.decode(
#         token,
#         key=key,
#         algorithms=["RS256"],
#         audience=Config.ENTRA_CLIENT_ID,
#         issuer=f"https://login.microsoftonline.com/{Config.ENTRA_TENANT_ID}/v2.0",
#     )
#     return decoded


# def require_jwt(func):
#     """
#     Flask decorator: requires a valid JWT access token.
#     Expects Authorization: Bearer <token>
#     """
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         auth_header = request.headers.get("Authorization", "")
#         if not auth_header.startswith("Bearer "):
#             return jsonify({"error": "Missing or malformed Authorization header"}), 401

#         token = auth_header.split(" ", 1)[1].strip()
#         try:
#             decoded = _validate_jwt(token)
#             request.user = decoded  # attach claims to request for downstream use
#             logger.debug(f"JWT validated for sub={decoded.get('sub')}")
#         except Exception as e:
#             logger.warning(f"JWT validation failed: {e}")
#             return jsonify({"error": "Invalid or expired token"}), 401

#         return func(*args, **kwargs)

#     return wrapper










# app/utils/jwt_auth.py
# import time
from functools import wraps
from flask import request, jsonify, current_app, g
import jwt  # PyJWT
from jwt import PyJWKClient
from app.config import Config

_jwks_clients = {}  # cache JWK clients per issuer/jwks_url


def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    """Return a cached PyJWKClient for jwks_url."""
    client = _jwks_clients.get(jwks_url)
    if client is None:
        client = PyJWKClient(jwks_url)
        _jwks_clients[jwks_url] = client
    return client


def _validate_jwt(token: str) -> dict:
    """
    Validate an incoming JWT using JWKS.
    Returns the decoded claims (dict) on success, raises Exception on failure.
    Expects Config to have:
      - ENTRA_JWKS_URL (or JWKs URL)
      - ENTRA_AUDIENCE (expected audience) optional
      - ENTRA_ISSUER (expected issuer) optional
    """
    jwks_url = getattr(Config, "ENTRA_JWKS_URL", None) or getattr(Config, "JWKS_URL", None)
    if not jwks_url:
        raise RuntimeError("JWKS URL not configured (ENTRA_JWKS_URL)")

    client = _get_jwk_client(jwks_url)
    signing_key = client.get_signing_key_from_jwt(token).key

    options = {"verify_signature": True, "verify_aud": bool(getattr(Config, "ENTRA_AUDIENCE", None))}
    decoded = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "RS384", "RS512"],  # allowed algorithms
        audience=getattr(Config, "ENTRA_AUDIENCE", None),
        issuer=getattr(Config, "ENTRA_ISSUER", None),
        options=options,
    )
    return decoded


def require_jwt(func):
    """Flask decorator to require a Bearer JWT in Authorization header."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            claims = _validate_jwt(token)
            # Attach claims to flask.g for downstream use
            g.jwt_claims = claims
        except Exception as exc:
            current_app.logger.warning(f"JWT validation failed: {exc}")
            return jsonify({"error": "Invalid or expired token"}), 401
        return func(*args, **kwargs)
    return wrapper
