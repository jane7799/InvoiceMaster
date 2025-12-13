# 激活码生成服务 - NAS部署指南

## 📦 项目说明

这是一个Docker化的激活码生成Web服务，可以部署在NAS上，通过浏览器（包括手机）访问生成激活码。

## 🚀 快速部署（NAS）

### 方式一：使用Docker Compose（推荐）

1. **上传文件到NAS**
   - 将整个 `activation-service` 文件夹上传到NAS
   - 建议路径：`/volume1/docker/activation-service`

2. **SSH登录NAS**
   ```bash
   ssh your-nas-username@nas-ip
   ```

3. **进入目录**
   ```bash
   cd /volume1/docker/activation-service
   ```

4. **启动服务**
   ```bash
   docker-compose up -d
   ```

5. **访问服务**
   - 浏览器打开：`http://NAS的IP:5000`
   - 手机也可以访问

### 方式二：群晖NAS Docker界面

1. **打开Docker套件**
2. **注册表** → 搜索 `python` → 下载 `python:3.9-slim`
3. **映像** → 选择python镜像 → **启动**
4. **配置容器**：
   - 容器名称：`invoice-activation`
   - 端口设置：本地端口 `5000` → 容器端口 `5000`
   - 卷：将activation-service文件夹挂载到 `/app`
   - 环境变量：`SECRET_KEY=InvoiceMaster2024SecretKey#@!`
   - 命令：`python /app/app.py`

## 🔧 配置说明

### 修改密钥（重要）

编辑 `docker-compose.yml`，修改 `SECRET_KEY`：
```yaml
environment:
  - SECRET_KEY=你的自定义密钥
```

**注意**：密钥必须与InvoiceMaster应用中的密钥一致！

### 修改端口

如果5000端口被占用，修改 `docker-compose.yml`：
```yaml
ports:
  - "8080:5000"  # 改为8080或其他端口
```

## 📱 使用方法

1. **打开浏览器**
   - 电脑：`http://NAS的IP:5000`
   - 手机：`http://NAS的IP:5000`

2. **输入机器码**
   - 从InvoiceMaster应用的设置中复制机器码

3. **生成激活码**
   - 点击"生成激活码"按钮

4. **复制激活码**
   - 点击"复制激活码"按钮
   - 粘贴到InvoiceMaster应用中激活

## 🔒 安全建议

### 1. 局域网访问（推荐）
- 只在家庭/公司内网使用
- 不暴露到公网

### 2. 公网访问（需要额外配置）
如果需要外网访问：
- 使用反向代理（Nginx）
- 配置HTTPS证书
- 添加访问密码保护

### 3. 修改默认密钥
- 不要使用默认的SECRET_KEY
- 使用强密码

## 🛠️ 管理命令

### 查看日志
```bash
docker-compose logs -f
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 更新服务
```bash
docker-compose down
docker-compose up -d --build
```

## 📊 健康检查

访问 `http://NAS的IP:5000/health` 查看服务状态

## ❓ 常见问题

### 1. 无法访问服务
- 检查NAS防火墙是否开放5000端口
- 检查Docker容器是否正常运行：`docker ps`

### 2. 生成的激活码无效
- 确认SECRET_KEY与InvoiceMaster应用一致
- 检查机器码是否正确复制

### 3. 手机无法访问
- 确保手机和NAS在同一局域网
- 使用NAS的IP地址，不要用localhost

## 📞 支持

如有问题，请检查：
1. Docker容器日志
2. NAS防火墙设置
3. 网络连接状态
