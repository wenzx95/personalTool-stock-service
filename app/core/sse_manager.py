"""SSE (Server-Sent Events) 管理模块
用于实时推送日志消息给前端
"""
import asyncio
import logging
from typing import AsyncGenerator, Dict, Set
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

# 存储 SSE 连接的会话信息
class SSEManager:
    _instance = None
    _sessions: Dict[str, Set[asyncio.Queue]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
        return cls._instance

    @classmethod
    async def connect(cls, session_id: str) -> AsyncGenerator[str, None]:
        """
        建立 SSE 连接

        参数:
            session_id: 会话 ID
        """
        manager = cls()
        queue = asyncio.Queue()

        # 加入会话
        if session_id not in manager._sessions:
            manager._sessions[session_id] = set()
        manager._sessions[session_id].add(queue)

        logger.info(f"[SSE] 新连接，会话 {session_id}，当前连接数: {len(manager._sessions[session_id])}")

        try:
            while True:
                # 等待消息
                message = await queue.get()
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            logger.info(f"[SSE] 连接被取消，会话 {session_id}")
        except Exception as e:
            logger.error(f"[SSE] 连接异常，会话 {session_id}: {e}")
        finally:
            # 离开会话
            if session_id in manager._sessions:
                manager._sessions[session_id].remove(queue)
                logger.info(f"[SSE] 连接断开，会话 {session_id}，当前连接数: {len(manager._sessions[session_id])}")
                if len(manager._sessions[session_id]) == 0:
                    del manager._sessions[session_id]
                    logger.info(f"[SSE] 会话 {session_id} 已无连接，删除会话")

    @classmethod
    async def send(cls, session_id: str, message: str):
        """
        发送消息到指定会话的所有连接

        参数:
            session_id: 会话 ID
            message: 要发送的消息
        """
        manager = cls()

        if session_id in manager._sessions:
            queues = manager._sessions[session_id].copy()
            for queue in queues:
                try:
                    await queue.put(message)
                except Exception as e:
                    logger.error(f"[SSE] 发送消息失败: {e}")

    @classmethod
    async def broadcast(cls, message: str):
        """
        广播消息到所有会话

        参数:
            message: 要发送的消息
        """
        manager = cls()

        for session_id, queues in list(manager._sessions.items()):
            for queue in queues.copy():
                try:
                    await queue.put(message)
                except Exception as e:
                    logger.error(f"[SSE] 广播消息失败，会话 {session_id}: {e}")

    @classmethod
    def get_session_count(cls) -> int:
        """获取当前会话数"""
        manager = cls()
        return len(manager._sessions)

    @classmethod
    def get_total_connection_count(cls) -> int:
        """获取总连接数"""
        manager = cls()
        return sum(len(queues) for queues in manager._sessions.values())


# 装饰器用于发送日志到 SSE
def log_to_sse(session_id: str = None):
    """
    装饰器，自动将函数的 logger 输出发送到 SSE

    参数:
        session_id: 会话 ID，如果为 None 则广播到所有会话
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 创建临时 logger
            old_logger = logging.getLogger(__name__)

            # 保存原始日志处理器
            original_handlers = old_logger.handlers.copy()

            # 创建 SSE 日志处理器
            class SSEHandler(logging.Handler):
                def emit(self, record):
                    msg = self.format(record)
                    if session_id:
                        asyncio.create_task(SSEManager.send(session_id, msg))
                    else:
                        asyncio.create_task(SSEManager.broadcast(msg))

            sse_handler = SSEHandler()
            sse_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

            old_logger.addHandler(sse_handler)

            try:
                return await func(*args, **kwargs)
            finally:
                old_logger.removeHandler(sse_handler)

        return wrapper
    return decorator


# 使用示例（同步版本）
def send_sync(session_id: str, message: str):
    """
    同步发送消息的封装，在同步函数中使用

    参数:
        session_id: 会话 ID
        message: 要发送的消息
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(SSEManager.send(session_id, message))
    else:
        loop.run_until_complete(SSEManager.send(session_id, message))


def broadcast_sync(message: str):
    """
    同步广播消息的封装，在同步函数中使用

    参数:
        message: 要发送的消息
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(SSEManager.broadcast(message))
    else:
        loop.run_until_complete(SSEManager.broadcast(message))
