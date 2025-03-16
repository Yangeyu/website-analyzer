# Website Analyzer CI/CD 说明

## 自动化构建与部署流程

这个项目使用GitHub Actions实现了自动化的构建和发布流程，当代码推送到主分支时，会自动测试代码、构建Docker镜像并推送到阿里云容器镜像服务。

### 工作流程触发方式

工作流会在以下情况触发:
1. 代码推送到`main`或`master`分支（不包括README等文档更新）
2. 通过GitHub Actions页面手动触发

### 工作流程包含的步骤

工作流分为两个主要任务:

#### 测试任务
1. **检出代码**: 获取最新的代码
2. **设置Python环境**: 配置Python 3.9运行环境并启用pip缓存
3. **安装依赖**: 安装项目依赖和测试工具
4. **运行测试**: 执行项目测试套件

#### 构建和推送任务
1. **检出代码**: 获取最新的代码
2. **生成版本标签**: 创建包含提交的短SHA和时间戳的唯一版本标签
3. **登录容器镜像服务**: 使用安全方式登录阿里云容器镜像服务
4. **构建Docker镜像**: 使用项目Dockerfile构建应用镜像
5. **标记镜像**: 为镜像添加版本标签和latest标签
6. **推送镜像**: 将镜像推送到阿里云容器镜像仓库
7. **输出摘要**: 显示成功推送的镜像信息

### 环境变量

工作流使用以下环境变量:

- `REGISTRY`: 阿里云容器镜像服务地址 (registry.cn-hangzhou.aliyuncs.com)
- `NAMESPACE`: 阿里云容器镜像命名空间 (yang-git)
- `IMAGE_NAME`: 镜像名称 (web-analyzer)
- `DOCKER_USERNAME`: 阿里云容器镜像服务用户名 (aliy6537)

### 配置密钥

使用此工作流需要在GitHub仓库中设置以下密钥:

- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云账号的AccessKey Secret

### 手动部署到Kubernetes

镜像构建完成后，可以手动部署到Kubernetes集群:

```bash
# 拉取最新镜像
docker pull registry.cn-hangzhou.aliyuncs.com/yang-git/web-analyzer:latest

# 应用Kubernetes部署配置
kubectl apply -f k8s-deployment.yaml
```

### 常见问题

1. **测试失败**: 检查测试日志，修复测试问题后重新提交
2. **构建失败**: 检查Dockerfile配置是否正确
3. **推送失败**: 确认阿里云AccessKey权限和有效性
4. **权限问题**: 确保用于推送的账号有足够的权限访问指定的命名空间 