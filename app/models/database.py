"""数据库模型"""
import pymysql
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# 尝试加载 .env 文件
# 从 app/models/database.py 向上查找 .env 文件
# 项目结构: personalTool/personalTool-stock-service/personalTool-stock-service/app/models/database.py
# 需要向上5级到达 personalTool/
current_dir = Path(__file__).resolve()
for _ in range(6):  # 尝试向上6级
    env_file = current_dir / '.env'
    if env_file.exists():
        break
    current_dir = current_dir.parent

if env_file.exists():
    # 读取 .env 文件并设置环境变量
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    logger.info(f"已加载环境变量配置: {env_file}")
else:
    logger.warning(f"未找到 .env 文件，已在目录中搜索: {Path(__file__).resolve().parent}")

# MySQL 数据库配置 - 从环境变量读取，必须配置环境变量
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 验证必需的环境变量
required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(
        f"缺少必需的环境变量: {', '.join(missing_vars)}\n"
        f"请在项目根目录的 .env 文件中配置这些变量。\n"
        f"参考 .env.example 文件进行配置。"
    )


def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}", exc_info=True)
        raise


def init_db():
    """初始化数据库表（MySQL 表已手动创建，此函数仅用于测试连接）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        logger.info("MySQL 数据库连接成功")
    except Exception as e:
        logger.error(f"MySQL 数据库连接失败: {e}", exc_info=True)


class MarketReviewModel:
    """市场复盘数据模型"""

    @staticmethod
    def create(review_data: Dict) -> Optional[int]:
        """创建复盘记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO market_review (
                    date, volume, red_count, green_count, limit_up_count, limit_down_count,
                    zt_count, zt_rate, total_continuous_limit, continuous_limit_rate,
                    four_plus_count, four_plus_stocks, two_board_count, three_board_count,
                    three_board_stocks, total_stocks, hot_sectors, notes,
                    red_rate, market_strength, max_continuous_days, first_board_count,
                    three_board_stocks_with_sector, four_plus_stocks_with_sector
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                review_data.get('date'),
                review_data.get('volume', 0),
                review_data.get('red_count', 0),
                review_data.get('green_count', 0),
                review_data.get('limit_up_count', 0),
                review_data.get('limit_down_count', 0),
                review_data.get('zt_count', 0),
                review_data.get('zt_rate', 0),
                review_data.get('total_continuous_limit', 0),
                review_data.get('continuous_limit_rate', 0),
                review_data.get('four_plus_count', 0),
                json.dumps(review_data.get('four_plus_stocks', []), ensure_ascii=False),
                review_data.get('two_board_count', 0),
                review_data.get('three_board_count', 0),
                json.dumps(review_data.get('three_board_stocks', []), ensure_ascii=False),
                review_data.get('total_stocks', 0),
                json.dumps(review_data.get('hot_sectors', []), ensure_ascii=False),
                review_data.get('notes', ''),
                # 新增字段
                review_data.get('red_rate', 0),
                review_data.get('market_strength', ''),
                review_data.get('max_continuous_days', 0),
                review_data.get('first_board_count', 0),
                json.dumps(review_data.get('three_board_stocks_with_sector', []), ensure_ascii=False),
                json.dumps(review_data.get('four_plus_stocks_with_sector', []), ensure_ascii=False)
            ))

            review_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"创建复盘记录成功: date={review_data.get('date')}, id={review_id}")
            return review_id

        except pymysql.IntegrityError as e:
            logger.warning(f"日期 {review_data.get('date')} 的记录已存在: {e}")
            return None
        except Exception as e:
            logger.error(f"创建复盘记录失败: {e}", exc_info=True)
            return None

    @staticmethod
    def get_by_date(date: str) -> Optional[Dict]:
        """根据日期获取复盘记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM market_review WHERE date = %s', (date,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                return MarketReviewModel._row_to_dict(row)
            return None

        except Exception as e:
            logger.error(f"获取复盘记录失败: {e}", exc_info=True)
            return None

    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取所有复盘记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM market_review
                ORDER BY date DESC
                LIMIT %s OFFSET %s
            ''', (limit, offset))

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            return [MarketReviewModel._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"获取复盘记录列表失败: {e}", exc_info=True)
            return []

    @staticmethod
    def update(review_id: int, review_data: Dict) -> bool:
        """更新复盘记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE market_review SET
                    hot_sectors = %s,
                    notes = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (
                json.dumps(review_data.get('hot_sectors', []), ensure_ascii=False),
                review_data.get('notes', ''),
                review_id
            ))

            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()

            if affected_rows > 0:
                logger.info(f"更新复盘记录成功: id={review_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"更新复盘记录失败: {e}", exc_info=True)
            return False

    @staticmethod
    def delete(review_id: int) -> bool:
        """删除复盘记录"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM market_review WHERE id = %s', (review_id,))
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()

            if affected_rows > 0:
                logger.info(f"删除复盘记录成功: id={review_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"删除复盘记录失败: {e}", exc_info=True)
            return False

    @staticmethod
    def _row_to_dict(row) -> Dict:
        """将数据库行转换为字典"""
        # MySQL 返回的是字典格式（使用 DictCursor）
        # 处理 JSON 字段和 datetime 对象
        def parse_json_field(value):
            """解析 JSON 字段"""
            if value is None or value == '' or value == '[]':
                return []
            try:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            except:
                return []

        def format_datetime(value):
            """格式化 datetime 对象"""
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return value.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': row['id'],
            'date': str(row['date']) if row['date'] else None,
            'volume': int(row['volume']) if row['volume'] is not None else 0,
            'red_count': int(row['red_count']) if row['red_count'] is not None else 0,
            'green_count': int(row['green_count']) if row['green_count'] is not None else 0,
            'limit_up_count': int(row['limit_up_count']) if row['limit_up_count'] is not None else 0,
            'limit_down_count': int(row['limit_down_count']) if row['limit_down_count'] is not None else 0,
            'zt_count': int(row['zt_count']) if row['zt_count'] is not None else 0,
            'zt_rate': int(row['zt_rate']) if row['zt_rate'] is not None else 0,
            'total_continuous_limit': int(row['total_continuous_limit']) if row['total_continuous_limit'] is not None else 0,
            'continuous_limit_rate': int(row['continuous_limit_rate']) if row['continuous_limit_rate'] is not None else 0,
            'four_plus_count': int(row['four_plus_count']) if row['four_plus_count'] is not None else 0,
            'four_plus_stocks': parse_json_field(row['four_plus_stocks']),
            'two_board_count': int(row['two_board_count']) if row['two_board_count'] is not None else 0,
            'three_board_count': int(row['three_board_count']) if row['three_board_count'] is not None else 0,
            'three_board_stocks': parse_json_field(row['three_board_stocks']),
            'total_stocks': int(row['total_stocks']) if row['total_stocks'] is not None else 0,
            'hot_sectors': parse_json_field(row['hot_sectors']),
            'notes': row['notes'] if row['notes'] else '',
            'created_at': format_datetime(row['created_at']),
            'updated_at': format_datetime(row['updated_at']),
            # 新增字段
            'red_rate': int(row['red_rate']) if row.get('red_rate') is not None else 0,
            'market_strength': row.get('market_strength', ''),
            'max_continuous_days': int(row['max_continuous_days']) if row.get('max_continuous_days') is not None else 0,
            'first_board_count': int(row['first_board_count']) if row.get('first_board_count') is not None else 0,
            'three_board_stocks_with_sector': parse_json_field(row.get('three_board_stocks_with_sector')),
            'four_plus_stocks_with_sector': parse_json_field(row.get('four_plus_stocks_with_sector'))
        }


# 初始化数据库
init_db()
