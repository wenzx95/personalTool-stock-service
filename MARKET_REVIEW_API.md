# 市场复盘数据API文档

## 概述

已创建市场复盘数据获取服务，使用 `akshare` 库获取A股市场复盘数据。

## API端点

### GET `/api/market/review`

获取市场复盘数据

**参数:**
- `trade_date` (可选): 交易日期，格式：YYYYMMDD，默认为今天
  - 示例: `20250105`

**返回数据字段:**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "date": "2025-01-05",              // 日期
    "volume": 1234567890,              // 成交量
    "red_count": 2500,                 // 红盘（上涨家数）
    "green_count": 1800,               // 绿盘（下跌家数）
    "limit_up_count": 50,              // 涨停
    "limit_down_count": 10,            // 跌停
    "zt_count": 5,                     // 炸板数量
    "zt_rate": 10.0,                   // 炸板率(%)
    "total_continuous_limit": 30,      // 总连板
    "continuous_limit_rate": 0.6,      // 连板率(%)
    "four_plus_count": 5,              // 4板及以上个数
    "four_plus_stocks": [              // 4板及以上个股
      {"代码": "000001", "名称": "平安银行"},
      ...
    ],
    "two_board_count": 15,             // 二板个数
    "three_board_count": 10,           // 三板个数
    "three_board_stocks": [            // 三板个股
      {"代码": "000002", "名称": "万科A"},
      ...
    ],
    "total_stocks": 5000               // 总家数
  }
}
```

## 使用示例

### 获取今天的数据

```bash
curl http://localhost:8000/api/market/review
```

### 获取指定日期的数据

```bash
curl "http://localhost:8000/api/market/review?trade_date=20250105"
```

### Python示例

```python
import requests

# 获取今天的数据
response = requests.get("http://localhost:8000/api/market/review")
data = response.json()
print(data)

# 获取指定日期的数据
response = requests.get("http://localhost:8000/api/market/review", params={"trade_date": "20250105"})
data = response.json()
print(data)
```

## 数据来源

使用 `akshare` 库获取数据：
- 涨停板数据: `ak.stock_zt_pool_em()`
- 跌停板数据: `ak.stock_dt_pool_em()`
- 市场统计: `ak.stock_zh_a_spot_em()`

## 注意事项

1. **依赖要求**: 需要安装 `akshare` 和 `py_mini_racer`
2. **Python版本**: 建议使用 Python 3.9+（当前使用 3.8 可能有兼容性问题）
3. **数据可用性**: 某些数据可能只在交易日可用
4. **API限制**: akshare 可能有请求频率限制

## 安装依赖

```bash
pip install akshare py_mini_racer
```

## 字段说明

- **日期**: 交易日期
- **成交量**: 市场总成交量
- **红盘**: 上涨股票数量
- **绿盘**: 下跌股票数量
- **涨停**: 涨停股票数量
- **跌停**: 跌停股票数量
- **炸板**: 涨停后开板的股票数量
- **炸板率**: 炸板数 / 涨停数 × 100%
- **总连板**: 连续涨停的股票总数
- **连板率**: 总连板数 / 总股票数 × 100%
- **4板及以上**: 连续4个或以上涨停的股票
- **二板**: 连续2个涨停的股票数量
- **三板**: 连续3个涨停的股票数量
- **总家数**: A股市场总股票数

