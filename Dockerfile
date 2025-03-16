FROM python:3.9-slim

WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright和Chromium
RUN pip install playwright && \
    python -m playwright install --with-deps chromium

# 创建数据目录
RUN mkdir -p /app/data/temp/html && \
    chmod -R 777 /app/data

# 配置环境
ENV HOST=0.0.0.0
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8000"] 