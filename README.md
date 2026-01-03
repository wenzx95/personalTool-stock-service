# PersonalTool Stock Service

个人工具集A股分析服务 - 基于FastAPI，提供A股数据抓取和金融分析功能。

## 技术栈

- FastAPI 0.109.0
- Selenium + BeautifulSoup（数据抓取）
- Pandas + NumPy（数据处理）
- TA-Lib（技术指标）
- APScheduler（定时任务）

## 功能模块

- 板块数据抓取（同花顺）
- 个股数据抓取
- 资金流向分析
- 技术指标计算
- 板块轮动分析
- 市场情绪分析

## 快速开始

### 环境要求

- Python 3.11+
- Chrome/Chromium浏览器（用于Selenium）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

### 运行

```bash
# 开发环境
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker构建

```bash
docker build -t personalTool-stock-service:latest .
docker run -p 8000:8000 personalTool-stock-service:latest
```

## API文档

启动服务后访问：http://localhost:8000/docs

## 项目结构

```
app/
├── api/                    # API路由
│   ├── stock.py           # 个股接口
│   └── sector.py          # 板块接口
├── crawler/               # 数据抓取
│   └── ths_crawler.py     # 同花顺抓取器
├── service/                # 业务逻辑
├── scheduler.py            # 定时任务
└── core/                   # 核心配置
    └── config.py           # 应用配置
```

## 定时任务

- 每日15:30自动执行复盘任务
- 抓取板块和个股数据
- 生成分析报告

