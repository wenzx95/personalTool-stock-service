"""市场相关API"""
from fastapi import APIRouter, HTTPException
from app.service.market_service import MarketService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
market_service = MarketService()


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


