# NAS Docker界面部署指南（无需SSH）

## 📋 准备工作

### 1. 下载文件到电脑
将 `activation-service` 文件夹下载到本地电脑

### 2. 确认文件结构
```
activation-service/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── templates/
    └── index.html
```

## 🚀 NAS部署步骤（通过Docker界面）

### 步骤1：上传文件到NAS

1. 打开NAS的**File Station**（文件管理器）
2. 创建文件夹：`docker/activation-service`
3. 上传所有文件到这个文件夹
4. 确保文件结构完整

### 步骤2：打开Docker套件

1. 打开NAS的**Docker**应用
2. 进入**项目**标签页

### 步骤3：创建项目

1. 点击**新增**按钮
2. 填写项目信息：
   - **项目名称**：`invoice-activation`
   - **路径**：选择刚才上传的 `docker/activation-service` 文件夹
3. 点击**下一步**

### 步骤4：配置（使用docker-compose.yml）

系统会自动读取 `docker-compose.yml` 文件，显示配置：

```yaml
version: '3.8'

services:
  activation-service:
    build: .
    container_name: invoice-activation
    ports:
      - "6300:5000"
    environment:
      - SECRET_KEY=InvoiceMaster2024SecretKey#@!
    restart: unless-stopped
```

**重要配置说明：**
- **端口 6300**：外部访问端口（可以修改）
- **SECRET_KEY**：必须与InvoiceMaster应用一致

### 步骤5：启动项目

1. 点击**完成**
2. 等待Docker构建镜像（首次需要几分钟）
3. 构建完成后，容器会自动启动

### 步骤6：验证运行

1. 在Docker界面查看容器状态
2. 确认 `invoice-activation` 容器正在运行
3. 状态应该显示为"正在运行"

## 🌐 访问服务

### 电脑访问
打开浏览器，输入：
```
http://NAS的IP地址:6300
```

### 手机访问
1. 确保手机连接到同一WiFi
2. 打开浏览器，输入：
```
http://NAS的IP地址:6300
```

## 🔧 修改配置

### 修改端口（如果6300被占用）

1. 在File Station中编辑 `docker-compose.yml`
2. 修改端口映射：
```yaml
ports:
  - "8080:5000"  # 改为其他端口
```
3. 在Docker界面**停止**项目
4. **启动**项目（会应用新配置）

### 修改密钥

1. 编辑 `docker-compose.yml`
2. 修改 `SECRET_KEY` 值
3. 重启项目

## 📱 使用流程

1. **打开网页**：`http://NAS的IP:6300`
2. **输入机器码**：从InvoiceMaster应用复制
3. **生成激活码**：点击按钮
4. **复制激活码**：点击复制按钮
5. **激活软件**：粘贴到InvoiceMaster

## ⚠️ 常见问题

### 1. 无法访问网页
- 检查NAS防火墙是否开放6300端口
- 在Docker界面确认容器正在运行
- 尝试用NAS的IP地址，不要用localhost

### 2. 容器无法启动
- 检查端口是否被占用
- 查看Docker日志（容器详情 → 日志）
- 确认所有文件都已上传

### 3. 生成的激活码无效
- 确认SECRET_KEY与InvoiceMaster一致
- 检查机器码是否正确复制（包含连字符）

## 🛠️ 管理操作

### 查看日志
1. Docker界面 → **容器**
2. 选择 `invoice-activation`
3. 点击**详情** → **日志**

### 停止服务
1. Docker界面 → **项目**
2. 选择 `invoice-activation`
3. 点击**停止**

### 重启服务
1. 停止项目
2. 点击**启动**

### 更新服务
1. 修改文件后
2. 停止项目
3. 点击**构建** → **启动**

## 💡 提示

- ✅ 首次构建需要下载Python镜像，需要几分钟
- ✅ 后续启动很快，几秒钟即可
- ✅ 容器会自动重启（除非手动停止）
- ✅ 支持所有浏览器和手机访问

## 🔒 安全建议

1. **局域网使用**：不要暴露到公网
2. **修改密钥**：不要使用默认SECRET_KEY
3. **定期更新**：保持Docker镜像最新
