"""SSE (Server-Sent Events) 相关API"""
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from app.core.sse_manager import SSEManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/events/{session_id}")
async def sse_events(session_id: str):
    """
    建立 SSE 连接，用于实时接收日志消息

    参数:
        session_id: 会话 ID，用于区分不同的客户端连接
    """
    logger.info(f"[SSE API] 客户端连接，会话 ID: {session_id}")
    try:
        return EventSourceResponse(SSEManager.connect(session_id))
    except Exception as e:
        logger.error(f"[SSE API] 连接建立失败: {e}")
        raise
