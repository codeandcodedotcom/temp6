@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "https://digital-dev.rolls-royce.com",
            "Access-Control-Allow-Credentials": "true",
        },
            )
