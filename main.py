"""
PersonalTool Stock Service
个人工具集A股分析服务
提供A股数据抓取和金融分析功能
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api import stock, sector
from app.core.config import settings
from app.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    scheduler.start()
    yield
    # 关闭时
    scheduler.shutdown()


app = FastAPI(
    title="PersonalTool Stock Service",
    description="个人工具集A股分析服务 - A股数据抓取和金融分析",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stock.router, prefix="/api/stock", tags=["个股"])
app.include_router(sector.router, prefix="/api/sector", tags=["板块"])


@app.get("/")
async def root():
    """健康检查"""
    return {"message": "PersonalTool Stock Service is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

