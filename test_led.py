import neopixel
from machine import Pin
import time

n = 1
p = 16

np = neopixel.NeoPixel(Pin(p), n)

while True:    
    np[0] = (64, 0, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(1)

    np[0] = (0, 64, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 64, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(1)

    np[0] = (0, 0, 64)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 64)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 64)
    np.write()
    time.sleep(0.25)
    np[0] = (0, 0, 0)
    np.write()
    time.sleep(1)
