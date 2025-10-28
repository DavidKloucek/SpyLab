import wireup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import wireup.integration
import wireup.integration.fastapi
from app.container import container
from app.app_config import (
    ALLOWED_ORIGINS,
    APP_TITLE,
    GQL_PATH,
    IMG_TEMP_DIR_URL_PATH,
    IMG_ORIG_DIR_URL_PATH,
    IMG_TEMP_DIR,
    IMG_ORIG_DIR,
)
from app.router import router
from strawberry.fastapi import GraphQLRouter
from app.gql_schema import get_context, schema


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    app.mount(IMG_TEMP_DIR_URL_PATH, StaticFiles(directory=IMG_TEMP_DIR), name="preview")
    app.mount(IMG_ORIG_DIR_URL_PATH, StaticFiles(directory=IMG_ORIG_DIR), name="original")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
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

    graphql_app = GraphQLRouter(schema, context_getter=get_context)
    app.include_router(graphql_app, prefix=GQL_PATH)

    return app


app = create_app()
