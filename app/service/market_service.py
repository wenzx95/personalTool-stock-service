"""市场分析服务"""
from typing import Dict, List
from datetime import datetime
from app.crawler.ths_crawler import ThsCrawler
from app.service.sector_service import SectorService
import logging

logger = logging.getLogger(__name__)


class MarketService:
    """市场分析服务类"""
    
    def __init__(self):
        # 延迟初始化，避免启动时Chrome驱动问题
        self.crawler = ThsCrawler(init_driver=False)
        self.sector_service = SectorService()
    
    def get_market_emotion(self) -> Dict:
        """获取市场情绪分析"""
        try:
            # 获取市场统计数据
            statistics = self.crawler.get_market_statistics()
            
            # 获取板块数据
            sectors = self.sector_service.get_sector_list()
            
            # 计算情绪得分
            total_stocks = statistics.get('total_stocks', 0)
            up_count = statistics.get('up_count', 0)
            down_count = statistics.get('down_count', 0)
            limit_up_count = statistics.get('limit_up_count', 0)
            limit_down_count = statistics.get('limit_down_count', 0)
            
            # 情绪得分计算（0-100）
            emotion_score = 50  # 基准分
            
            if total_stocks > 0:
                up_ratio = up_count / total_stocks
                down_ratio = down_count / total_stocks
                
                # 上涨比例影响
                emotion_score += (up_ratio - 0.5) * 40
                
                # 涨停/跌停影响
                if total_stocks > 0:
                    limit_up_ratio = limit_up_count / total_stocks
                    limit_down_ratio = limit_down_count / total_stocks
                    emotion_score += (limit_up_ratio - limit_down_ratio) * 30
            
            # 板块表现影响
            if sectors:
                up_sectors = [s for s in sectors if s.get('change_pct', 0) > 0]
                if len(up_sectors) > len(sectors) * 0.6:
                    emotion_score += 10
                elif len(up_sectors) < len(sectors) * 0.4:
                    emotion_score -= 10
            
            emotion_score = max(0, min(100, emotion_score))
            
            # 判断情绪周期
            emotion_cycle = "震荡"
            if emotion_score >= 75:
                emotion_cycle = "上升期"
            elif emotion_score >= 60:
                emotion_cycle = "活跃"
            elif emotion_score >= 40:
                emotion_cycle = "震荡"
            elif emotion_score >= 25:
                emotion_cycle = "退潮期"
            else:
                emotion_cycle = "冰点期"
            
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total_stocks': total_stocks,
                'up_count': up_count,
                'down_count': down_count,
                'flat_count': statistics.get('flat_count', 0),
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'emotion_score': round(emotion_score, 2),
                'emotion_cycle': emotion_cycle
            }
            
        except Exception as e:
            logger.error(f"获取市场情绪失败: {e}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'emotion_score': 50,
                'emotion_cycle': '未知'
            }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()

