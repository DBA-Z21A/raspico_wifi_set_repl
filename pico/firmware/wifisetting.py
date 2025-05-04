import ujson
import network
import machine
import hashlib
import os
from micropython import const
from ucryptolib import aes
import ubinascii

# AES ブロックサイズ (バイト)
_BLOCK_SIZE = const(16)

# 設定ファイル名
_SETTING_FILE_NAME = "wifi_config.json"


def rssi_to_stars(rssi):
    """
    RSSI（dBm）値を 0〜10 の星（*）に変換して文字列で返す
    """
    # dBm値は通常 -100〜-30 の範囲
    rssi_clamped = max(-100, min(-30, rssi))
    level = int((rssi_clamped + 100) / 7)
    return "_" * (10 - level) + "*" * level


def scanSSID():
    """
    接続可能なWiFiのSSIDを列挙
    """
    print("start Wi-Fi SSID scan...")

    # Wi-Fiステーションモードを有効にする
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.active():
        print("Wi-Fi activation failed!")
        return

    # Wi-Fiネットワークのスキャンを実行
    try:
        networkInfoList = wlan.scan()
        if networkInfoList:
            print("find Wi-Fi SSID Name and rssi:")
            for networkInfo in networkInfoList:
                ssid = networkInfo[0].decode("utf-8")
                rssi = networkInfo[3]
                rssiLevel = rssi_to_stars(rssi)
                print(f"{rssiLevel}/{ssid}")
        else:
            print("No Wi-Fi networks found.")
    except Exception as e:
        print("Wi-Fiスキャン失敗:", repr(e))

    # Wi-Fiを無効化
    wlan.active(False)
    print("disconnect Wi-Fi")


def generate_key():
    """machine.unique_id() を SHA256 でハッシュ化し、最初の 16 バイトをキーとして使用"""
    uid = machine.unique_id()
    hashed_uid = hashlib.sha256(uid).digest()
    return hashed_uid[:16]


def encrypt_password(password, key):
    """AES (CBC モード) を用いてパスワードを暗号化し、IV を先頭に付加"""
    iv = os.urandom(_BLOCK_SIZE)
    cipher = aes(key, 2, iv)
    padded_password = password.encode("utf-8")
    # パディング (PKCS#7)
    padding_len = _BLOCK_SIZE - len(padded_password) % _BLOCK_SIZE
    padded_password += bytes([padding_len] * padding_len)
    ciphertext = cipher.encrypt(padded_password)
    return ubinascii.b2a_base64(iv + ciphertext).decode().strip()


def decrypt_password(encrypted_b64, key):
    """Base64形式のIV付き暗号文を復号"""
    data = ubinascii.a2b_base64(encrypted_b64)
    iv = data[:_BLOCK_SIZE]
    ciphertext = data[_BLOCK_SIZE:]
    cipher = aes(key, 2, iv)
    padded_password = cipher.decrypt(ciphertext)
    padding_len = padded_password[-1]
    if padding_len > _BLOCK_SIZE or padding_len > len(padded_password):
        raise ValueError("Invalid padding")
    return padded_password[:-padding_len].decode("utf-8")


def save_wifi_config(json_string, filename=_SETTING_FILE_NAME):
    """
    引数で指定された文字列をJSONとして解釈し、パスワードを暗号化してからファイルに保存
    """
    try:
        wifi_config = ujson.loads(json_string)
        key = generate_key()
        if "wifi_password" in wifi_config and wifi_config["wifi_password"]:
            encrypted_password = encrypt_password(wifi_config["wifi_password"], key)
            wifi_config["wifi_password_encrypted"] = encrypted_password
            del wifi_config["wifi_password"]  # 元のパスワードを削除

        with open(filename, "w") as f:
            ujson.dump(wifi_config, f)
        print(f"WiFi configuration saved to '{filename}'.")
        return True, wifi_config
    except Exception as e:
        print(f"Error saving WiFi config: {e}")
        return False, None


def apply_wifi_config(filename=_SETTING_FILE_NAME):
    """
    ファイルに保存されたWiFi接続情報を用いてWiFiに接続
    """
    try:
        if not filename in os.listdir():
            print(f"Config file '{filename}' not found.")
            return

        config = ujson.loads(open(filename).read())
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            wlan.disconnect()
        print("Disconecct Wi-Fi...")
        wlan.active(True)

        ssid = config.get("wifi_ssid")
        encrypted_password = config.get("wifi_password_encrypted")
        use_static = config.get("use_static_ip", False)
        ip = config.get("static_ip")
        subnet = config.get("subnet_mask")
        gateway = config.get("gateway")
        dns = config.get("dns_server")

        password = None
        if encrypted_password:
            key = generate_key()
            try:
                password = decrypt_password(encrypted_password, key)
            except ValueError as e:
                print(f"Password decryption error: {e}")
                return

        if ssid and password is not None:
            if use_static:
                if ip and subnet and gateway and dns:
                    wlan.ifconfig((ip, subnet, gateway, dns))
                    print(
                        f"Using static IP: {ip}, GW: {gateway}, Subnet: {subnet}, DNS: {dns}"
                    )
                else:
                    print("Static IP configuration incomplete.")
            else:
                print("Using DHCP.")

            wlan.connect(ssid, password)
            print(f"connected {ssid}...")
        else:
            print("SSID or encrypted password not found in configuration.")
    except Exception as e:
        print(f"Error connectiong WiFi: {e}")


# テスト用コード
# Web Serial API から受信した JSON 文字列の例 (パスワードは暗号化前のもの)
# received_json_string = '{"wifi_ssid": "your_wifi_ssid", "wifi_password": "plain_password", "use_static_ip": true, "static_ip": "192.168.1.100", "subnet_mask": "255.255.255.0", "gateway": "192.168.1.1", "dns_server": "192.168.1.1"}'

# success, config_data = save_wifi_config(received_json_string)
# if success and config_data:
#    apply_wifi_config()
#    wlan = network.WLAN(network.STA_IF)
#    wlan.active(False)
#    print("Disconnect Wi-Fi...")
