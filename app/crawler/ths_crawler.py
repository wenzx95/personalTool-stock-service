"""同花顺数据抓取器"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 尝试导入webdriver-manager（可选）
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    logger.warning("webdriver-manager未安装，将使用系统PATH中的ChromeDriver")


class ThsCrawler:
    """同花顺数据抓取类"""
    
    def __init__(self, init_driver: bool = True):
        self.base_url = settings.THS_BASE_URL
        self.driver = None
        if init_driver:
            self._init_driver()
    
    def ensure_driver(self):
        """确保驱动已初始化"""
        if self.driver is None:
            self._init_driver()
            if self.driver is None:
                # 如果初始化失败，记录警告但不抛出异常
                logger.warning("Chrome驱动未初始化，无法抓取数据。返回空数据。")
                return False
        return True
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        if self.driver is not None:
            # 如果已经初始化，直接返回
            return
        
        try:
            options = Options()
            options.add_argument('--headless')  # 无头模式
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 方法1: 尝试使用Selenium 4.6+的内置驱动管理（最简单）
            try:
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Chrome驱动初始化成功（使用Selenium内置驱动管理）")
                return
            except Exception as e1:
                logger.debug(f"Selenium内置驱动管理失败: {e1}")
            
            # 方法2: 尝试使用webdriver-manager
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    # 清除缓存，重新下载
                    from webdriver_manager.chrome import ChromeDriverManager
                    from webdriver_manager.core.os_manager import ChromeType
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info("✅ Chrome驱动初始化成功（使用webdriver-manager）")
                    return
                except Exception as e2:
                    logger.warning(f"webdriver-manager初始化失败: {e2}")
                    # 尝试指定Chrome类型
                    try:
                        service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
                        self.driver = webdriver.Chrome(service=service, options=options)
                        logger.info("✅ Chrome驱动初始化成功（使用webdriver-manager，指定Chrome类型）")
                        return
                    except Exception as e3:
                        logger.warning(f"webdriver-manager（指定类型）初始化失败: {e3}")
            
            # 方法3: 尝试使用系统PATH中的ChromeDriver
            try:
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Chrome驱动初始化成功（使用系统PATH）")
                return
            except Exception as e4:
                logger.warning(f"系统PATH中的ChromeDriver初始化失败: {e4}")
            
            # 所有方法都失败
            raise Exception("所有Chrome驱动初始化方法都失败")
            
        except Exception as e:
            logger.error(f"❌ Chrome驱动初始化失败: {e}")
            logger.error("=" * 60)
            logger.error("解决方案：")
            logger.error("1. 确保已安装Chrome浏览器")
            logger.error("2. 手动下载ChromeDriver并添加到PATH：")
            logger.error("   - 下载地址: https://googlechromelabs.github.io/chrome-for-testing/")
            logger.error("   - 或使用: https://chromedriver.chromium.org/downloads")
            logger.error("   - 确保ChromeDriver版本与Chrome浏览器版本匹配")
            logger.error("3. 或者安装webdriver-manager: pip install webdriver-manager")
            logger.error("4. 如果问题持续，可以暂时禁用爬虫功能，服务仍可正常启动")
            logger.error("=" * 60)
            # 不抛出异常，允许服务启动（延迟初始化）
            self.driver = None
    
    def _random_delay(self, min_delay: float = 1.0, max_delay: float = None):
        """随机延迟"""
        if max_delay is None:
            max_delay = settings.CRAWL_DELAY
        time.sleep(random.uniform(min_delay, max_delay))
    
    def _parse_number(self, text: str) -> float:
        """解析数字字符串，处理百分比、万、亿等单位"""
        if not text or text == '-':
            return 0.0
        
        text = text.strip().replace(',', '')
        
        # 处理百分比
        if '%' in text:
            text = text.replace('%', '')
            return float(text) if text else 0.0
        
        # 处理万、亿
        multiplier = 1
        if '亿' in text:
            multiplier = 100000000
            text = text.replace('亿', '')
        elif '万' in text:
            multiplier = 10000
            text = text.replace('万', '')
        
        try:
            return float(text) * multiplier if text else 0.0
        except ValueError:
            return 0.0
    
    def get_sector_list(self) -> List[Dict]:
        """获取板块列表"""
        logger.info("[ThsCrawler] ========== 开始获取板块列表 ==========")
        start_time = time.time()
        try:
            logger.info("[ThsCrawler] 步骤1: 检查并初始化Chrome驱动")
            if not self.ensure_driver():
                logger.warning("[ThsCrawler] Chrome驱动未初始化，返回空列表")
                return []
            logger.info("[ThsCrawler] 步骤1完成: Chrome驱动已就绪")
            
            url = f"{self.base_url}/thshy/"
            logger.info(f"[ThsCrawler] 步骤2: 访问URL: {url}")
            self.driver.get(url)
            logger.info("[ThsCrawler] 页面已加载，等待2-3秒...")
            self._random_delay(2, 3)
            
            logger.info("[ThsCrawler] 步骤3: 等待表格元素加载（最多15秒）")
            # 等待页面加载
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .m-table, .table"))
            )
            logger.info("[ThsCrawler] 步骤3完成: 表格元素已找到")
            
            logger.info("[ThsCrawler] 步骤4: 解析HTML页面")
            # 解析HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            sectors = []
            
            logger.info("[ThsCrawler] 步骤5: 查找表格元素")
            # 查找表格
            table = soup.find('table') or soup.find(class_=re.compile('table', re.I))
            if not table:
                logger.warning("[ThsCrawler] 未找到板块表格，返回空列表")
                return []
            logger.info("[ThsCrawler] 步骤5完成: 表格已找到")
            
            rows = table.find_all('tr')[1:]  # 跳过表头
            logger.info(f"[ThsCrawler] 步骤6: 开始解析表格，共 {len(rows)} 行数据")
            processed_count = 0
            for row_idx, row in enumerate(rows, 1):
                try:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) < 5:
                        continue
                    
                    # 解析板块数据（根据同花顺实际页面结构调整）
                    sector_code = cols[0].get_text(strip=True) if len(cols) > 0 else ''
                    sector_name = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                    change_pct = self._parse_number(cols[2].get_text(strip=True)) if len(cols) > 2 else 0.0
                    
                    # 尝试解析更多字段
                    up_count = 0
                    down_count = 0
                    limit_up_count = 0
                    limit_down_count = 0
                    
                    if len(cols) > 3:
                        up_count = int(cols[3].get_text(strip=True) or 0)
                    if len(cols) > 4:
                        down_count = int(cols[4].get_text(strip=True) or 0)
                    if len(cols) > 5:
                        limit_up_count = int(cols[5].get_text(strip=True) or 0)
                    if len(cols) > 6:
                        limit_down_count = int(cols[6].get_text(strip=True) or 0)
                    
                    # 尝试解析更多字段：换手率、成交量、成交额
                    turnover_rate = 0.0
                    volume = 0
                    amount = 0
                    
                    # 根据同花顺表格结构，这些字段可能在后面的列
                    if len(cols) > 7:
                        turnover_rate = self._parse_number(cols[7].get_text(strip=True))
                    if len(cols) > 8:
                        volume_text = cols[8].get_text(strip=True)
                        volume = int(self._parse_number(volume_text))
                    if len(cols) > 9:
                        amount_text = cols[9].get_text(strip=True)
                        amount = int(self._parse_number(amount_text))
                    
                    # 计算总股票数（如果表格中没有，则用上涨+下跌家数）
                    total_stocks = up_count + down_count
                    if len(cols) > 10:
                        total_text = cols[10].get_text(strip=True)
                        if total_text:
                            total_stocks = int(self._parse_number(total_text)) or total_stocks
                    
                    if sector_code and sector_name:
                        sectors.append({
                            'code': sector_code,
                            'name': sector_name,
                            'change_pct': change_pct,
                            'up_count': up_count,
                            'down_count': down_count,
                            'limit_up_count': limit_up_count,
                            'limit_down_count': limit_down_count,
                            'total_stocks': total_stocks,
                            'turnover_rate': turnover_rate,
                            'volume': volume,
                            'amount': amount
                        })
                        processed_count += 1
                        if processed_count % 10 == 0:
                            logger.debug(f"[ThsCrawler] 已处理 {processed_count} 个板块...")
                except Exception as e:
                    logger.warning(f"[ThsCrawler] 解析第 {row_idx} 行数据失败: {e}")
                    continue
            
            elapsed = time.time() - start_time
            logger.info(f"[ThsCrawler] ========== 板块列表获取完成 ==========")
            logger.info(f"[ThsCrawler] 成功抓取 {len(sectors)} 个板块，总耗时 {elapsed:.3f}秒")
            return sectors
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[ThsCrawler] ========== 板块列表获取失败 ==========")
            logger.error(f"[ThsCrawler] 错误信息: {e}，耗时 {elapsed:.3f}秒", exc_info=True)
            return []
    
    def get_sector_detail(self, sector_code: str) -> Optional[Dict]:
        """获取板块详情"""
        try:
            if not self.ensure_driver():
                return None
            
            url = f"{self.base_url}/thshy/detail/code/{sector_code}/"
            logger.info(f"开始抓取板块详情: {url}")
            self.driver.get(url)
            self._random_delay(2, 3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 解析板块详情数据
            detail = {
                'code': sector_code,
                'name': '',
                'change_pct': 0.0,
                'volume': 0,
                'amount': 0,
                'turnover_rate': 0.0,
                'stocks': []
            }
            
            # 这里需要根据实际页面结构解析
            # TODO: 完善详情页解析逻辑
            
            return detail
            
        except Exception as e:
            logger.error(f"抓取板块详情失败: {e}")
            return None
    
    def get_sector_fund_flow(self, sector_code: str) -> Dict:
        """获取板块资金流向"""
        try:
            if not self.ensure_driver():
                return {'code': sector_code, 'net_inflow': 0.0}
            
            url = f"{self.base_url}/thshy/detail/field/265649/order/desc/page/1/ajax/1/code/{sector_code}/"
            logger.info(f"开始抓取板块资金流向: {url}")
            self.driver.get(url)
            self._random_delay(2, 3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            fund_flow = {
                'code': sector_code,
                'net_inflow': 0.0,
                'main_force_inflow': 0.0,
                'main_force_outflow': 0.0,
                'net_main_force': 0.0
            }
            
            # 解析资金流向数据
            # TODO: 根据实际页面结构完善解析逻辑
            
            return fund_flow
            
        except Exception as e:
            logger.error(f"抓取板块资金流向失败: {e}")
            return {'code': sector_code, 'net_inflow': 0.0}
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict]:
        """获取个股数据"""
        try:
            if not self.ensure_driver():
                return None
            
            url = f"{self.base_url}/stock/detail/stockcode/{stock_code}/"
            logger.info(f"开始抓取个股数据: {url}")
            self.driver.get(url)
            self._random_delay(2, 3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            stock_data = {
                'code': stock_code,
                'name': '',
                'price': 0.0,
                'change_pct': 0.0,
                'volume': 0,
                'amount': 0,
                'turnover_rate': 0.0,
                'high': 0.0,
                'low': 0.0,
                'open': 0.0,
                'close': 0.0
            }
            
            # 解析个股数据
            # TODO: 根据实际页面结构完善解析逻辑
            
            return stock_data
            
        except Exception as e:
            logger.error(f"抓取个股数据失败: {e}")
            return None
    
    def get_market_statistics(self) -> Dict:
        """获取市场统计数据（涨跌家数等）"""
        try:
            if not self.ensure_driver():
                return {
                    'total_stocks': 0,
                    'up_count': 0,
                    'down_count': 0,
                    'flat_count': 0,
                    'limit_up_count': 0,
                    'limit_down_count': 0
                }
            
            url = f"{self.base_url}/market/"
            logger.info(f"开始抓取市场统计: {url}")
            self.driver.get(url)
            self._random_delay(2, 3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            statistics = {
                'total_stocks': 0,
                'up_count': 0,
                'down_count': 0,
                'flat_count': 0,
                'limit_up_count': 0,
                'limit_down_count': 0
            }
            
            # 解析市场统计数据
            # TODO: 根据实际页面结构完善解析逻辑
            
            return statistics
            
        except Exception as e:
            logger.error(f"抓取市场统计失败: {e}")
            return statistics
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")

