from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_hello_endpoint():
    """测试 /hello 端点是否正常工作"""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"} 