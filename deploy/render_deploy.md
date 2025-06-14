# Render 部署指南

## 🎯 Render 免费部署（最推荐方案）

Render 提供完全免费的 Web Service，非常适合webhook服务！

### 📋 部署步骤

#### 1. 注册账号
```
访问: https://render.com
使用 GitHub 账号注册
```

#### 2. 创建 Web Service
```
1. 点击 "New Web Service"
2. 连接你的 GitHub 仓库
3. 选择分支：main/master
4. 配置如下：
```

#### 3. 部署配置
```yaml
Name: tradingview-webhook
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python webhook_server.py
```

#### 4. 环境变量设置
在 Render 面板中添加：
```
PORT=10000
WEBHOOK_SECRET=your_secret_here
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_SANDBOX=true
MAX_POSITION_SIZE=0.1
```

#### 5. 自动获取 Webhook URL
```
https://your-service-name.onrender.com/webhook
```

### ✅ 优势
- **完全免费** 🆓
- **自动 HTTPS** 🔒
- **自动重启** 🔄
- **GitHub 集成** 📱
- **99.9% 在线率** ⚡

### 📝 注意事项
```
- 服务空闲15分钟后会休眠
- 收到请求时自动唤醒（约30秒）
- 对于webhook完全够用
```
