import wifisetting
import time
import rp2
import os
import sys
import ntptime
import machine
import urequests
import network


# 末尾に追加（もしくは別ファイルへ共通化）
def debounce(delay=0.1):
    start = time.ticks_ms()
    while rp2.bootsel_button():
        if time.ticks_diff(time.ticks_ms(), start) > delay * 1000:
            return True
    return False


beep = machine.Pin(28, machine.Pin.OUT)
led = machine.Pin("LED", machine.Pin.OUT)
filename = wifisetting._SETTING_FILE_NAME
url = "http://example.com"

# WiFi接続設定が存在しない場合は終了
if not filename in os.listdir():
    print(f"Config file '{filename}' not found.")
    for i in range(10):
        beep.toggle()
        time.sleep(0.125)
    beep.off()
    raise SystemExit()

# 既にWiFi接続されていた場合は5秒間待機
wlan = network.WLAN(network.STA_IF)
if wlan.isconnected():
    wlan.disconnect()
    for i in range(20):
        time.sleep(0.25)
        led.toggle()

# 設定ファイルを用いてWiFi接続
if wifisetting.apply_wifi_config() == False:
    print("WiFi connected fail.")
    for i in range(5):
        beep.on()
        time.sleep(0.5)
        beep.off()
    raise SystemExit()


# NTPサーバに接続し内部時計を同期。ただしUTCである事に注意
try:
    time.sleep(1)
    ntptime.host = "ntp.nict.jp"
    ntptime.settime()
    print("datetime set from NTP")
except Exception as e:
    print("Error:", e)


led.on()
reset_entry_timestamps = []
now_waiting_reset = False
waiting_reset_start_time = -1
last_http_access_time = -1
reset_confirm_timestamps = []

while True:

    if now_waiting_reset:
        led.off()
        time.sleep(0.25)
        led.on()

    # ボタンが押されたら現在の時刻を記録（秒単位のUNIX時間）
    if rp2.bootsel_button() == 1:
        if debounce():
            if now_waiting_reset:
                reset_confirm_timestamps.append(time.time())
                beep.on()
                time.sleep(0.25)
                beep.off()
                print(f"to reset for {len(reset_confirm_timestamps)}")
            else:
                reset_entry_timestamps.append(time.time())

    # 5秒以上経過したデータをリストから削除
    current_time = time.time()
    reset_entry_timestamps = [
        t for t in reset_entry_timestamps if current_time - t <= 5
    ]
    reset_confirm_timestamps = [
        t for t in reset_confirm_timestamps if current_time - t <= 5
    ]

    # 通常状態で5秒間に三回ボタンが押されたらリセット待機状態に移行
    if len(reset_entry_timestamps) >= 5:
        waiting_reset_start_time = current_time
        reset_entry_timestamps = []
        now_waiting_reset = True
        beep.on()
        time.sleep(0.25)
        beep.off()

    if now_waiting_reset:

        # リセット待機状態で再度三回ボタンが押されたら、設定ファイルを削除して再起動
        if len(reset_confirm_timestamps) >= 3:
            beep.on()
            time.sleep(0.5)
            beep.off()
            time.sleep(0.5)
            beep.on()
            time.sleep(2)
            beep.off()
            os.remove(filename)
            machine.reset()

        # リセット待機状態から10秒間操作がなければ待機状態をクリア
        if (current_time - waiting_reset_start_time >= 10) and (
            len(reset_confirm_timestamps) == 0
        ):
            now_waiting_reset = False
            reset_confirm_timestamps = []
            print("clear waiting_reset_mode...")

    # 一分ごとにHTTPへアクセス
    # ※本来Raspberry Pi Pico Wに実行させたいロジックはここに記述する
    if last_http_access_time < (current_time - 60):
        try:
            last_http_access_time = current_time
            year, month, day, hour, minute, second, _, _ = time.localtime(
                time.time() + (9 * 60 * 60)
            )
            print(
                f"try access for {url}: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} (JST)"
            )
            response = urequests.get(url, timeout=5)
            print("Response Status:", response.status_code)
            print("Response Content:", response.text)
            response.close()
        except Exception as e:
            print("Error:", e)

    time.sleep(0.1)
