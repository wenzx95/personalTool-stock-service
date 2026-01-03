"""板块相关API"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.service.sector_service import SectorService
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter()
sector_service = SectorService()


@router.get("/list")
async def get_sector_list():
    """获取板块列表"""
    logger.info("=" * 60)
    logger.info("[API调用] 开始获取板块列表")
    start_time = time.time()
    try:
        logger.info("[步骤1] 调用sector_service.get_sector_list()")
        sectors = sector_service.get_sector_list()
        elapsed = time.time() - start_time
        logger.info(f"[步骤2] 获取到 {len(sectors)} 个板块，耗时 {elapsed:.3f}秒")
        
        result = {
            "code": 200,
            "message": "success",
            "data": {
                "sectors": sectors,
                "total": len(sectors)
            }
        }
        logger.info(f"[API完成] 板块列表获取成功，总耗时 {time.time() - start_time:.3f}秒")
        logger.info("=" * 60)
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[API异常] 获取板块列表失败: {e}，耗时 {elapsed:.3f}秒", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/detail")
async def get_sector_detail(code: str):
    """获取板块详情"""
    try:
        detail = sector_service.get_sector_detail(code)
        if not detail:
            raise HTTPException(status_code=404, detail="板块不存在")
        return {
            "code": 200,
            "message": "success",
            "data": detail
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranking")
async def get_sector_ranking(order_by: str = "change_pct", limit: int = 100):
    """获取板块涨跌幅排名"""
    try:
        sectors = sector_service.get_sector_ranking(order_by, limit)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "sectors": sectors,
                "order_by": order_by,
                "total": len(sectors)
            }
        }
    except Exception as e:
        logger.error(f"获取板块排名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/fund-flow")
async def get_sector_fund_flow(code: str):
    """获取板块资金流向"""
    try:
        fund_flow = sector_service.get_sector_fund_flow(code)
        return {
            "code": 200,
            "message": "success",
            "data": fund_flow
        }
    except Exception as e:
        logger.error(f"获取板块资金流向失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rotation")
async def get_sector_rotation():
    """获取板块轮动分析"""
    try:
        sectors = sector_service.get_sector_list()
        rotation_data = sector_service.analyze_sector_rotation(sectors)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "rotation": rotation_data,
                "total": len(rotation_data)
            }
        }
    except Exception as e:
        logger.error(f"获取板块轮动分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-table")
async def get_sector_review_table():
    """获取板块复盘表格数据（用于表格展示）"""
    logger.info("=" * 60)
    logger.info("[API调用] 开始获取板块复盘表格数据")
    start_time = time.time()
    try:
        logger.info("[步骤1] 调用sector_service.get_sector_review_table()")
        table_data = sector_service.get_sector_review_table()
        elapsed = time.time() - start_time
        logger.info(f"[步骤2] 获取到 {len(table_data)} 条表格数据，耗时 {elapsed:.3f}秒")
        
        result = {
            "code": 200,
            "message": "success",
            "data": {
                "table": table_data,
                "total": len(table_data),
                "columns": [
                    {"key": "sector_name", "label": "板块名称"},
                    {"key": "sector_code", "label": "板块代码"},
                    {"key": "change_pct", "label": "涨跌幅(%)"},
                    {"key": "total_stocks", "label": "股票总数"},
                    {"key": "up_count", "label": "上涨家数"},
                    {"key": "down_count", "label": "下跌家数"},
                    {"key": "limit_up_count", "label": "涨停家数"},
                    {"key": "limit_down_count", "label": "跌停家数"},
                    {"key": "turnover_rate", "label": "换手率(%)"},
                    {"key": "volume", "label": "成交量"},
                    {"key": "amount", "label": "成交额"},
                    {"key": "up_ratio", "label": "上涨比例(%)"},
                    {"key": "limit_up_ratio", "label": "涨停占比(%)"}
                ]
            }
        }
        logger.info(f"[API完成] 板块复盘表格数据获取成功，总耗时 {time.time() - start_time:.3f}秒")
        logger.info("=" * 60)
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[API异常] 获取板块复盘表格数据失败: {e}，耗时 {elapsed:.3f}秒", exc_info=True)
        logger.info("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))

