#!/usr/bin/env python3
import pytest
import sys

if __name__ == "__main__":
    # 运行所有测试
    result = pytest.main(["-v"])
    
    # 检查测试结果，返回适当的退出代码
    sys.exit(result) 