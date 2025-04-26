import ujson
import network
import machine
import hashlib
import os
import sys
from micropython import const
from ucryptolib import aes

# AES ブロックサイズ (バイト)
_BLOCK_SIZE = const(16)


def scanSSID():
    # Wi-Fiステーションモードを有効にする
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Wi-Fiネットワークのスキャンを実行
    networks = wlan.scan()

    # スキャン結果を表示
    for network in networks:
        ssid = network[0].decode("utf-8")  # SSIDをデコードして文字列として取得
        print(ssid)  # REPL上にSSIDを表示

    # Wi-Fi接続を切断
    wlan.active(False)  # Wi-Fiを無効にする
    print("Wi-Fiを切断しました")


def generate_key():
    """machine.unique_id() を SHA256 でハッシュ化し、最初の 16 バイトをキーとして使用"""
    uid = machine.unique_id()
    hashed_uid = hashlib.sha256(uid).digest()
    return hashed_uid[:16]


def encrypt_password(password, key):
    """AES (CBC モード) を用いてパスワードを暗号化し、IV を先頭に付加"""
    cipher = aes(key, 1)
    iv = os.urandom(_BLOCK_SIZE)
    cipher = aes(key, 2, iv)
    padded_password = password.encode("utf-8")
    # パディング (PKCS#7)
    padding_len = _BLOCK_SIZE - len(padded_password) % _BLOCK_SIZE
    padded_password += bytes([padding_len] * padding_len)
    ciphertext = cipher.encrypt(padded_password)
    return iv + ciphertext.hex()


def decrypt_password(encrypted_hex, key):
    """先頭の IV を取り除き、AES (CBC モード) を用いてパスワードを復号"""
    iv = bytes.fromhex(encrypted_hex[: _BLOCK_SIZE * 2])
    ciphertext = bytes.fromhex(encrypted_hex[_BLOCK_SIZE * 2 :])
    cipher = aes(key, 2, iv)  # MODE_CBC を使用
    padded_password = cipher.decrypt(ciphertext)
    # パディング解除 (PKCS#7)
    padding_len = padded_password[-1]
    if padding_len > _BLOCK_SIZE or padding_len > len(padded_password):
        raise ValueError("Invalid padding")
    password = padded_password[:-padding_len].decode("utf-8")
    return password


def save_wifi_config(json_string, filename="wifi_config.json"):
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


def apply_wifi_config(config):

    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    print("現在のWi-Fi接続を切断しました")
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
            wlan.ifconfig("dhcp")
            print("Using DHCP.")

        wlan.connect(ssid, password)
        print(f"Connecting to {ssid}...")
        # 接続状態を監視する処理などを追加
    else:
        print("SSID or encrypted password not found in configuration.")


# Web Serial API から受信した JSON 文字列の例 (パスワードは暗号化前のもの)
received_json_string = '{"wifi_ssid": "your_wifi_ssid", "wifi_password": "plain_password", "use_static_ip": true, "static_ip": "192.168.1.100", "subnet_mask": "255.255.255.0", "gateway": "192.168.1.1", "dns_server": "192.168.1.1"}'

success, config_data = save_wifi_config(received_json_string)
if success and config_data:
    apply_wifi_config(config_data)
