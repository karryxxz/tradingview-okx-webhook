#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX交易模块 - 处理合约交易操作

功能特点：
1. 支持开多/开空仓位
2. 自动设置止损止盈
3. 仓位管理和风险控制
4. 完整的错误处理和日志记录

安全提示：
- 请确保API权限设置正确（只开启合约交易权限）
- 建议先在测试环境验证功能
- 使用前请仔细检查所有参数设置
"""

import okx.Account as Account
import okx.Trade as Trade
import okx.MarketData as MarketData
import json
import time
import logging
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class OKXTrader:
    """OKX合约交易器"""
    
    def __init__(self):
        """初始化OKX交易接口"""
        try:
            # 根据配置决定使用正式环境还是测试环境
            self.flag = "1" if Config.OKX_SANDBOX else "0"  # "0": 正式环境, "1": 测试环境
            
            logger.info(f"初始化OKX交易接口，环境: {'测试环境' if self.flag == '1' else '正式环境'}")
            
            # 初始化各个API接口 - 使用正确的SDK用法
            self.account_api = Account.AccountAPI(
                api_key=Config.OKX_API_KEY,
                api_secret_key=Config.OKX_SECRET_KEY,  # 注意这里使用正确的参数名
                passphrase=Config.OKX_PASSPHRASE,
                use_server_time=False,
                flag=self.flag
            )
            
            self.trade_api = Trade.TradeAPI(
                api_key=Config.OKX_API_KEY,
                api_secret_key=Config.OKX_SECRET_KEY,  # 注意这里使用正确的参数名
                passphrase=Config.OKX_PASSPHRASE,
                use_server_time=False,
                flag=self.flag
            )
            
            # MarketData不需要认证
            self.market_api = MarketData.MarketAPI(flag=self.flag)
            
            # 交易状态跟踪
            self.daily_trade_count = 0
            self.last_trade_date = None
            
            logger.info("OKX交易接口初始化成功")
            
        except Exception as e:
            logger.error(f"初始化OKX交易接口失败: {e}")
            raise
    
    def check_connection(self):
        """检查API连接状态"""
        try:
            logger.info("开始测试OKX API连接...")
            logger.info(f"使用环境: {'测试环境' if self.flag == '1' else '正式环境'}")
            logger.info(f"API Key前4位: {Config.OKX_API_KEY[:4]}****")
            
            # 使用正确的方法名 - 测试市场数据获取
            result = self.market_api.get_tickers(instType="SPOT")
            logger.info(f"API响应: {result}")
            
            if result.get('code') == '0':
                logger.info("OKX API连接正常")
                return True
            else:
                logger.error(f"OKX API连接异常: {result}")
                return False
        except Exception as e:
            logger.error(f"检查OKX连接失败: {e}")
            logger.error(f"异常类型: {type(e)}")
            logger.error(f"异常详情: {str(e)}")
            return False
    
    def get_balance(self):
        """获取账户余额"""
        try:
            # 使用正确的方法名
            result = self.account_api.get_account_balance()
            if result.get('code') == '0':
                logger.info("获取余额成功")
                return {
                    'success': True,
                    'data': result.get('data', [])
                }
            else:
                logger.error(f"获取余额失败: {result}")
                return {
                    'success': False,
                    'error': result.get('msg', '获取余额失败')
                }
        except Exception as e:
            logger.error(f"获取余额异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_positions(self):
        """获取当前持仓"""
        try:
            logger.info("正在获取持仓信息...")
            logger.info(f"使用API环境: {'测试环境' if self.flag == '1' else '正式环境'}")
            
            result = self.account_api.get_positions()
            logger.info(f"持仓API原始响应: {result}")
            logger.info(f"响应类型: {type(result)}")
            
            if result.get('code') == '0':
                logger.info("获取持仓成功")
                return {
                    'success': True,
                    'data': result.get('data', [])
                }
            else:
                logger.error(f"获取持仓失败，错误代码: {result.get('code')}")
                logger.error(f"错误信息: {result.get('msg')}")
                return {
                    'success': False,
                    'error': result.get('msg', '获取持仓失败')
                }
        except Exception as e:
            logger.error(f"获取持仓异常: {e}")
            logger.error(f"异常类型: {type(e)}")
            logger.error(f"异常详情: {str(e)}")
            # 如果是JSON解析错误，可能收到的是HTML响应
            if "Expecting value" in str(e):
                logger.error("可能收到非JSON响应，疑似API认证失败")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_market_price(self, symbol):
        """获取市场价格"""
        try:
            result = self.market_api.get_ticker(instId=symbol)
            if result.get('code') == '0' and result.get('data'):
                price = float(result['data'][0]['last'])
                return {
                    'success': True,
                    'price': price
                }
            else:
                return {
                    'success': False,
                    'error': '获取价格失败'
                }
        except Exception as e:
            logger.error(f"获取市场价格异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_leverage(self, symbol, leverage):
        """设置杠杆倍数"""
        try:
            logger.info(f"设置杠杆 {symbol}: {leverage}x")
            
            # 使用正确的方法名
            result = self.account_api.set_leverage(
                instId=symbol,
                lever=str(leverage),
                mgnMode="cross"  # 全仓模式
            )
            
            if result.get('code') == '0':
                logger.info(f"设置杠杆成功: {leverage}x")
                return {'success': True}
            else:
                logger.error(f"设置杠杆失败: {result}")
                return {
                    'success': False,
                    'error': result.get('msg', '设置杠杆失败')
                }
        except Exception as e:
            logger.error(f"设置杠杆异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def place_order(self, symbol, side, amount, order_type='market', price=None):
        """下单"""
        try:
            logger.info(f"准备下单: {symbol} {side} {amount}")
            
            # 使用正确的方法名
            result = self.trade_api.place_order(
                instId=symbol,
                tdMode="cross",  # 全仓模式
                side=side,  # buy 或 sell
                ordType=order_type,  # market 或 limit
                sz=str(amount),
                px=str(price) if price else None
            )
            
            if result.get('code') == '0':
                order_id = result['data'][0]['ordId']
                logger.info(f"下单成功，订单ID: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'data': result['data'][0]
                }
            else:
                logger.error(f"下单失败: {result}")
                return {
                    'success': False,
                    'error': result.get('msg', '下单失败')
                }
        except Exception as e:
            logger.error(f"下单异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def close_position(self, symbol, side):
        """平仓"""
        try:
            logger.info(f"准备平仓: {symbol} {side}")
            
            # 获取持仓信息
            positions = self.get_positions()
            if not positions['success']:
                return positions
            
            target_position = None
            for pos in positions['data']:
                if pos['instId'] == symbol and pos['posSide'] == side:
                    target_position = pos
                    break
            
            if not target_position:
                logger.info("没有找到需要平仓的持仓")
                return {'success': True, 'message': '无持仓需要平仓'}
            
            pos_size = abs(float(target_position['pos']))
            close_side = 'sell' if side == 'long' else 'buy'
            
            # 使用正确的方法名
            result = self.trade_api.place_order(
                instId=symbol,
                tdMode="cross",
                side=close_side,
                ordType="market",
                sz=str(pos_size),
                reduceOnly=True  # 只减仓
            )
            
            if result.get('code') == '0':
                logger.info("平仓成功")
                return {
                    'success': True,
                    'order_id': result['data'][0]['ordId']
                }
            else:
                logger.error(f"平仓失败: {result}")
                return {
                    'success': False,
                    'error': result.get('msg', '平仓失败')
                }
                
        except Exception as e:
            logger.error(f"平仓异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def place_stop_order(self, symbol, side, size, trigger_price, order_price=None):
        """下止损止盈单"""
        try:
            logger.info(f"设置止损单: {symbol} {side} {size} @ {trigger_price}")
            
            # 使用正确的方法名
            result = self.trade_api.place_algo_order(
                instId=symbol,
                tdMode="cross",
                side=side,
                ordType="conditional",  # 条件单
                sz=str(size),
                triggerPx=str(trigger_price),
                orderPx=str(order_price) if order_price else str(trigger_price)
            )
            
            if result.get('code') == '0':
                logger.info("止损单设置成功")
                return {
                    'success': True,
                    'order_id': result['data'][0]['algoId']
                }
            else:
                logger.error(f"止损单设置失败: {result}")
                return {
                    'success': False,
                    'error': result.get('msg', '止损单设置失败')
                }
        except Exception as e:
            logger.error(f"止损单设置异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def open_long_position(self, symbol, size, leverage=10, stop_loss=None, take_profit=None):
        """开多仓"""
        try:
            logger.info(f"准备开多仓: {symbol}, 数量: {size}, 杠杆: {leverage}x")
            
            # 风险检查
            risk_check = self._risk_check(symbol, size, leverage)
            if not risk_check['success']:
                return risk_check
            
            # 平掉现有仓位
            close_result = self.close_position(symbol, 'long')
            if not close_result['success']:
                logger.warning(f"平仓失败，继续开仓: {close_result}")
            
            # 设置杠杆
            leverage_result = self.set_leverage(symbol, leverage)
            if not leverage_result['success']:
                logger.warning(f"设置杠杆失败: {leverage_result}")
            
            # 开多仓
            order_result = self.place_order(
                symbol=symbol,
                side="buy",
                amount=size,
                order_type="market"
            )
            
            if not order_result['success']:
                return order_result
            
            # 设置止损止盈
            sl_tp_results = []
            
            if stop_loss and stop_loss > 0:
                sl_result = self.place_stop_order(
                    symbol=symbol,
                    side="sell",
                    size=size,
                    trigger_price=stop_loss
                )
                sl_tp_results.append(('止损', sl_result))
            
            if take_profit and take_profit > 0:
                tp_result = self.place_stop_order(
                    symbol=symbol,
                    side="sell",
                    size=size,
                    trigger_price=take_profit
                )
                sl_tp_results.append(('止盈', tp_result))
            
            return {
                'success': True,
                'action': 'open_long',
                'symbol': symbol,
                'size': size,
                'leverage': leverage,
                'order_id': order_result['order_id'],
                'stop_loss_take_profit': sl_tp_results,
                'message': f'开多仓成功: {size} {symbol}'
            }
            
        except Exception as e:
            logger.error(f"开多仓异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def open_short_position(self, symbol, size, leverage=10, stop_loss=None, take_profit=None):
        """开空仓"""
        try:
            logger.info(f"准备开空仓: {symbol}, 数量: {size}, 杠杆: {leverage}x")
            
            # 风险检查
            risk_check = self._risk_check(symbol, size, leverage)
            if not risk_check['success']:
                return risk_check
            
            # 平掉现有仓位
            close_result = self.close_position(symbol, 'short')
            if not close_result['success']:
                logger.warning(f"平仓失败，继续开仓: {close_result}")
            
            # 设置杠杆
            leverage_result = self.set_leverage(symbol, leverage)
            if not leverage_result['success']:
                logger.warning(f"设置杠杆失败: {leverage_result}")
            
            # 开空仓
            order_result = self.place_order(
                symbol=symbol,
                side="sell",
                amount=size,
                order_type="market"
            )
            
            if not order_result['success']:
                return order_result
            
            # 设置止损止盈
            sl_tp_results = []
            
            if stop_loss and stop_loss > 0:
                sl_result = self.place_stop_order(
                    symbol=symbol,
                    side="buy",
                    size=size,
                    trigger_price=stop_loss
                )
                sl_tp_results.append(('止损', sl_result))
            
            if take_profit and take_profit > 0:
                tp_result = self.place_stop_order(
                    symbol=symbol,
                    side="buy",
                    size=size,
                    trigger_price=take_profit
                )
                sl_tp_results.append(('止盈', tp_result))
            
            return {
                'success': True,
                'action': 'open_short',
                'symbol': symbol,
                'size': size,
                'leverage': leverage,
                'order_id': order_result['order_id'],
                'stop_loss_take_profit': sl_tp_results,
                'message': f'开空仓成功: {size} {symbol}'
            }
            
        except Exception as e:
            logger.error(f"开空仓异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _risk_check(self, symbol, size, leverage):
        """风险检查"""
        try:
            # 检查交易对
            if symbol not in Config.SUPPORTED_SYMBOLS:
                return {
                    'success': False,
                    'error': f'不支持的交易对: {symbol}'
                }
            
            # 检查仓位大小
            if size > Config.MAX_POSITION_SIZE:
                return {
                    'success': False,
                    'error': f'仓位超过限制: {size} > {Config.MAX_POSITION_SIZE}'
                }
            
            # 检查杠杆
            if leverage > Config.MAX_LEVERAGE:
                return {
                    'success': False,
                    'error': f'杠杆超过限制: {leverage} > {Config.MAX_LEVERAGE}'
                }
            
            # 检查日交易次数
            if self._check_daily_trade_limit():
                return {
                    'success': False,
                    'error': f'今日交易次数已达上限: {Config.MAX_DAILY_TRADES}'
                }
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"风险检查异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_daily_trade_limit(self):
        """检查日交易次数限制"""
        today = datetime.now().date()
        
        if self.last_trade_date != today:
            self.daily_trade_count = 0
            self.last_trade_date = today
        
        return self.daily_trade_count >= Config.MAX_DAILY_TRADES
    
    def _update_trade_count(self):
        """更新交易计数"""
        today = datetime.now().date()
        
        if self.last_trade_date != today:
            self.daily_trade_count = 1
            self.last_trade_date = today
        else:
            self.daily_trade_count += 1
        
        logger.info(f"今日交易次数: {self.daily_trade_count}/{Config.MAX_DAILY_TRADES}")

# 测试函数
if __name__ == '__main__':
    trader = OKXTrader()
    
    # 测试连接
    if trader.check_connection():
        print("✅ OKX连接测试通过")
        
        # 获取余额
        balance = trader.get_balance()
        print(f"账户余额: {balance}")
        
        # 获取持仓
        positions = trader.get_positions()
        print(f"当前持仓: {positions}")
    else:
        print("❌ OKX连接测试失败")
