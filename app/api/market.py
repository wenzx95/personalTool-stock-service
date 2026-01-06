"""市场相关API"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from app.service.market_service import MarketService
from app.service.market_review_service import MarketReviewService
from app.models.database import MarketReviewModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
market_service = MarketService()
market_review_service = MarketReviewService()


class ReviewCreateRequest(BaseModel):
    """创建复盘请求"""
    date: str
    hot_sectors: Optional[List[str]] = []
    notes: Optional[str] = ""


class ReviewUpdateRequest(BaseModel):
    """更新复盘请求"""
    hot_sectors: Optional[List[str]] = []
    notes: Optional[str] = ""


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
    获取市场复盘数据（实时获取，不保存）

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


@router.get("/review/list")
async def get_review_list(limit: int = 100, offset: int = 0):
    """获取复盘记录列表"""
    try:
        logger.info(f"[API] 获取复盘列表 - limit={limit}, offset={offset}")
        reviews = MarketReviewModel.get_all(limit=limit, offset=offset)
        logger.info(f"[API] 成功获取 {len(reviews)} 条复盘记录")
        return {
            "code": 200,
            "message": "success",
            "data": reviews
        }
    except Exception as e:
        logger.error(f"[API] 获取复盘列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/detail/{date}")
async def get_review_detail(date: str):
    """获取指定日期的复盘记录"""
    try:
        review = MarketReviewModel.get_by_date(date)
        if review:
            return {
                "code": 200,
                "message": "success",
                "data": review
            }
        else:
            raise HTTPException(status_code=404, detail="记录不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取复盘详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/create")
async def create_review(request: ReviewCreateRequest):
    """
    创建复盘记录（自动获取当日市场数据）

    请求体:
        - date: 日期（YYYY-MM-DD格式）
        - hot_sectors: 热门板块列表
        - notes: 复盘笔记
    """
    try:
        # 先获取当日市场数据
        # 将YYYY-MM-DD转换为YYYYMMDD
        trade_date = request.date.replace('-', '')

        logger.info(f"[API] 开始创建复盘记录，日期: {trade_date}")

        # 获取市场数据
        market_data = market_review_service.get_market_review_data(trade_date)

        # 合并请求数据
        market_data['hot_sectors'] = request.hot_sectors
        market_data['notes'] = request.notes

        # 保存到数据库
        review_id = MarketReviewModel.create(market_data)

        if review_id:
            # 获取完整的记录
            review = MarketReviewModel.get_by_date(market_data['date'])
            return {
                "code": 200,
                "message": "复盘记录创建成功",
                "data": review
            }
        else:
            raise HTTPException(status_code=400, detail="该日期的记录已存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建复盘记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/review/update/{review_id}")
async def update_review(review_id: int, request: ReviewUpdateRequest):
    """更新复盘记录（只能更新热门板块和笔记）"""
    try:
        update_data = {
            'hot_sectors': request.hot_sectors,
            'notes': request.notes
        }

        success = MarketReviewModel.update(review_id, update_data)

        if success:
            # 获取更新后的记录
            from app.models.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM market_review WHERE id = ?', (review_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                from app.models.database import MarketReviewModel
                review = MarketReviewModel._row_to_dict(row)
                return {
                    "code": 200,
                    "message": "复盘记录更新成功",
                    "data": review
                }

        raise HTTPException(status_code=404, detail="记录不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新复盘记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/review/delete/{review_id}")
async def delete_review(review_id: int):
    """删除复盘记录"""
    try:
        success = MarketReviewModel.delete(review_id)

        if success:
            return {
                "code": 200,
                "message": "复盘记录删除成功",
                "data": None
            }
        else:
            raise HTTPException(status_code=404, detail="记录不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除复盘记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


