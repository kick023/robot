import time
import json
from binance.spot import Spot

# 配置信息
API_KEY = ''
SECRET_KEY = ''
BASE_URL = 'https://testnet.binance.vision'

# 初始化客户端
client = Spot(api_key=API_KEY, api_secret=SECRET_KEY, base_url=BASE_URL)

def get_balance():
    """获取账户余额"""
    try:
        account_info = client.account()
        balances = {asset['asset']: asset for asset in account_info['balances']}
        btc = balances.get('BTC', {'free': '0.00000000'})
        usdt = balances.get('USDT', {'free': '0.00000000'})
        print(f"\n当前余额:\nBTC 可用: {btc['free']}\nUSDT 可用: {usdt['free']}")
        return balances
    except Exception as e:
        print(f"获取余额失败: {str(e)}")
        return {}

def create_order(symbol, side, quantity, custom_id):
    """创建市价订单"""
    try:
        if side == 'BUY':
            order = client.new_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quoteOrderQty=quantity,
                newClientOrderId=custom_id
            )

        else:
            order = client.new_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                newClientOrderId=custom_id
            )
        print(f"\n创建{side}单成功:\n{json.dumps(order, indent=2, ensure_ascii=False)}")
        return order
    except Exception as e:
        print(f"创建订单失败: {str(e)}")
        return {}

def get_order(symbol, order_id):
    """查询订单详情"""
    try:
        order = client.get_order(symbol=symbol, origClientOrderId=order_id)
        print(f"\n订单详情:\n{json.dumps(order, indent=2, ensure_ascii=False)}")
        return order
    except Exception as e:
        print(f"查询订单失败: {str(e)}")
        return {}

def print_order_details(order):
    """打印订单详细信息"""
    print(f"\n订单ID: {order.get('clientOrderId', '未知')}")
    print(f"方向: {'买入' if order.get('side') == 'BUY' else '卖出'}")
    timestamp = order.get('updateTime', order.get('transactTime', 0)) // 1000
    print(f"完成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
    executed_qty = float(order.get('executedQty', 0))
    cum_quote = float(order.get('cummulativeQuoteQty', 0))
    avg_price = cum_quote / executed_qty if executed_qty > 0 else 0
    print(f"成交均价: {avg_price:.2f} USDT")
    print(f"成交数量: {executed_qty:.8f} BTC")
    # 手续费信息可能需要通过交易记录获取

def main():
    try:
        print("=== 初始余额 ===")
        get_balance()

        # 创建市价买单
        buy_custom_id = f"BUY_{int(time.time() * 1000)}"
        print("\n=== 创建买单 ===")
        buy_order = create_order('BTCUSDT', 'BUY', '100', buy_custom_id)
        if 'orderId' in buy_order:
            print("\n=== 买单详情 ===")
            buy_details = get_order('BTCUSDT', buy_custom_id)
            print_order_details(buy_details)

        print("\n=== 买后余额 ===")
        get_balance()

        # 创建市价卖单
        sell_custom_id = f"SELL_{int(time.time() * 1000)}"
        print("\n=== 创建卖单 ===")
        sell_order = create_order('BTCUSDT', 'SELL', '0.001', sell_custom_id)
        if 'orderId' in sell_order:
            print("\n=== 卖单详情 ===")
            sell_details = get_order('BTCUSDT', sell_custom_id)
            print_order_details(sell_details)

        print("\n=== 最终余额 ===")
        get_balance()
    except Exception as e:
        print(f"\n操作异常: {str(e)}")

if __name__ == '__main__':
    main()