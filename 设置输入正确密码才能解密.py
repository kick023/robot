from cryptography.fernet import Fernet
from hashlib import sha256
import base64

# 将提供的密码转换为符合要求的fernet 32字节密钥
def generate_fernet_key(password):
    # 将密钥编码为字节
    password_bytes = password.encode('utf-8')

    # 使用SHA-256哈希函数生成32字节的摘要
    hash_bytes = sha256(password_bytes).digest()

    # 将哈希值转换为Base64编码的32字节密钥
    fernet_key = base64.urlsafe_b64encode(hash_bytes)
    return fernet_key


# 加密函数
def encrypt(text, key):
    cipher = Fernet(key)
    encrypted = cipher.encrypt(text.encode('utf-8'))
    return encrypted


# 解密函数
def decrypt(encrypted, key):
    cipher = Fernet(key)
    decrypted = cipher.decrypt(encrypted).decode('utf-8')
    return decrypted

#设置密码
def set_password():
    #设置一个固定的密码（灵活）
    return "666qwertyuiop666"

#验证输入的密码
def verify_password(input_password,true_password):
    return input_password == true_password

#主程序
def main():
    #设置正确的密码
    true_password = set_password()

    #最大尝试次数
    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        #输入密码
        enter_password = input("请输入正确密码解密：")

        #验证密码是否正确
        if verify_password(enter_password,true_password):
            #密码正确就继续解密
            text = "From the sea to the boundless sky, I am the shore; from the mountain to the summit, I am the peak"

            #生成密钥
            key = generate_fernet_key(true_password)

            # 加密
            encrypted = encrypt(text, key)
            print("Encrypted:", encrypted)

            # 解密
            decrypted = decrypt(encrypted, key)
            print("Decrypted:", decrypted)

            # 对比前后原始文本和解密后的

            if text == decrypted:
                print("密码正确，通过")
            else:
                print("密码错误，解析失败")
            return #退出主程序
        else:
            print("密码错误，重试")
            attempts += 1

    #如果超过最大次数
    print("密码错误次数过多，退出程序")

#运行主程序
if __name__ == "__main__":
    main()