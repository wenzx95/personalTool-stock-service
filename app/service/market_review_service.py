"""市场复盘数据服务"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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
            
            # 1. 获取涨停板数据（用于判断日期是否有效）
            is_valid_date = False
            try:
                limit_up_df = ak.stock_zt_pool_em(date=trade_date)
                limit_up_count = len(limit_up_df) if limit_up_df is not None and not limit_up_df.empty else 0
                if limit_up_count == 0:
                    logger.warning(f"[MarketReviewService] 涨停数量为0，可能是非交易日或日期超出范围（只能查询最近30个交易日）")
                    is_valid_date = False
                else:
                    logger.info(f"[MarketReviewService] 涨停数量: {limit_up_count}")
                    is_valid_date = True
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取涨停数据失败: {e}")
                limit_up_count = 0
                is_valid_date = False
            
            # 2. 获取跌停板数据
            try:
                # 使用跌停股池函数
                limit_down_df = ak.stock_zt_pool_dtgc_em(date=trade_date)
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
            # 如果日期无效（涨停数量为0），市场统计数据也返回0
            if not is_valid_date:
                logger.warning(f"[MarketReviewService] 日期无效，市场统计数据返回0")
                total_stocks = 0
                red_count = 0
                green_count = 0
                volume = 0
            else:
                try:
                    # 优先使用A股实时行情接口（更准确）
                    try:
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

                            # 成交额
                            if '成交额' in stock_info_df.columns:
                                volume = int(stock_info_df['成交额'].sum())
                            elif '成交量' in stock_info_df.columns:
                                volume = int(stock_info_df['成交量'].sum())
                            else:
                                volume = 0

                            logger.info(f"[MarketReviewService] 市场统计(实时行情): 总家数={total_stocks}, 红盘={red_count}, 绿盘={green_count}, 成交额={volume}")
                        else:
                            raise ValueError("实时行情数据为空")
                    except Exception as e1:
                        logger.warning(f"[MarketReviewService] 实时行情接口失败: {e1}")
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
                # 使用炸板股池函数获取炸板数据
                zt_broken_df = ak.stock_zt_pool_zbgc_em(date=trade_date)
                if zt_broken_df is not None and not zt_broken_df.empty:
                    zt_count = len(zt_broken_df)
                else:
                    # 如果炸板股池没有数据，尝试从涨停板数据中统计炸板次数>0的股票
                    zt_analyze_df = ak.stock_zt_pool_em(date=trade_date)
                    if zt_analyze_df is not None and not zt_analyze_df.empty:
                        if '炸板次数' in zt_analyze_df.columns:
                            # 统计炸板次数 > 0 的股票数量（不是求和）
                            zt_count = len(zt_analyze_df[zt_analyze_df['炸板次数'] > 0])
                        else:
                            zt_count = 0
                    else:
                        zt_count = 0
                
                # 炸板率 = 炸板数 / (炸板数 + 涨停数) × 100%
                total_zt = zt_count + limit_up_count
                if total_zt > 0:
                    zt_rate = round((zt_count / total_zt) * 100)
                else:
                    zt_rate = 0
                logger.info(f"[MarketReviewService] 炸板数据: 炸板={zt_count}, 涨停={limit_up_count}, 炸板率={zt_rate}%")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取炸板数据失败: {e}")
                zt_count = 0
                zt_rate = 0
            
            # 6. 计算连板率 = 总连板数 / 上一日涨停数 × 100%
            # 先查询上一日的涨停数
            try:
                from app.models.database import MarketReviewModel

                # 计算上一日日期
                if trade_date:
                    current_date = datetime.strptime(trade_date, '%Y%m%d')
                    prev_date = current_date - timedelta(days=1)
                    prev_date_str = prev_date.strftime('%Y-%m-%d')

                    # 查询上一日的涨停数
                    prev_review = MarketReviewModel.get_by_date(prev_date_str)
                    prev_limit_up_count = prev_review['limit_up_count'] if prev_review else 0

                    logger.info(f"[MarketReviewService] 上一日({prev_date_str})涨停数: {prev_limit_up_count}")
                else:
                    prev_limit_up_count = 0

                # 计算连板率
                if prev_limit_up_count > 0:
                    continuous_limit_rate = round((total_continuous_limit / prev_limit_up_count) * 100)
                else:
                    continuous_limit_rate = 0

                logger.info(f"[MarketReviewService] 连板率: {total_continuous_limit}/{prev_limit_up_count} = {continuous_limit_rate}%")
            except Exception as e:
                logger.warning(f"[MarketReviewService] 获取上一日涨停数失败: {e}")
                # 如果无法获取上一日涨停数，使用总股票数作为分母（兼容旧逻辑）
                if total_stocks > 0:
                    continuous_limit_rate = round((total_continuous_limit / total_stocks) * 100)
                else:
                    continuous_limit_rate = 0
            
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
                'total_stocks': total_stocks,
                # 新增情绪监控字段
                'red_rate': round(red_count / total_stocks * 100) if total_stocks > 0 else 0,
                'market_strength': self._calculate_market_strength(red_count, green_count, total_stocks),
                'max_continuous_days': self._get_max_continuous_days(four_plus_df) if four_plus_df is not None else 0,
                'first_board_count': max(0, limit_up_count - total_continuous_limit) if limit_up_count and total_continuous_limit else 0,
                'three_board_stocks_with_sector': self._extract_stocks_with_sector(three_board_stocks),
                'four_plus_stocks_with_sector': self._extract_stocks_with_sector(four_plus_stocks)
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
            'zt_rate': 0,
            'total_continuous_limit': 0,
            'continuous_limit_rate': 0,
            'four_plus_count': 0,
            'four_plus_stocks': [],
            'two_board_count': 0,
            'three_board_count': 0,
            'three_board_stocks': [],
            'total_stocks': 0,
            # 新增字段
            'red_rate': 0,
            'market_strength': '',
            'max_continuous_days': 0,
            'first_board_count': 0,
            'three_board_stocks_with_sector': [],
            'four_plus_stocks_with_sector': []
        }

    def _calculate_market_strength(self, red_count: int, green_count: int, total_stocks: int) -> str:
        """计算市场强弱"""
        if total_stocks == 0:
            return ''

        red_rate = red_count / total_stocks

        if red_rate >= 0.8:
            return '极强'
        elif red_rate >= 0.6:
            return '强'
        elif red_rate >= 0.5:
            return '偏强'
        elif red_rate >= 0.4:
            return '中性'
        elif red_rate >= 0.2:
            return '偏弱'
        else:
            return '弱'

    def _get_max_continuous_days(self, four_plus_df) -> int:
        """获取最高连板天数"""
        try:
            if four_plus_df is not None and not four_plus_df.empty and '连板数' in four_plus_df.columns:
                return int(four_plus_df['连板数'].max())
        except:
            pass
        return 0

    def _extract_stocks_with_sector(self, stocks_list: list) -> list:
        """从股票列表中提取名称（暂时没有板块信息，使用空字符串）"""
        if not stocks_list:
            return []

        result = []
        for stock in stocks_list:
            if isinstance(stock, dict):
                result.append({
                    'name': stock.get('name', ''),
                    'code': stock.get('code', ''),
                    'sector': ''  # 暂时没有板块信息
                })
        return result

