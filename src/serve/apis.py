import sys
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from src.protocol.api_protocol import BaseResponse
from src.serve.openai_api_server import check_api_key
from src.serve.utils import create_embeddings, document


def mount_app_routes(app: FastAPI):
    app.get("/", include_in_schema=False, response_model=BaseResponse, summary="swagger 文档")(document)

    app.post(
        "/v1/embeddings",
        tags=["embedding"],
        dependencies=[Depends(check_api_key)],
        summary="文本向量化",
    )(create_embeddings)

    app.post(
        "/v1/engines/{model_name}/embeddings",
        tags=["embedding"],
        dependencies=[Depends(check_api_key)],
        summary="文本向量化",
    )(create_embeddings)


def MakeFastAPIOffline(
    app: FastAPI,
    static_dir=Path(__file__).parent / "static",
    static_url="/static-offline-docs",
    docs_url: Optional[str] = "/docs",
    redoc_url: Optional[str] = "/redoc",
) -> None:
    """patch the FastAPI obj that doesn't rely on CDN for the documentation page"""

    openapi_url = app.openapi_url
    swagger_ui_oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url

    def remove_route(url: str) -> None:
        """
        remove original route from app
        """
        index = None
        for i, r in enumerate(app.routes):
            if r.path.lower() == url.lower():
                index = i
                break
        if isinstance(index, int):
            app.routes.pop(index)

    # Set up static file mount
    app.mount(
        static_url,
        StaticFiles(directory=Path(static_dir).as_posix()),
        name="static-offline-docs",
    )

    if docs_url is not None:
        remove_route(docs_url)
        remove_route(swagger_ui_oauth2_redirect_url)

        # Define the doc and redoc pages, pointing at the right files
        @app.get(docs_url, include_in_schema=False)
        async def custom_swagger_ui_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"
            return get_swagger_ui_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
                swagger_js_url=f"{root}{static_url}/swagger-ui-bundle.js",
                swagger_css_url=f"{root}{static_url}/swagger-ui.css",
                swagger_favicon_url=favicon,
            )

        @app.get(swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect() -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()

    if redoc_url is not None:
        remove_route(redoc_url)

        @app.get(redoc_url, include_in_schema=False)
        async def redoc_html(request: Request) -> HTMLResponse:
            root = request.scope.get("root_path")
            favicon = f"{root}{static_url}/favicon.png"

            return get_redoc_html(
                openapi_url=f"{root}{openapi_url}",
                title=app.title + " - ReDoc",
                redoc_js_url=f"{root}{static_url}/redoc.standalone.js",
                with_google_fonts=False,
                redoc_favicon_url=favicon,
            )
