"""定时任务调度"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.service.sector_service import SectorService
from app.service.market_service import MarketService
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """设置定时任务"""
    if not settings.SCHEDULE_ENABLED:
        return
    
    # 每日复盘任务（收盘后）
    hour, minute = map(int, settings.DAILY_REVIEW_TIME.split(':'))
    scheduler.add_job(
        daily_review_task,
        CronTrigger(hour=hour, minute=minute),
        id='daily_review',
        name='每日复盘任务'
    )
    
    logger.info("定时任务已启动")


async def daily_review_task():
    """每日复盘任务"""
    logger.info("开始执行每日复盘任务")
    try:
        # 抓取板块数据
        sector_service = SectorService()
        sectors = sector_service.get_sector_list()
        logger.info(f"抓取到 {len(sectors)} 个板块数据")
        
        # 分析市场情绪
        market_service = MarketService()
        emotion = market_service.get_market_emotion()
        logger.info(f"市场情绪得分: {emotion.get('emotion_score')}, 周期: {emotion.get('emotion_cycle')}")
        
        # 分析板块轮动
        rotation = sector_service.analyze_sector_rotation(sectors)
        logger.info(f"分析板块轮动，热点板块数: {len([r for r in rotation if r.get('hot_score', 0) > 70])}")
        
        # TODO: 将数据存储到数据库或发送到Java服务
        
        logger.info("每日复盘任务完成")
    except Exception as e:
        logger.error(f"每日复盘任务执行失败: {e}")


# 启动时设置定时任务
setup_scheduler()

