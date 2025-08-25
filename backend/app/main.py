import wireup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import wireup.integration
import wireup.integration.fastapi
from app.container import container
from app.app_config import APP_TITLE, IMG_TEMP_DIR, IMG_ORIG_DIR
from app.router import router


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE
    )
    app.mount("/preview", StaticFiles(directory=IMG_TEMP_DIR), name="preview")
    app.mount("/source_img", StaticFiles(directory=IMG_ORIG_DIR), name="original")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "http://localhost:9000",
            "http://localhost:3000",
            "http://localhost:5173"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api", tags=[])

    wireup.integration.fastapi.setup(container, app)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.detail,
                "statusCode": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "message": "Unexpected error has occured during processing your request, please contact the owner",
                "statusCode": 500,
            },
        )

    return app


app = create_app()
