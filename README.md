# Website Analyzer

一个基于 Crawl4AI 的网站分析工具，可以从网站生成结构化的 Markdown 内容。

## 功能特点

- 抓取网站内容并生成高质量的 Markdown 格式数据
- 支持单页面和多页面抓取
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

3. 查看已保存的文件：

```bash
python main.py list
```

### API 服务

1. 启动 API 服务器：

```bash
python main.py serve
```

2. 使用 API 进行抓取：

```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 1}'
```

3. 获取文件列表：

```bash
curl "http://localhost:8000/files"
```

4. 获取特定文件内容：

```bash
curl "http://localhost:8000/files/example-com_20230101_123456.md"
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
- 抓取 OpenAI Agents SDK 文档页面的专门测试
- 内容相关性和质量测试
- 文档结构和代码示例检测

## 项目结构

```
website-analyzer/
├── data/
│   └── temp/         # 保存抓取结果的临时文件夹
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
└── requirements.txt  # 项目依赖
```

## 许可证

MIT
