"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 应用配置
    APP_NAME: str = "PersonalTool Stock Service"
    DEBUG: bool = False
    
    # Java服务地址
    JAVA_SERVICE_URL: str = "http://java-service:8080"
    
    # 同花顺配置
    THS_BASE_URL: str = "https://q.10jqka.com.cn"
    
    # 数据抓取配置
    CRAWL_DELAY: float = 2.0  # 抓取延迟（秒）
    REQUEST_TIMEOUT: int = 30  # 请求超时（秒）
    
    # 代理配置
    PROXY_URL: Optional[str] = "http://127.0.0.1:7890"  # 代理服务器地址
    
    # 定时任务配置
    SCHEDULE_ENABLED: bool = True
    DAILY_REVIEW_TIME: str = "15:30"  # 每日复盘时间
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

