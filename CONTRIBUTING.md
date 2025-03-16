# 贡献指南

感谢您对website-analyzer项目的关注！本文档将指导您如何参与贡献代码。

## Git工作流程

我们采用基于[Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)的分支管理策略：

### 主要分支

- `main`: 生产环境分支，保持稳定
- `develop`: 开发分支，新功能的集成点

### 功能分支

当开发新功能时，请从`develop`分支创建一个功能分支：

```bash
git checkout develop
git pull origin develop
git checkout -b feature/功能名称
```

### 提交规范

提交信息应当清晰描述更改内容，建议使用以下格式：

```
<类型>: <描述>

[可选的详细说明]

[可选的相关问题引用]
```

类型包括：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更改
- `style`: 代码风格更改（不影响代码功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

### 合并请求流程

1. 完成功能开发后，使用以下命令推送到远程仓库：
   ```bash
   git push origin feature/功能名称
   ```

2. 在Git平台（如GitHub、GitLab）上创建合并请求（Merge/Pull Request）到`develop`分支

3. 代码审查通过后，合并到`develop`分支

4. 定期将`develop`分支合并到`main`分支进行发布

## 发布流程

当准备发布新版本时：

1. 从`develop`分支创建`release`分支：
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v版本号
   ```

2. 在`release`分支上进行最终测试和bug修复

3. 完成后，将`release`分支合并到`main`和`develop`分支：
   ```bash
   git checkout main
   git merge release/v版本号
   git push origin main
   
   git checkout develop
   git merge release/v版本号
   git push origin develop
   ```

4. 在`main`分支上创建版本标签：
   ```bash
   git checkout main
   git tag -a v版本号 -m "版本说明"
   git push origin v版本号
   ```

## 常用Git命令

### 基础命令

```bash
# 克隆仓库
git clone https://github.com/yourusername/website-analyzer.git

# 查看状态
git status

# 添加更改
git add .

# 提交更改
git commit -m "提交说明"

# 推送到远程
git push origin 分支名

# 获取远程更新
git pull origin 分支名
```

### 分支操作

```bash
# 查看所有分支
git branch -a

# 创建新分支
git checkout -b 新分支名

# 切换分支
git checkout 分支名

# 删除本地分支
git branch -d 分支名

# 删除远程分支
git push origin --delete 分支名
```

### 解决冲突

当出现合并冲突时：

1. 打开冲突文件，找到`<<<<<<<`, `=======`, `>>>>>>>`标记的区域
2. 编辑文件解决冲突
3. 添加解决后的文件：`git add 冲突文件`
4. 完成合并：`git commit`

## 代码规范

- 请遵循项目现有的代码风格
- 添加适当的文档注释
- 编写单元测试覆盖新功能
- 确保所有测试通过：`python run_tests.py`

感谢您的贡献！ 