# Website Analyzer

一个基于 Crawl4AI 的网站分析工具，可以从网站生成结构化的 Markdown 内容。

## 功能特点

- 抓取网站内容并生成高质量的 Markdown 格式数据
- 支持单页面和多页面抓取
- 提取和分析网页元数据（标题、描述、关键词等）
- 分析和提取网页链接（内部链接和外部链接）
- 保存原始HTML内容（可选）
- 提供智能爬取延时，避免对目标网站请求过快
- 支持自定义用户代理，避免被目标网站封锁
- 提供 RESTful API 和命令行界面
- 自动保存抓取结果到临时文件夹
- 支持后台任务处理

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/website-analyzer.git
cd website-analyzer
```

2. 创建虚拟环境（可选但推荐）：

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 安装浏览器环境（如有必要）：

```bash
python -m playwright install --with-deps chromium
```

## 使用方法

### 命令行界面

1. 抓取单个网页：

```bash
python main.py crawl https://example.com
```

2. 限制抓取页面数量：

```bash
python main.py crawl https://example.com --max-pages 5
```

3. 开启HTML保存和元数据提取：

```bash
python main.py crawl https://example.com --save-html --extract-metadata
```

4. 设置爬取延时和自定义用户代理：

```bash
python main.py crawl https://example.com --crawl-delay 1.5 --user-agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
```

5. 分析并保存链接：

```bash
python main.py crawl https://example.com --save-links
```

6. 查看已保存的文件：

```bash
python main.py list
```

### 多页面爬取

1. 从文件爬取多个URL：

```bash
python main.py crawl-batch urls.txt --crawl-delay 2.0
```

2. 爬取特定深度的页面：

```bash
python main.py crawl https://example.com --max-pages 10 --depth 2 --follow-links
```

### API 服务

1. 启动 API 服务器：

```bash
python main.py serve
```

2. 使用 API 进行基本抓取：

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 1}'
```

3. 使用 API 进行高级抓取：

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com", 
    "max_pages": 5, 
    "depth": 2,
    "follow_links": true,
    "save_html": true,
    "extract_metadata": true,
    "save_links": true,
    "crawl_delay": 1.0
  }'
```

4. 批量抓取多个URL：

```bash
curl -X POST "http://localhost:8000/crawl-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://another-example.com"],
    "crawl_delay": 2.0
  }'
```

5. 获取文件列表：

```bash
curl "http://localhost:8000/files"
```

6. 获取特定文件内容：

```bash
curl "http://localhost:8000/files/example-com_20230101_123456.md"
```

## 高级配置

### WebsiteCrawlerService 类选项

```python
from src.crawler import WebsiteCrawlerService

# 创建基本爬虫服务
crawler = WebsiteCrawlerService()

# 创建高级爬虫服务
advanced_crawler = WebsiteCrawlerService(
    output_dir=Path("./custom_output"),  # 自定义输出目录
    save_html=True,                     # 保存HTML内容
    user_agent="自定义用户代理",         # 指定用户代理
    crawl_delay=1.5,                    # 设置爬取延时（秒）
    extract_metadata=True               # 提取元数据
)

# 抓取单个URL
result = await advanced_crawler.crawl_url(
    url="https://example.com",
    max_pages=5,                        # 最大页面数
    depth=2,                            # 最大深度
    follow_links=True,                  # 跟随链接
    save_links=True                     # 保存链接分析
)

# 批量抓取多个URL
results = await advanced_crawler.crawl_multiple_urls(
    urls=["https://example.com", "https://another-example.com"],
    max_pages_per_url=3,
    crawl_delay=2.0                     # 覆盖实例的爬取延时
)
```

## API 文档

API 服务运行后，可以访问以下端点获取 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 运行测试

项目包含全面的单元测试，用于验证爬虫功能和内容提取质量。

1. 运行所有测试：

```bash
python run_tests.py
```

2. 运行特定测试：

```bash
python -m unittest tests.test_crawler
python -m unittest tests.test_openai_agents
```

3. 测试报告将保存在 `test_reports` 目录中。

### 测试特性

- 基本爬虫功能测试
- 标题提取功能测试
- 元数据提取功能测试
- 链接分析功能测试
- 抓取 OpenAI Agents SDK 文档页面的专门测试
- 内容相关性和质量测试
- 文档结构和代码示例检测
- 多页面爬取功能测试

## 项目结构

```
website-analyzer/
├── data/
│   └── temp/         # 保存抓取结果的临时文件夹
│       └── html/     # 保存原始HTML内容的子文件夹
├── src/
│   ├── __init__.py
│   ├── api.py        # FastAPI 接口定义
│   └── crawler.py    # 网站抓取服务
├── tests/
│   ├── __init__.py
│   ├── test_crawler.py      # 基本爬虫测试
│   └── test_openai_agents.py # OpenAI Agents SDK 页面测试
├── test_reports/     # 测试报告输出目录
├── main.py           # 主入口点
├── run_tests.py      # 测试运行脚本
├── README.md
├── CONTRIBUTING.md   # 贡献指南
└── requirements.txt  # 项目依赖
```

## 贡献

请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何贡献代码。

## 许可证

MIT
