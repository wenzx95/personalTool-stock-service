"""市场相关API"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.service.market_service import MarketService
from app.service.market_review_service import MarketReviewService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
market_service = MarketService()
market_review_service = MarketReviewService()


@router.get("/emotion")
async def get_market_emotion():
    """获取市场情绪分析"""
    try:
        emotion_data = market_service.get_market_emotion()
        return {
            "code": 200,
            "message": "success",
            "data": emotion_data
        }
    except Exception as e:
        logger.error(f"获取市场情绪失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_market_statistics():
    """获取市场统计数据"""
    try:
        statistics = market_service.crawler.get_market_statistics()
        return {
            "code": 200,
            "message": "success",
            "data": statistics
        }
    except Exception as e:
        logger.error(f"获取市场统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review")
async def get_market_review(trade_date: Optional[str] = None):
    """
    获取市场复盘数据
    
    参数:
        trade_date: 交易日期，格式：YYYYMMDD，默认为今天
        例如：20250105
    
    返回:
        包含以下字段的市场复盘数据:
        - date: 日期
        - volume: 成交量
        - red_count: 红盘（上涨家数）
        - green_count: 绿盘（下跌家数）
        - limit_up_count: 涨停
        - limit_down_count: 跌停
        - zt_count: 炸板数量
        - zt_rate: 炸板率
        - total_continuous_limit: 总连板
        - continuous_limit_rate: 连板率
        - four_plus_count: 4板及以上个数
        - four_plus_stocks: 4板及以上个股
        - two_board_count: 二板个数
        - three_board_count: 三板个数
        - three_board_stocks: 三板个股
        - total_stocks: 总家数
    """
    try:
        logger.info(f"[API] 开始获取市场复盘数据，日期: {trade_date}")
        review_data = market_review_service.get_market_review_data(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": review_data
        }
    except Exception as e:
        logger.error(f"获取市场复盘数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


