"""定时任务调度"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
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
    # TODO: 实现每日数据抓取和分析
    logger.info("每日复盘任务完成")


# 启动时设置定时任务
setup_scheduler()

