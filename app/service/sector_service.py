"""板块业务逻辑服务"""
from typing import List, Dict, Optional
from app.crawler.ths_crawler import ThsCrawler
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class SectorService:
    """板块服务类"""
    
    def __init__(self):
        # 延迟初始化，避免启动时Chrome驱动问题
        self.crawler = ThsCrawler(init_driver=False)
    
    def get_sector_list(self) -> List[Dict]:
        """获取板块列表"""
        logger.info("[SectorService] 开始获取板块列表")
        start_time = time.time()
        try:
            logger.info("[SectorService] 调用crawler.get_sector_list()")
            sectors = self.crawler.get_sector_list()
            elapsed = time.time() - start_time
            logger.info(f"[SectorService] 成功获取 {len(sectors)} 个板块，耗时 {elapsed:.3f}秒")
            return sectors
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[SectorService] 获取板块列表失败: {e}，耗时 {elapsed:.3f}秒", exc_info=True)
            return []
    
    def get_sector_ranking(self, order_by: str = "change_pct", limit: int = 100) -> List[Dict]:
        """获取板块排名"""
        try:
            sectors = self.get_sector_list()
            
            # 排序
            reverse = True if order_by == "change_pct" else False
            if order_by == "change_pct":
                sectors.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
            elif order_by == "limit_up_count":
                sectors.sort(key=lambda x: x.get('limit_up_count', 0), reverse=True)
            elif order_by == "volume":
                sectors.sort(key=lambda x: x.get('volume', 0), reverse=True)
            
            return sectors[:limit]
        except Exception as e:
            logger.error(f"获取板块排名失败: {e}")
            return []
    
    def get_sector_detail(self, sector_code: str) -> Optional[Dict]:
        """获取板块详情"""
        try:
            return self.crawler.get_sector_detail(sector_code)
        except Exception as e:
            logger.error(f"获取板块详情失败: {e}")
            return None
    
    def get_sector_fund_flow(self, sector_code: str) -> Dict:
        """获取板块资金流向"""
        try:
            return self.crawler.get_sector_fund_flow(sector_code)
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            return {'code': sector_code, 'net_inflow': 0.0}
    
    def analyze_sector_rotation(self, sectors: List[Dict]) -> List[Dict]:
        """分析板块轮动"""
        try:
            rotation_data = []
            
            for sector in sectors:
                change_pct = sector.get('change_pct', 0)
                limit_up_count = sector.get('limit_up_count', 0)
                up_count = sector.get('up_count', 0)
                total_stocks = sector.get('total_stocks', 1)
                
                # 计算热度评分
                hot_score = 0
                if change_pct > 0:
                    hot_score += min(change_pct * 10, 50)  # 涨幅贡献最多50分
                if limit_up_count > 0:
                    hot_score += min(limit_up_count * 5, 30)  # 涨停数贡献最多30分
                if up_count > 0:
                    up_ratio = up_count / total_stocks if total_stocks > 0 else 0
                    hot_score += up_ratio * 20  # 上涨比例贡献最多20分
                
                # 判断动量
                momentum = "weak"
                if hot_score >= 70:
                    momentum = "strong"
                elif hot_score >= 40:
                    momentum = "medium"
                
                # 判断轮动趋势
                rotation_trend = "stable"
                if change_pct > 3 and limit_up_count > 5:
                    rotation_trend = "in"
                elif change_pct < -3:
                    rotation_trend = "out"
                
                rotation_data.append({
                    'code': sector.get('code'),
                    'name': sector.get('name'),
                    'hot_score': round(hot_score, 2),
                    'momentum': momentum,
                    'rotation_trend': rotation_trend,
                    'change_pct': change_pct,
                    'limit_up_count': limit_up_count
                })
            
            # 按热度排序
            rotation_data.sort(key=lambda x: x.get('hot_score', 0), reverse=True)
            
            return rotation_data
        except Exception as e:
            logger.error(f"分析板块轮动失败: {e}")
            return []
    
    def get_sector_review_table(self) -> List[Dict]:
        """获取板块复盘表格数据（用于表格展示）"""
        logger.info("[SectorService] 开始获取板块复盘表格数据")
        start_time = time.time()
        try:
            logger.info("[SectorService] 步骤1: 获取板块列表")
            sectors = self.get_sector_list()
            logger.info(f"[SectorService] 步骤1完成: 获取到 {len(sectors)} 个板块")
            
            logger.info("[SectorService] 步骤2: 格式化表格数据")
            # 格式化表格数据
            table_data = []
            for i, sector in enumerate(sectors, 1):
                if i % 10 == 0:
                    logger.debug(f"[SectorService] 正在处理第 {i}/{len(sectors)} 个板块")
                table_data.append({
                    'sector_name': sector.get('name', ''),
                    'sector_code': sector.get('code', ''),
                    'change_pct': round(sector.get('change_pct', 0), 2),
                    'total_stocks': sector.get('total_stocks', 0),
                    'up_count': sector.get('up_count', 0),
                    'down_count': sector.get('down_count', 0),
                    'limit_up_count': sector.get('limit_up_count', 0),
                    'limit_down_count': sector.get('limit_down_count', 0),
                    'turnover_rate': round(sector.get('turnover_rate', 0), 2),
                    'volume': sector.get('volume', 0),
                    'amount': sector.get('amount', 0),
                    # 计算涨跌比
                    'up_ratio': round(
                        (sector.get('up_count', 0) / sector.get('total_stocks', 1)) * 100, 2
                    ) if sector.get('total_stocks', 0) > 0 else 0.0,
                    # 计算涨停占比
                    'limit_up_ratio': round(
                        (sector.get('limit_up_count', 0) / sector.get('total_stocks', 1)) * 100, 2
                    ) if sector.get('total_stocks', 0) > 0 else 0.0,
                })
            
            logger.info("[SectorService] 步骤3: 按涨跌幅排序")
            # 按涨跌幅排序（降序）
            table_data.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
            
            elapsed = time.time() - start_time
            logger.info(f"[SectorService] 板块复盘表格数据获取成功，共 {len(table_data)} 条，耗时 {elapsed:.3f}秒")
            return table_data
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[SectorService] 获取板块复盘表格数据失败: {e}，耗时 {elapsed:.3f}秒", exc_info=True)
            return []
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()

