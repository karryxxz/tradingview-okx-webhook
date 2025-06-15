#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView Webhook服务器 - 对接OKX合约交易
接收TradingView策略信号并自动执行OKX合约下单

作者: AlgoAlpha Team
版本: 1.0
创建日期: 2024-06-14
"""

from flask import Flask, request, jsonify
import json
import hmac
import hashlib
import logging
from datetime import datetime
import threading
import time
from okx_trader import OKXTrader
from config import Config
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 初始化OKX交易器
okx_trader = OKXTrader()

# 请求验证函数
def verify_webhook_signature(payload, signature, secret):
    """
    验证TradingView webhook签名
    """
    if not secret:
        return True  # 如果没有设置密钥，则跳过验证
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    接收TradingView webhook信号的主要处理函数
    """
    try:
        # 获取原始数据
        raw_data = request.get_data()
        logger.info(f"收到webhook请求，数据长度: {len(raw_data)} bytes")
        
        # 验证签名（如果配置了密钥）
        signature = request.headers.get('X-TradingView-Signature', '')
        if Config.WEBHOOK_SECRET and not verify_webhook_signature(raw_data, signature, Config.WEBHOOK_SECRET):
            logger.warning("Webhook签名验证失败")
            return jsonify({'error': '签名验证失败'}), 401
        
        # 解析JSON数据
        try:
            signal_data = json.loads(raw_data.decode('utf-8'))
            logger.info(f"解析webhook信号: {signal_data}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return jsonify({'error': 'Invalid JSON'}), 400
        
        # 验证必要字段
        required_fields = ['action', 'symbol', 'price', 'size']
        missing_fields = [field for field in required_fields if field not in signal_data]
        if missing_fields:
            logger.error(f"缺少必要字段: {missing_fields}")
            return jsonify({'error': f'缺少必要字段: {missing_fields}'}), 400
        
        # 异步处理交易信号
        threading.Thread(
            target=process_trading_signal,
            args=(signal_data,),
            daemon=True
        ).start()
        
        return jsonify({
            'status': 'received',
            'message': '信号已接收，正在处理',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"webhook处理异常: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_trading_signal(signal_data):
    """
    处理交易信号的核心函数
    """
    try:
        logger.info(f"开始处理交易信号: {signal_data}")
        
        # 提取信号信息
        action = signal_data.get('action')  # 'buy' 或 'sell'
        symbol = signal_data.get('symbol')  # 交易对
        price = float(signal_data.get('price', 0))
        size = float(signal_data.get('size', 0))
        leverage = int(signal_data.get('leverage', 10))
        stop_loss = float(signal_data.get('stop_loss', 0))
        take_profit = float(signal_data.get('take_profit', 0))
        
        # 转换交易对格式（TradingView -> OKX）
        okx_symbol = convert_symbol_format(symbol)
        
        # 验证交易参数
        if not validate_trading_params(action, okx_symbol, size, leverage):
            return
        
        # 执行交易
        if action.lower() == 'buy':
            # 开多仓
            result = okx_trader.open_long_position(
                symbol=okx_symbol,
                size=size,
                leverage=leverage,
                stop_loss=stop_loss if stop_loss > 0 else None,
                take_profit=take_profit if take_profit > 0 else None
            )
        elif action.lower() == 'sell':
            # 开空仓
            result = okx_trader.open_short_position(
                symbol=okx_symbol,
                size=size,
                leverage=leverage,
                stop_loss=stop_loss if stop_loss > 0 else None,
                take_profit=take_profit if take_profit > 0 else None
            )
        else:
            logger.error(f"不支持的交易动作: {action}")
            return
        
        # 记录结果
        if result.get('success'):
            logger.info(f"交易执行成功: {result}")
            
            # 发送成功通知（可选）
            send_notification(f"✅ 交易成功: {action.upper()} {size} {okx_symbol}")
        else:
            logger.error(f"交易执行失败: {result}")
            
            # 发送失败通知（可选）
            send_notification(f"❌ 交易失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"处理交易信号异常: {str(e)}")
        send_notification(f"🚨 交易异常: {str(e)}")

def convert_symbol_format(tv_symbol):
    """
    将TradingView符号转换为OKX格式
    例: BTCUSDT -> BTC-USDT-SWAP
    """
    try:
        # 移除交易所前缀 (如 BINANCE:BTCUSDT -> BTCUSDT)
        if ':' in tv_symbol:
            tv_symbol = tv_symbol.split(':')[1]
        
        # 如果已经是OKX格式（包含-SWAP后缀），直接返回
        if '-SWAP' in tv_symbol or '-FUTURES' in tv_symbol:
            logger.info(f"交易对已是OKX格式: {tv_symbol}")
            return tv_symbol
        
        # 处理常见格式
        symbol_map = {
            'BTCUSDT': 'BTC-USDT-SWAP',
            'ETHUSDT': 'ETH-USDT-SWAP',
            'ADAUSDT': 'ADA-USDT-SWAP',
            'SOLUSDT': 'SOL-USDT-SWAP',
            'DOTUSDT': 'DOT-USDT-SWAP',
            'LINKUSDT': 'LINK-USDT-SWAP',
            'LTCUSDT': 'LTC-USDT-SWAP',
            'BCHUSDT': 'BCH-USDT-SWAP'
        }
        
        if tv_symbol in symbol_map:
            return symbol_map[tv_symbol]
        
        # 通用转换逻辑
        if tv_symbol.endswith('USDT'):
            base = tv_symbol[:-4]  # 移除USDT
            return f"{base}-USDT-SWAP"
        
        logger.warning(f"未知交易对格式: {tv_symbol}, 使用原格式")
        return tv_symbol
        
    except Exception as e:
        logger.error(f"交易对格式转换失败: {e}")
        return tv_symbol

def validate_trading_params(action, symbol, size, leverage):
    """
    验证交易参数
    """
    try:
        # 检查动作
        if action.lower() not in ['buy', 'sell']:
            logger.error(f"无效交易动作: {action}")
            return False
        
        # 检查交易对
        if not symbol:
            logger.error("交易对不能为空")
            return False
        
        # 检查仓位大小
        if size <= 0:
            logger.error(f"无效仓位大小: {size}")
            return False
        
        if size > Config.MAX_POSITION_SIZE:
            logger.error(f"仓位大小超过限制: {size} > {Config.MAX_POSITION_SIZE}")
            return False
        
        # 检查杠杆
        if leverage <= 0 or leverage > Config.MAX_LEVERAGE:
            logger.error(f"无效杠杆倍数: {leverage}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"参数验证异常: {e}")
        return False

def send_notification(message):
    """
    发送通知消息（可扩展到微信、邮件等）
    """
    try:
        logger.info(f"通知: {message}")
        
        # 这里可以添加其他通知方式
        # 例如: 微信、邮件、Telegram等
        
    except Exception as e:
        logger.error(f"发送通知失败: {e}")

@app.route('/positions', methods=['GET'])
def get_positions():
    """获取当前持仓信息"""
    try:
        positions = okx_trader.get_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"获取持仓信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/balance', methods=['GET'])
def get_balance():
    """获取账户余额"""
    try:
        balance = okx_trader.get_balance()
        return jsonify(balance)
    except Exception as e:
        logger.error(f"获取余额信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    try:
        return jsonify({
            'server_status': 'running',
            'okx_connection': okx_trader.check_connection(),
            'timestamp': datetime.now().isoformat(),
            'config': {
                'max_position_size': Config.MAX_POSITION_SIZE,
                'max_leverage': Config.MAX_LEVERAGE,
                'enable_trading': Config.ENABLE_TRADING
            }
        })
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 云平台端口适配：Render会提供PORT环境变量
    port = int(os.environ.get("PORT", Config.SERVER_PORT or 5000))
    
    print(f"🚀 TradingView Webhook服务器启动中...")
    print(f"📡 监听端口: {port}")
    print(f"🔗 Webhook URL: http://0.0.0.0:{port}/webhook")
    print(f"❤️  健康检查: http://0.0.0.0:{port}/health")
    print(f"📊 状态页面: http://0.0.0.0:{port}/status")
    
    # 启动Flask应用，适配云平台
    app.run(
        host='0.0.0.0',  # 云平台需要绑定所有接口
        port=port,
        debug=False,     # 生产环境关闭调试模式
        threaded=True    # 支持多线程处理
    )
