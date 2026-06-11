from app.api import router as api_router
from app.core.config import get_settings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    # 统一在应用工厂里完成配置读取、中间件装配和总路由挂载，
    # 这样 main.py 保持为纯入口文件，后续测试和部署也更容易复用。
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
