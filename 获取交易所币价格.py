import requests

def get_binance_prices():
    """获取币安交易所买一卖一价格"""
    try:
        url = "https://api.binance.com/api/v3/ticker/bookTicker?symbol=SOLUSDT"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return float(data['bidPrice']), float(data['askPrice'])
    except Exception as e:
        print(f"币安价格获取失败: {e}")
        return None, None

def get_okx_prices():
    """获取OKX交易所买一卖一价格"""
    try:
        url = "https://www.okx.com/api/v5/market/books?instId=SOL-USDT&sz=1"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['code'] == "0":
            bid = float(data['data'][0]['bids'][0][0])
            ask = float(data['data'][0]['asks'][0][0])
            return bid, ask
        print(f"OKX API错误: {data.get('msg')}")
        return None, None
    except Exception as e:
        print(f"OKX价格获取失败: {e}")
        return None, None

def get_binance_orderbook():
    """获取币安交易所前10档挂单"""
    try:
        url = "https://api.binance.com/api/v3/depth?symbol=SOLUSDT&limit=10"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        bids = [[float(p), float(q)] for p, q in data['bids']]
        asks = [[float(p), float(q)] for p, q in data['asks']]
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