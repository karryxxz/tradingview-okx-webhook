#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - TradingView Webhook & OKX交易设置

重要提示：
1. 请在OKX官网申请API密钥，并确保开启合约交易权限
2. 建议先在测试网测试，确认无误后再使用正式环境
3. 请妥善保管API密钥，不要泄露给他人

配置步骤：
1. 将your_api_key等占位符替换为真实的API信息
2. 根据需要调整风险控制参数
3. 确保服务器具有公网IP（用于接收TradingView webhook）
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # ===== 服务器配置 =====
    SERVER_PORT = int(os.getenv('SERVER_PORT', 8080))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Webhook安全密钥（可选，用于验证TradingView请求）
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')
    
    # ===== OKX API配置 =====
    # 请在OKX官网申请API密钥: https://www.okx.com/account/my-api
    OKX_API_KEY = os.getenv('OKX_API_KEY', 'your_api_key')
    OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', 'your_secret_key')
    OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', 'your_passphrase')
    
    # API环境设置
    # 测试环境: True (使用demo-aws环境进行测试)
    # 正式环境: False (使用正式交易环境)
    OKX_SANDBOX = os.getenv('OKX_SANDBOX', 'True').lower() == 'true'
    
    # ===== 交易风险控制 =====
    # 是否启用实际交易（False=只记录日志，不实际下单）
    ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'False').lower() == 'true'
    
    # 最大单次交易仓位（BTC数量）
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.1'))
    
    # 最大杠杆倍数
    MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '10'))
    
    # 最大持仓总价值（USDT）
    MAX_TOTAL_POSITION_VALUE = float(os.getenv('MAX_TOTAL_POSITION_VALUE', '1000'))
    
    # 每日最大交易次数
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '20'))
    
    # ===== 交易参数 =====
    # 默认订单类型 ('market' 市价单, 'limit' 限价单)
    DEFAULT_ORDER_TYPE = os.getenv('DEFAULT_ORDER_TYPE', 'market')
    
    # 市价单滑点容忍度（百分比）
    SLIPPAGE_TOLERANCE = float(os.getenv('SLIPPAGE_TOLERANCE', '0.1'))
    
    # 订单超时时间（秒）
    ORDER_TIMEOUT = int(os.getenv('ORDER_TIMEOUT', '30'))
    
    # ===== 通知设置 =====
    # 微信通知（可选，需要企业微信机器人）
    WECHAT_WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL', '')
    
    # 邮件通知（可选）
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', '')
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    
    # ===== 日志配置 =====
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading.log')
    MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ===== 支持的交易对 =====
    SUPPORTED_SYMBOLS = [
        'BTC-USDT-SWAP',
        'ETH-USDT-SWAP',
        'ADA-USDT-SWAP',
        'DOT-USDT-SWAP',
        'LINK-USDT-SWAP',
        'LTC-USDT-SWAP',
        'BCH-USDT-SWAP',
        'XRP-USDT-SWAP',
        'EOS-USDT-SWAP',
        'TRX-USDT-SWAP'
    ]
    
    @classmethod
    def validate_config(cls):
        """验证配置是否正确"""
        errors = []
        
        # 检查API密钥
        if cls.OKX_API_KEY == 'your_api_key':
            errors.append("请配置真实的OKX_API_KEY")
        
        if cls.OKX_SECRET_KEY == 'your_secret_key':
            errors.append("请配置真实的OKX_SECRET_KEY")
        
        if cls.OKX_PASSPHRASE == 'your_passphrase':
            errors.append("请配置真实的OKX_PASSPHRASE")
        
        # 检查风险参数
        if cls.MAX_POSITION_SIZE <= 0:
            errors.append("MAX_POSITION_SIZE必须大于0")
        
        if cls.MAX_LEVERAGE <= 0 or cls.MAX_LEVERAGE > 100:
            errors.append("MAX_LEVERAGE必须在1-100之间")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("=== 当前配置 ===")
        print(f"服务器端口: {cls.SERVER_PORT}")
        print(f"调试模式: {cls.DEBUG}")
        print(f"OKX测试环境: {cls.OKX_SANDBOX}")
        print(f"实际交易: {cls.ENABLE_TRADING}")
        print(f"最大仓位: {cls.MAX_POSITION_SIZE} BTC")
        print(f"最大杠杆: {cls.MAX_LEVERAGE}x")
        print(f"API密钥: {'已配置' if cls.OKX_API_KEY != 'your_api_key' else '未配置'}")
        print("================")

# 全局配置验证
if __name__ == '__main__':
    errors = Config.validate_config()
    if errors:
        print("⚠️  配置错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 配置检查通过")
    
    Config.print_config()
