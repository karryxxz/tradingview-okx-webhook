#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - TradingView Webhook自动交易系统

这个脚本会帮你：
1. 检查环境配置
2. 验证OKX API连接
3. 启动webhook服务器
4. 提供系统状态监控

使用方法：
python start_server.py
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from config import Config
from okx_trader import OKXTrader
from webhook_server import app

# 设置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║               TradingView Webhook 自动交易系统                    ║
║                     Version 1.0                                 ║
║                                                                  ║
║  功能特点：                                                        ║
║  • 接收TradingView策略信号                                         ║
║  • 自动执行OKX合约交易                                             ║
║  • 完整的风险控制和日志记录                                          ║
║  • 支持止损止盈设置                                                ║
║                                                                  ║
║  ⚠️  风险提示：请先在测试环境验证功能，确认无误后再实盘使用            ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_environment():
    """检查环境配置"""
    print("\n🔍 检查环境配置...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查环境变量文件
    if not os.path.exists('.env'):
        print("⚠️  未找到.env配置文件")
        print("   请复制.env.example为.env并配置真实的API信息")
        
        # 自动创建基础.env文件
        try:
            with open('.env.example', 'r', encoding='utf-8') as f:
                content = f.read()
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ 已自动创建.env文件，请编辑配置后重新启动")
        except Exception as e:
            print(f"❌ 创建.env文件失败: {e}")
        
        return False
    
    print("✅ 环境配置文件存在")
    
    # 验证配置
    errors = Config.validate_config()
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ 配置验证通过")
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = [
        'flask',
        'okx',
        'python-dotenv',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def test_okx_connection():
    """测试OKX API连接"""
    print("\n🔗 测试OKX API连接...")
    
    try:
        trader = OKXTrader()
        
        if trader.check_connection():
            print("✅ OKX API连接成功")
            
            # 获取账户信息
            balance = trader.get_balance()
            if balance['success']:
                print("✅ 账户信息获取成功")
            else:
                print(f"⚠️  账户信息获取失败: {balance.get('error')}")
            
            return True
        else:
            print("❌ OKX API连接失败")
            return False
            
    except Exception as e:
        print(f"❌ OKX连接测试异常: {e}")
        return False

def print_configuration():
    """打印当前配置"""
    print("\n⚙️  当前配置:")
    Config.print_config()
    print(f"Webhook URL: http://localhost:{Config.SERVER_PORT}/webhook")
    print(f"状态页面: http://localhost:{Config.SERVER_PORT}/status")
    print(f"健康检查: http://localhost:{Config.SERVER_PORT}/health")

def print_next_steps():
    """打印后续步骤说明"""
    steps = f"""
🚀 系统启动成功！

📋 接下来的配置步骤：

1️⃣ 配置TradingView策略:
   • 打开TradingView，加载你的策略
   • 在策略设置中找到"Webhook设置"
   • 启用Webhook交易
   • 设置仓位大小和杠杆倍数

2️⃣ 设置TradingView Alert:
   • 在策略图表上右键 → "添加提醒"
   • 条件选择: 策略名称 → Order fills only
   • Webhook URL: http://你的服务器IP:{Config.SERVER_PORT}/webhook
   • 消息格式: 自动（使用策略内置JSON格式）

3️⃣ 测试流程:
   • 先在测试环境验证信号接收
   • 检查日志文件: {Config.LOG_FILE}
   • 确认交易逻辑正确后，在config.py中设置ENABLE_TRADING=True

4️⃣ 监控系统:
   • 实时日志: tail -f {Config.LOG_FILE}
   • 系统状态: http://localhost:{Config.SERVER_PORT}/status
   • 持仓信息: http://localhost:{Config.SERVER_PORT}/positions

⚠️  重要提醒:
   • 确保服务器有公网IP或使用内网穿透工具
   • 建议设置防火墙只允许TradingView IP访问
   • 定期检查日志和系统状态
   • 首次使用请小仓位测试

💡 故障排除:
   • 如果TradingView无法访问webhook，检查网络和防火墙设置
   • 如果交易失败，检查OKX API权限和余额
   • 详细错误信息请查看日志文件

按Ctrl+C停止服务器
    """
    print(steps)

def signal_handler(sig, frame):
    """处理退出信号"""
    print("\n\n👋 正在关闭系统...")
    print("感谢使用TradingView Webhook自动交易系统！")
    sys.exit(0)

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 打印启动横幅
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请修复后重试")
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的包")
        sys.exit(1)
    
    # 测试OKX连接
    if not test_okx_connection():
        print("\n❌ OKX连接测试失败，请检查API配置")
        if Config.OKX_SANDBOX:
            print("💡 当前使用测试环境，请确保API密钥支持测试环境")
        sys.exit(1)
    
    # 打印配置信息
    print_configuration()
    
    # 记录启动信息
    logger.info("TradingView Webhook自动交易系统启动")
    logger.info(f"监听端口: {Config.SERVER_PORT}")
    logger.info(f"交易模式: {'启用' if Config.ENABLE_TRADING else '禁用'}")
    logger.info(f"OKX环境: {'测试' if Config.OKX_SANDBOX else '正式'}")
    
    try:
        # 启动Flask服务器
        print("\n🚀 启动Webhook服务器...")
        print_next_steps()
        
        app.run(
            host='0.0.0.0',
            port=Config.SERVER_PORT,
            debug=Config.DEBUG,
            use_reloader=False  # 避免重复启动检查
        )
        
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        print(f"\n❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
