from machine import Pin
import time

sw = Pin(16, Pin.IN, Pin.PULL_UP)
beep = Pin(28, Pin.OUT)
led = Pin("LED", Pin.OUT)

while True:
    if sw.value() == 0:
        print("ボタンが押されました!")
        led.on()
        beep.on()
    else:
        led.off()
        beep.off()
    time.sleep(0.1)
