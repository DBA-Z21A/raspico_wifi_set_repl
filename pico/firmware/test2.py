import ujson
import network


def rssi_to_stars(rssi):
    """
    RSSI（dBm）値を 0〜10 の星（*）に変換して文字列で返す
    """
    # dBm値は通常 -100〜-30 の範囲
    rssi_clamped = max(-100, min(-30, rssi))
    level = int((rssi_clamped + 100) / 7)
    return "_" * (10 - level) + "*" * level


def scanSSID():
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
                bssid = ":".join("{:02X}".format(b) for b in networkInfo[1])
                print(f"{rssiLevel}/{ssid}(BSSID: {bssid})")
        else:
            print("No Wi-Fi networks found.")
    except Exception as e:
        print("Wi-Fiスキャン失敗:", repr(e))

    # Wi-Fiを無効化
    wlan.active(False)
    print("disconnect Wi-Fi")


def save_wifi_config(json_string, filename="wifi_config.json"):
    try:
        wifi_config = ujson.loads(json_string)
        with open(filename, "w") as file:
            ujson.dump(wifi_config, file)
        print(f"WiFi configuration saved to '{filename}'.")
        return True, wifi_config
    except Exception as e:
        print(f"Error saving WiFi config: {e}")
        return False, None


# テスト用
# scanSSID()
