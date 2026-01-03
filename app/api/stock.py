"""个股相关API"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter()


@router.get("/{code}/detail")
async def get_stock_detail(code: str):
    """获取个股详情"""
    # TODO: 实现个股数据抓取
    return {
        "code": code,
        "name": "示例股票",
        "message": "功能开发中"
    }


@router.get("/{code}/indicators")
async def get_stock_indicators(code: str):
    """获取个股技术指标"""
    # TODO: 实现技术指标计算
    return {
        "code": code,
        "indicators": {},
        "message": "功能开发中"
    }


@router.get("/ranking")
async def get_stock_ranking(
    order_by: str = "change_pct",
    limit: int = 100
):
    """获取个股涨跌幅排名"""
    # TODO: 实现个股排名
    return {
        "stocks": [],
        "message": "功能开发中"
    }

