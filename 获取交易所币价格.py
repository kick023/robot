from binance.client import Client as BinanceClient
from okx.MarketData import MarketAPI

# 初始化客户端
binance_client = BinanceClient()
okx_client = MarketAPI(
    flag="0",        # 实盘模式
    domain="https://www.okx.com",
    # 即使不需要交易功能，SDK页要求传入占位密钥
    api_key="",      # 留空
    api_secret_key="",  # 留空
    passphrase=""
)

def get_binance_prices():
    """使用币安官方SDK获取价格"""
    try:
        ticker = binance_client.get_orderbook_ticker(symbol='SOLUSDT')
        return float(ticker['bidPrice']), float(ticker['askPrice'])
    except Exception as e:
        print(f"币安价格获取失败: {e}")
        return None, None

def get_okx_prices():
    """使用OKX官方SDK获取价格"""
    try:
        response = okx_client.get_orderbook(instId="SOL-USDT", sz=1)
        if response["code"] == "0":
            # 数据结构验证
            bids = response["data"][0]["bids"]
            asks = response["data"][0]["asks"]
            if len(bids) > 0 and len(asks) > 0:
                return float(bids[0][0]), float(asks[0][0])
            else:
                print("OKX订单簿数据为空")
                return None, None
        else:
            print(f"OKX API错误: {response['msg']} (错误码: {response['code']})")
            return None, None
    except Exception as e:
        print(f"OKX价格获取失败: {str(e)}")
        return None, None

def get_binance_orderbook():
    """获取币安挂单数据"""
    try:
        depth = binance_client.get_order_book(symbol='SOLUSDT', limit=10)
        bids = [[float(p), float(q)] for p, q in depth['bids']]
        asks = [[float(p), float(q)] for p, q in depth['asks']]
        return bids, asks
    except Exception as e:
        print(f"币安挂单获取失败: {e}")
        return None, None

def main(threshold=0.5):
    # 获取价格数据
    b_bid, b_ask = get_binance_prices()
    o_bid, o_ask = get_okx_prices()

    if None in (b_bid, b_ask, o_bid, o_ask):
        return

    # 计算并打印差价
    bid_diff = b_bid - o_bid
    ask_diff = b_ask - o_ask
    print(f"买一差价:币安({b_bid:.4f}) - OKX({o_bid:.4f}) = {bid_diff:.4f}")
    print(f"卖一差价:币安({b_ask:.4f}) - OKX({o_ask:.4f}) = {ask_diff:.4f}")

    # 判断阈值
    if abs(bid_diff) > threshold or abs(ask_diff) > threshold:
        print(f"\n !!!检测到超过 {threshold} USDT 的差价！")
    else:
        print(f"\n ---差价均在 {threshold} USDT 以内")

    # 获取并打印币安挂单
    bids, asks = get_binance_orderbook()
    if bids and asks:
        print("\n---币安买单前10档")
        for price, qty in bids[:10]:
            print(f"价格: {price:<8} 数量: {qty:.2f}")

        print("\n---币安卖单前10档")
        for price, qty in asks[:10]:
            print(f"价格: {price:<8} 数量: {qty:.2f}")

if __name__ == "__main__":
    # 设置差价阈值，具体多少看具体需求(USDT)
    PRICE_THRESHOLD = 1
    main(PRICE_THRESHOLD)