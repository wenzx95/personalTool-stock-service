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
        logger.info("[ThsCrawler] ensure_driver: 检查驱动状态")
        if self.driver is None:
            logger.info("[ThsCrawler] ensure_driver: 驱动未初始化，开始初始化...")
            try:
                self._init_driver()
                if self.driver is None:
                    logger.warning("[ThsCrawler] ensure_driver: Chrome驱动初始化失败，返回False")
                    return False
                else:
                    logger.info("[ThsCrawler] ensure_driver: Chrome驱动初始化成功")
                    return True
            except Exception as e:
                logger.error(f"[ThsCrawler] ensure_driver: 初始化过程出现异常: {e}", exc_info=True)
                return False
        else:
            logger.info("[ThsCrawler] ensure_driver: 驱动已存在，直接返回True")
            return True
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        logger.info("[ThsCrawler] _init_driver: 开始初始化Chrome驱动")
        if self.driver is not None:
            logger.info("[ThsCrawler] _init_driver: 驱动已存在，跳过初始化")
            return
        
        init_start_time = time.time()
        try:
            logger.info("[ThsCrawler] _init_driver: 步骤1 - 配置Chrome选项")
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
            logger.info("[ThsCrawler] _init_driver: Chrome选项配置完成")
            
            # 方法0: 尝试使用本地ChromeDriver文件（最快，如果已下载）
            import os
            import platform
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # 根据操作系统选择驱动文件名
            if platform.system() == 'Windows':
                driver_filename = 'chromedriver.exe'
            else:
                driver_filename = 'chromedriver'
            
            local_driver_path = os.path.join(project_root, driver_filename)
            if os.path.exists(local_driver_path):
                logger.info(f"[ThsCrawler] _init_driver: 方法0 - 尝试使用本地ChromeDriver: {local_driver_path}")
                try:
                    # 确保文件有执行权限（macOS/Linux）
                    if platform.system() != 'Windows':
                        os.chmod(local_driver_path, 0o755)
                    service = Service(local_driver_path)
                    logger.info("[ThsCrawler] _init_driver: 正在使用本地ChromeDriver创建WebDriver实例...")
                    self.driver = webdriver.Chrome(service=service, options=options)
                    elapsed = time.time() - init_start_time
                    logger.info(f"✅ [ThsCrawler] _init_driver: Chrome驱动初始化成功（使用本地文件），耗时 {elapsed:.3f}秒")
                    return
                except Exception as e0:
                    elapsed = time.time() - init_start_time
                    logger.warning(f"[ThsCrawler] _init_driver: 本地ChromeDriver失败（耗时 {elapsed:.3f}秒）: {e0}")
                    logger.warning(f"[ThsCrawler] _init_driver: 错误详情: {type(e0).__name__}: {str(e0)}")
            else:
                logger.info(f"[ThsCrawler] _init_driver: 本地ChromeDriver文件不存在 ({local_driver_path})，跳过方法0")
            
            # 方法1: 尝试使用Selenium 4.6+的内置驱动管理（最简单）
            logger.info("[ThsCrawler] _init_driver: 方法1 - 尝试使用Selenium内置驱动管理")
            try:
                logger.info("[ThsCrawler] _init_driver: 正在创建Chrome WebDriver实例...")
                self.driver = webdriver.Chrome(options=options)
                elapsed = time.time() - init_start_time
                logger.info(f"✅ [ThsCrawler] _init_driver: Chrome驱动初始化成功（使用Selenium内置驱动管理），耗时 {elapsed:.3f}秒")
                return
            except Exception as e1:
                elapsed = time.time() - init_start_time
                logger.warning(f"[ThsCrawler] _init_driver: Selenium内置驱动管理失败（耗时 {elapsed:.3f}秒）: {e1}")
            
            # 方法2: 尝试使用webdriver-manager
            if WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("[ThsCrawler] _init_driver: 方法2 - 尝试使用webdriver-manager")
                try:
                    logger.info("[ThsCrawler] _init_driver: 正在下载/安装ChromeDriver...")
                    from webdriver_manager.chrome import ChromeDriverManager
                    from webdriver_manager.core.os_manager import ChromeType
                    import os
                    
                    # 配置代理（如果设置了）
                    proxy_url = getattr(settings, 'PROXY_URL', None)
                    if proxy_url:
                        logger.info(f"[ThsCrawler] _init_driver: 使用代理服务器: {proxy_url}")
                        os.environ['HTTP_PROXY'] = proxy_url
                        os.environ['HTTPS_PROXY'] = proxy_url
                        os.environ['http_proxy'] = proxy_url
                        os.environ['https_proxy'] = proxy_url
                    
                    # 创建ChromeDriverManager实例并安装
                    driver_manager = ChromeDriverManager()
                    driver_path = driver_manager.install()
                    logger.info(f"[ThsCrawler] _init_driver: ChromeDriver已安装，路径: {driver_path}")
                    
                    service = Service(driver_path)
                    logger.info("[ThsCrawler] _init_driver: 正在创建WebDriver实例...")
                    self.driver = webdriver.Chrome(service=service, options=options)
                    elapsed = time.time() - init_start_time
                    logger.info(f"✅ [ThsCrawler] _init_driver: Chrome驱动初始化成功（使用webdriver-manager），耗时 {elapsed:.3f}秒")
                    return
                except Exception as e2:
                    elapsed = time.time() - init_start_time
                    logger.warning(f"[ThsCrawler] _init_driver: webdriver-manager初始化失败（耗时 {elapsed:.3f}秒）: {e2}")
                    logger.warning(f"[ThsCrawler] _init_driver: 错误详情: {type(e2).__name__}: {str(e2)}")
                    # 尝试指定Chrome类型
                    try:
                        logger.info("[ThsCrawler] _init_driver: 尝试指定Chrome类型...")
                        driver_manager = ChromeDriverManager(chrome_type=ChromeType.GOOGLE)
                        driver_path = driver_manager.install()
                        logger.info(f"[ThsCrawler] _init_driver: ChromeDriver已安装（指定类型），路径: {driver_path}")
                        service = Service(driver_path)
                        self.driver = webdriver.Chrome(service=service, options=options)
                        elapsed = time.time() - init_start_time
                        logger.info(f"✅ [ThsCrawler] _init_driver: Chrome驱动初始化成功（使用webdriver-manager，指定Chrome类型），耗时 {elapsed:.3f}秒")
                        return
                    except Exception as e3:
                        elapsed = time.time() - init_start_time
                        logger.warning(f"[ThsCrawler] _init_driver: webdriver-manager（指定类型）初始化失败（耗时 {elapsed:.3f}秒）: {e3}")
                        logger.warning(f"[ThsCrawler] _init_driver: 错误详情: {type(e3).__name__}: {str(e3)}")
            else:
                logger.info("[ThsCrawler] _init_driver: webdriver-manager不可用，跳过方法2")
            
            # 方法3: 尝试使用系统PATH中的ChromeDriver
            logger.info("[ThsCrawler] _init_driver: 方法3 - 尝试使用系统PATH中的ChromeDriver")
            try:
                logger.info("[ThsCrawler] _init_driver: 正在从系统PATH创建Chrome WebDriver实例...")
                self.driver = webdriver.Chrome(options=options)
                elapsed = time.time() - init_start_time
                logger.info(f"✅ [ThsCrawler] _init_driver: Chrome驱动初始化成功（使用系统PATH），耗时 {elapsed:.3f}秒")
                return
            except Exception as e4:
                elapsed = time.time() - init_start_time
                logger.warning(f"[ThsCrawler] _init_driver: 系统PATH中的ChromeDriver初始化失败（耗时 {elapsed:.3f}秒）: {e4}")
            
            # 所有方法都失败
            elapsed = time.time() - init_start_time
            logger.error(f"[ThsCrawler] _init_driver: 所有初始化方法都失败，总耗时 {elapsed:.3f}秒")
            raise Exception("所有Chrome驱动初始化方法都失败")
            
        except Exception as e:
            elapsed = time.time() - init_start_time
            logger.error(f"❌ [ThsCrawler] _init_driver: Chrome驱动初始化失败（总耗时 {elapsed:.3f}秒）: {e}")
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
            # 等待更长时间，确保数据加载完成
            logger.info("[ThsCrawler] 额外等待3秒，确保表格数据完全加载...")
            self._random_delay(3, 4)
            
            # 解析HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            sectors = []
            
            # 调试：保存页面HTML到文件（仅用于调试）
            import os
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, 'page_source.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"[ThsCrawler] 调试: 页面HTML已保存到 {debug_file}")
            
            logger.info("[ThsCrawler] 步骤5: 查找表格元素")
            # 尝试多种方式查找表格
            table = None
            # 方法1: 查找标准table标签
            tables = soup.find_all('table')
            logger.info(f"[ThsCrawler] 调试: 找到 {len(tables)} 个table标签")
            if tables:
                # 选择最大的table（通常是数据表格）
                table = max(tables, key=lambda t: len(t.find_all('tr')))
                logger.info(f"[ThsCrawler] 调试: 选择最大的table，包含 {len(table.find_all('tr'))} 行")
            
            # 方法2: 如果没找到，尝试通过class查找
            if not table:
                table = soup.find(class_=re.compile('table|m-table|data-table', re.I))
                if table:
                    logger.info("[ThsCrawler] 调试: 通过class找到表格")
            
            # 方法3: 尝试查找tbody
            if not table:
                tbody = soup.find('tbody')
                if tbody:
                    table = tbody.parent if tbody.parent else tbody
                    logger.info("[ThsCrawler] 调试: 通过tbody找到表格")
            
            if not table:
                logger.warning("[ThsCrawler] 未找到板块表格，返回空列表")
                logger.warning(f"[ThsCrawler] 调试: 页面标题: {soup.title.string if soup.title else 'N/A'}")
                return []
            
            logger.info("[ThsCrawler] 步骤5完成: 表格已找到")
            
            # 查找所有行
            all_rows = table.find_all('tr')
            logger.info(f"[ThsCrawler] 调试: 表格总行数: {len(all_rows)}")
            if len(all_rows) > 0:
                logger.info(f"[ThsCrawler] 调试: 第一行内容示例: {all_rows[0].get_text(strip=True)[:100]}")
            
            rows = all_rows[1:] if len(all_rows) > 1 else all_rows  # 跳过表头（如果有）
            logger.info(f"[ThsCrawler] 步骤6: 开始解析表格，共 {len(rows)} 行数据")
            processed_count = 0
            for row_idx, row in enumerate(rows, 1):
                try:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) < 3:  # 至少需要3列：代码、名称、涨跌幅
                        continue
                    
                    # 解析板块数据（只保留表格核心字段）
                    sector_code = cols[0].get_text(strip=True) if len(cols) > 0 else ''
                    sector_name = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                    change_pct = self._parse_number(cols[2].get_text(strip=True)) if len(cols) > 2 else 0.0
                    
                    # 核心字段：上涨/下跌家数、涨停/跌停家数
                    # 使用更灵活的解析方式，支持整数和浮点数
                    def safe_int(text, default=0):
                        """安全地将文本转换为整数"""
                        if not text or text == '-':
                            return default
                        try:
                            # 先尝试转换为浮点数，再转为整数（处理"1277.75"这种情况）
                            return int(float(text.strip().replace(',', '')))
                        except (ValueError, AttributeError):
                            return default
                    
                    up_count = safe_int(cols[3].get_text(strip=True)) if len(cols) > 3 else 0
                    down_count = safe_int(cols[4].get_text(strip=True)) if len(cols) > 4 else 0
                    limit_up_count = safe_int(cols[5].get_text(strip=True)) if len(cols) > 5 else 0
                    limit_down_count = safe_int(cols[6].get_text(strip=True)) if len(cols) > 6 else 0
                    
                    # 计算总股票数（上涨+下跌家数）
                    total_stocks = up_count + down_count
                    
                    if sector_code and sector_name:
                        sectors.append({
                            'code': sector_code,
                            'name': sector_name,
                            'change_pct': change_pct,
                            'up_count': up_count,
                            'down_count': down_count,
                            'limit_up_count': limit_up_count,
                            'limit_down_count': limit_down_count,
                            'total_stocks': total_stocks
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

