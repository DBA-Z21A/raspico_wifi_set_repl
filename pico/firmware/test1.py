from machine import Pin
import time
import rp2

sw = Pin(21, Pin.IN, Pin.PULL_UP)
beep = Pin(28, Pin.OUT)
led = Pin("LED", Pin.OUT)

while True:
    if rp2.bootsel_button() == 1:
        print("ボタンが押されました!")
        led.on()
        beep.on()
    else:
        led.off()
        beep.off()
    time.sleep(0.1)
