# FastAPI Hello World

一个简单的FastAPI应用，返回"hello"消息。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
uvicorn main:app --reload
```

运行后，访问 http://127.0.0.1:8000/hello 将看到 `{"message": "hello"}` 的响应。

## API文档

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc 