from mnemonic import Mnemonic
from bip32utils import BIP32Key
from eth_account import Account
import random


def generate_mnemonic() -> str:
    """生成12个单词的助记词"""
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128) # 128位强度对应12个单词
    #return 'fork street begin detect flame topple defense rebel annual balcony smart present'

def generate_password() -> str:
    """生成8位随机数字密码"""
    return str(random.randint(0, 99999999)).zfill(8)
    #return '83721421'

def recover_wallet(words: str, password: str):
    """根据助记词和密码恢复钱包并派生地址"""
    # 生成种子（助记词 + 密码）
    seed = Mnemonic.to_seed(words, passphrase=password)
    # 创建根密钥
    root_key = BIP32Key.fromEntropy(seed)

    for i in range(10):
        # 按 BIP44 路径派生密钥：m/44'/60'/0'/0/{i}
        child_key = (
            root_key.ChildKey(44 + 0x80000000)  # BIP44 用途层（硬化派生）
            .ChildKey(60 + 0x80000000)  # 以太坊的币种类型（60）
            .ChildKey(0 + 0x80000000)  # 账户索引（0）
            .ChildKey(0)  # 外部链（外部地址）
            .ChildKey(i)  # 地址索引
        )
        # 获取私钥和地址
        private_key = child_key.PrivateKey()
        address = Account.from_key(private_key).address
        print(f"地址 {i}: {address}")
        print(f"私钥 {i}: {private_key.hex()}\n")
        with open("wallet_backup2.txt", "a", encoding="utf-8") as f:
            f.write(f"地址 {i}: {address}\n私钥 {i}: {private_key.hex()}\n")


if __name__ == "__main__":
    # 1. 生成助记词和密码
    words = generate_mnemonic()
    password = generate_password()
    print(f"生成的助记词: {words}")
    print(f"生成的密码: {password}\n")

    # 2. 保存助记词和密码（实际使用最好是需加密存储，这里是测试用）
    with open("wallet_backup2.txt", "w",encoding="utf-8") as f:
        f.write(f"助记词: {words}\n密码: {password}\n")

    # 3. 恢复钱包并打印地址和私钥
    print("恢复的钱包地址和私钥：")
    recover_wallet(words, password)