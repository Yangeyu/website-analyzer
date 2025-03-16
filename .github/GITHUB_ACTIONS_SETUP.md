# GitHub Actions 配置指南

本文档将指导你如何配置GitHub仓库的密钥，以便GitHub Actions能够自动构建和部署Website Analyzer到阿里云容器服务。

## 必需的GitHub Secrets

在GitHub仓库中，需要配置以下Secrets（密钥）：

### 阿里云访问凭证

- `ALIYUN_ACCESS_KEY_ID`: 阿里云账号的AccessKey ID
- `ALIYUN_ACCESS_KEY_SECRET`: 阿里云账号的AccessKey Secret
- `ACK_CLUSTER_ID`: 阿里云容器服务Kubernetes集群的ID

### 应用配置

- `LLM_PROVIDER`: LLM提供商，例如"openai"
- `LLM_MODEL`: 模型名称，例如"openai/qwen-max"
- `LLM_BASE_URL`: API基础URL，例如"https://dashscope.aliyuncs.com/compatible-mode/v1"
- `LLM_API_KEY`: API密钥
- `LLM_TEMPERATURE`: 生成的随机性，例如"0.0"
- `DEFAULT_CRAWL_DELAY`: 默认爬取延时（秒），例如"1.0"
- `DEFAULT_USER_AGENT`: 默认用户代理字符串

## 配置步骤

1. 在GitHub仓库页面，点击 **Settings** 选项卡
2. 在左侧导航栏中，点击 **Secrets and variables** > **Actions**
3. 点击 **New repository secret** 按钮
4. 填写密钥名称和值
5. 点击 **Add secret** 按钮

对每个必需的密钥重复上述步骤。

## 获取阿里云凭证

### 获取AccessKey

1. 登录[阿里云控制台](https://home.console.aliyun.com/)
2. 点击右上角头像，选择 **AccessKey管理**
3. 点击 **创建AccessKey**
4. 完成安全验证后，记录AccessKey ID和AccessKey Secret

> **重要**：出于安全考虑，建议创建RAM用户并授予最小权限，而不是使用主账号的AccessKey。

### 获取ACK集群ID

1. 登录[容器服务控制台](https://cs.console.aliyun.com/)
2. 找到你的Kubernetes集群
3. 集群ID会显示在集群列表或集群详情页中

## 环境变量自定义

在workflow文件(.github/workflows/deploy-to-aliyun.yml)中，需要修改以下环境变量：

```yaml
env:
  ACR_REGISTRY: registry.cn-hangzhou.aliyuncs.com  # 根据你的地域调整
  ACR_NAMESPACE: your-namespace  # 替换为你的命名空间名称
  IMAGE_NAME: website-analyzer
  K8S_NAMESPACE: default  # 替换为你的Kubernetes命名空间
```

- `ACR_REGISTRY`: 阿里云容器镜像服务注册表地址，根据你的地域调整
- `ACR_NAMESPACE`: 你在容器镜像服务中创建的命名空间
- `IMAGE_NAME`: 镜像名称，通常保持为website-analyzer
- `K8S_NAMESPACE`: Kubernetes命名空间，如果有特定命名空间则修改

## 权限要求

确保用于部署的AccessKey拥有以下权限：

1. 容器镜像服务（ACR）的推送权限
2. 容器服务Kubernetes版（ACK）的管理权限
3. 如需配置报警等功能，还需要相应服务的权限

## 故障排查

如果部署过程遇到问题：

1. 查看GitHub Actions运行日志，识别失败的具体阶段
2. 检查密钥是否正确配置
3. 确保阿里云服务正常运行
4. 验证部署配置文件(k8s-deployment.yaml)格式正确

## 安全最佳实践

1. 使用具有最小权限的RAM用户
2. 定期轮换AccessKey
3. 不要在代码中硬编码任何敏感信息
4. 考虑启用分支保护，限制谁可以推送到主分支

## 更多资源

- [GitHub Actions文档](https://docs.github.com/cn/actions)
- [阿里云容器服务文档](https://help.aliyun.com/product/85222.html)
- [kubectl命令参考](https://kubernetes.io/zh/docs/reference/kubectl/overview/) 