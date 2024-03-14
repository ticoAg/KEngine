import aiohttp
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.serve.apis import MakeFastAPIOffline, mount_app_routes
from src.serve.utils import parse_args

fetch_timeout = aiohttp.ClientTimeout(total=3 * 3600)


# @app.get("/v1/models", dependencies=[Depends(check_api_key)])
# async def show_available_models():
#     models = await fetch_remote(controller_address + "/list_models", None, "models")


#     models.sort()
#     # TODO: return real model permission details
#     model_cards = []
#     for m in models:
#         model_cards.append(ModelCard(id=m, root=m, permission=[ModelPermission()]))
#     return ModelList(data=model_cards)


def create_app(args):
    app = FastAPI(
        title="KEngine API",
    )
    MakeFastAPIOffline(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=args.allowed_origins,
        allow_credentials=args.allow_credentials,
        allow_methods=args.allowed_methods,
        allow_headers=args.allowed_headers,
    )

    mount_app_routes(app)

    return app


if __name__ == "__main__":
    args = parse_args()
    app = create_app(args)
    uvicorn.run(app, host=args.host, port=args.port)
