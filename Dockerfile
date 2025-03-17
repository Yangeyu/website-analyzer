FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PORT=8000

# 暴露端口
EXPOSE ${PORT}

# 启动命令
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} 