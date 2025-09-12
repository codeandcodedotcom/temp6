from flask import Flask
from app.api import test, generation, health, questionnaire, submissions, kpi
from app.config import Config
from app.utils.logger import get_logger
from flask_cors import CORS

logger = get_logger(__name__)

def create_app():
    """
    Registers blueprints and initializes extensions.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS(app, origins=["http://localhost:3000"])
    CORS(app)

    app.register_blueprint(test.bp, url_prefix="/api/test")
    logger.info("Blueprint 'test' registered at /api/test")

    app.register_blueprint(generation.bp, url_prefix="/api/generation")
    logger.info("Blueprint 'generation' registered at /api/generation")

    app.register_blueprint(health.bp, url_prefix="/api")
    logger.info("Blueprint 'health' registered at /api/health")

    app.register_blueprint(questionnaire.bp, url_prefix="/api")
    logger.info("Blueprint 'questionnaire' registered at /api/questionnaire")

    app.register_blueprint(submissions.bp, url_prefix="/api")
    logger.info("Blueprint 'submissions' registered at /api/submissions")

    app.register_blueprint(kpi.bp, url_prefix="/api")
    logger.info("Blueprint 'kpi' registered at /api/kpi")

    return app






