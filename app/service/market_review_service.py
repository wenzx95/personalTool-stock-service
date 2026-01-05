"""市场复盘数据服务"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# 尝试导入akshare
AKSHARE_AVAILABLE = False
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    logger.info("akshare导入成功")
except ImportError as e:
    logger.warning(f"akshare未安装: {e}")
except Exception as e:
    logger.warning(f"akshare导入失败: {e}")


class MarketReviewService:
    """市场复盘数据服务类"""
    
    def __init__(self):
        if not AKSHARE_AVAILABLE:
            logger.warning("akshare不可用，市场复盘功能将受限")
    
    def get_market_review_data(self, trade_date: Optional[str] = None) -> Dict:
        """
        获取市场复盘数据
        
        参数:
            trade_date: 交易日期，格式：YYYYMMDD，默认为今天
        
        返回:
            包含以下字段的字典:
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
        if not AKSHARE_AVAILABLE:
            return self._get_empty_data()
        
        try:
            # 如果没有指定日期，使用今天
            if not trade_date:
                trade_date = datetime.now().strftime('%Y%m%d')
            
            logger.info(f"[MarketReviewService] 开始获取市场复盘数据，日期: {trade_date}")
            
            # 获取市场整体数据
            result = {}
            
            # 1. 获取涨停板数据
            try:
                limit_up_df = ak.stock_zt_pool_em(date=trade_date)
                limit_up_count = len(limit_up_df) if limit_up_df is not None and not limit_up_df.empty else 0
                logger.info(f"[MarketReviewService] 涨停数量: {limit_up_count}")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取涨停数据失败: {e}")
                limit_up_count = 0
            
            # 2. 获取跌停板数据
            try:
                limit_down_df = ak.stock_dt_pool_em(date=trade_date)
                limit_down_count = len(limit_down_df) if limit_down_df is not None and not limit_down_df.empty else 0
                logger.info(f"[MarketReviewService] 跌停数量: {limit_down_count}")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取跌停数据失败: {e}")
                limit_down_count = 0
            
            # 3. 获取连板数据
            try:
                continuous_limit_df = ak.stock_zt_pool_em(date=trade_date)
                if continuous_limit_df is not None and not continuous_limit_df.empty:
                    # 计算连板数据
                    total_continuous_limit = len(continuous_limit_df)
                    # 筛选2板、3板、4板及以上
                    if '连板数' in continuous_limit_df.columns:
                        two_board_count = len(continuous_limit_df[continuous_limit_df['连板数'] == 2])
                        three_board_count = len(continuous_limit_df[continuous_limit_df['连板数'] == 3])
                        four_plus_df = continuous_limit_df[continuous_limit_df['连板数'] >= 4]
                        four_plus_count = len(four_plus_df)
                        four_plus_stocks = four_plus_df[['代码', '名称']].to_dict('records') if not four_plus_df.empty else []
                        three_board_stocks = continuous_limit_df[continuous_limit_df['连板数'] == 3][['代码', '名称']].to_dict('records') if three_board_count > 0 else []
                    else:
                        two_board_count = 0
                        three_board_count = 0
                        four_plus_count = 0
                        four_plus_stocks = []
                        three_board_stocks = []
                else:
                    total_continuous_limit = 0
                    two_board_count = 0
                    three_board_count = 0
                    four_plus_count = 0
                    four_plus_stocks = []
                    three_board_stocks = []
                logger.info(f"[MarketReviewService] 连板数据: 总连板={total_continuous_limit}, 2板={two_board_count}, 3板={three_board_count}, 4板+={four_plus_count}")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取连板数据失败: {e}")
                total_continuous_limit = 0
                two_board_count = 0
                three_board_count = 0
                four_plus_count = 0
                four_plus_stocks = []
                three_board_stocks = []
            
            # 4. 获取市场统计（涨跌家数、成交量等）
            try:
                # 获取A股实时行情
                stock_info_df = ak.stock_zh_a_spot_em()
                if stock_info_df is not None and not stock_info_df.empty:
                    total_stocks = len(stock_info_df)
                    # 红盘（上涨）
                    if '涨跌幅' in stock_info_df.columns:
                        red_count = len(stock_info_df[stock_info_df['涨跌幅'] > 0])
                        green_count = len(stock_info_df[stock_info_df['涨跌幅'] < 0])
                    else:
                        red_count = 0
                        green_count = 0
                    
                    # 成交量
                    if '成交量' in stock_info_df.columns:
                        volume = stock_info_df['成交量'].sum()
                    elif '成交额' in stock_info_df.columns:
                        volume = stock_info_df['成交额'].sum()
                    else:
                        volume = 0
                    
                    logger.info(f"[MarketReviewService] 市场统计: 总家数={total_stocks}, 红盘={red_count}, 绿盘={green_count}, 成交量={volume}")
                else:
                    total_stocks = 0
                    red_count = 0
                    green_count = 0
                    volume = 0
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取市场统计失败: {e}")
                total_stocks = 0
                red_count = 0
                green_count = 0
                volume = 0
            
            # 5. 获取炸板数据（涨停后开板）
            try:
                # 尝试获取炸板数据
                zt_analyze_df = ak.stock_zt_pool_em(date=trade_date)
                if zt_analyze_df is not None and not zt_analyze_df.empty:
                    # 如果有"炸板次数"或类似字段
                    if '炸板次数' in zt_analyze_df.columns:
                        zt_count = zt_analyze_df['炸板次数'].sum()
                    else:
                        # 尝试其他方式计算炸板
                        zt_count = 0
                    
                    # 炸板率 = 炸板数 / 涨停数
                    if limit_up_count > 0:
                        zt_rate = round((zt_count / limit_up_count) * 100, 2)
                    else:
                        zt_rate = 0.0
                else:
                    zt_count = 0
                    zt_rate = 0.0
                logger.info(f"[MarketReviewService] 炸板数据: 炸板={zt_count}, 炸板率={zt_rate}%")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取炸板数据失败: {e}")
                zt_count = 0
                zt_rate = 0.0
            
            # 6. 计算连板率
            if total_stocks > 0:
                continuous_limit_rate = round((total_continuous_limit / total_stocks) * 100, 2)
            else:
                continuous_limit_rate = 0.0
            
            # 格式化日期
            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            
            result = {
                'date': formatted_date,
                'volume': int(volume) if volume else 0,
                'red_count': red_count,
                'green_count': green_count,
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'zt_count': int(zt_count),
                'zt_rate': zt_rate,
                'total_continuous_limit': total_continuous_limit,
                'continuous_limit_rate': continuous_limit_rate,
                'four_plus_count': four_plus_count,
                'four_plus_stocks': four_plus_stocks,
                'two_board_count': two_board_count,
                'three_board_count': three_board_count,
                'three_board_stocks': three_board_stocks,
                'total_stocks': total_stocks
            }
            
            logger.info(f"[MarketReviewService] 市场复盘数据获取成功")
            return result
            
        except Exception as e:
            logger.error(f"[MarketReviewService] 获取市场复盘数据失败: {e}", exc_info=True)
            return self._get_empty_data()
    
    def _get_empty_data(self) -> Dict:
        """返回空数据"""
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'volume': 0,
            'red_count': 0,
            'green_count': 0,
            'limit_up_count': 0,
            'limit_down_count': 0,
            'zt_count': 0,
            'zt_rate': 0.0,
            'total_continuous_limit': 0,
            'continuous_limit_rate': 0.0,
            'four_plus_count': 0,
            'four_plus_stocks': [],
            'two_board_count': 0,
            'three_board_count': 0,
            'three_board_stocks': [],
            'total_stocks': 0
        }

