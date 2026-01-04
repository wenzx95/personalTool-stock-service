"""
PersonalTool Stock Service
个人工具集A股分析服务
提供A股数据抓取和金融分析功能
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
import logging
import time
from datetime import datetime

# 配置日志
import logging.handlers

# 确保log目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'log')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

# 配置日志：同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )  # 文件输出
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日志文件: {log_file}")

from app.api import stock, sector, market
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
    lifespan=lifespan,
    # 配置Swagger UI，确保"Try it out"功能可用
    swagger_ui_parameters={
        "tryItOutEnabled": True,  # 启用"Try it out"功能
        "persistAuthorization": True,  # 持久化授权信息
        "displayRequestDuration": True,  # 显示请求耗时
    }
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（用于测试页面）
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的详细信息"""
    start_time = time.time()
    request_id = f"{int(time.time() * 1000)}"
    
    logger.info(f"[请求开始] ID={request_id} | {request.method} {request.url.path} | 客户端={request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[请求完成] ID={request_id} | 状态码={response.status_code} | 耗时={process_time:.3f}秒")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[请求异常] ID={request_id} | 错误={str(e)} | 耗时={process_time:.3f}秒", exc_info=True)
        raise

# 注册路由
app.include_router(stock.router, prefix="/api/stock", tags=["个股"])
app.include_router(sector.router, prefix="/api/sector", tags=["板块"])
app.include_router(market.router, prefix="/api/market", tags=["市场"])

logger.info("=" * 60)
logger.info("PersonalTool Stock Service 启动中...")
logger.info(f"服务地址: http://0.0.0.0:8000")
logger.info(f"API文档: http://localhost:8000/docs")
logger.info(f"测试页面: http://localhost:8000/test")
logger.info("=" * 60)


@app.get("/test", include_in_schema=False)
async def test_page():
    """API测试页面"""
    test_file = os.path.join(static_dir, "test.html")
    if os.path.exists(test_file):
        return FileResponse(test_file)
    return {"message": "测试页面未找到"}


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

