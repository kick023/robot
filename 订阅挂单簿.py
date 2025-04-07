import asyncio
import json
import websockets


async def binance_order_book():
    # 订阅SOL-USDT现货的挂单簿深度更新流，每100毫秒更新一次
    stream_name = "solusdt@depth@100ms"
    uri = f"wss://stream.binance.com:9443/stream?streams={stream_name}"

    async with websockets.connect(uri) as websocket:
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                # 提取挂单簿数据
                if 'data' in data:
                    order_book = data['data']
                    print(f"事件类型: {order_book.get('e')}")
                    print(f"交易对: {order_book.get('s')}")
                    print(f"更新时间: {order_book.get('E')}")
                    print("买单更新 (Bids):")
                    for bid in order_book.get('b', []):
                        print(f"  价格: {bid[0]}, 数量: {bid[1]}")
                    print("卖单更新 (Asks):")
                    for ask in order_book.get('a', []):
                        print(f"  价格: {ask[0]}, 数量: {ask[1]}")
                    print(f"最后更新ID: {order_book.get('u')}")
                    print("-" * 50)
                else:
                    print("收到未知数据格式:", data)
        except websockets.exceptions.ConnectionClosed:
            print("连接中断，尝试重新连接...")
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(binance_order_book())