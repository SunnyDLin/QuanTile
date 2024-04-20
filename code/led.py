import neopixel
from machine import Pin
from mpy_enum import Enum


class LED:
    # Some development boards have an LED with red and green components reversed.
    # This is a hack to fix the problem.  I wired Pin 29 to 3.3v source to
    # identify boards with the wrong color assignment.
    colorSwitchPin = Pin(29, Pin.IN)
    if colorSwitchPin.value() == 0:      # correct color assignment
        Color = Enum(
            RED        = (255,  16,  16),
            GREEN      = ( 64, 255,  64),
            BLUE       = ( 64,  64, 255),
            DIM_YELLOW = ( 16,  16,   0),
            BLACK      = (  0,   0,   0)
            )
    else:                      # RED-GREEN reversed color assignment
        Color = Enum(
            RED        = ( 16, 255,  16),
            GREEN      = (255,  64,  64),
            BLUE       = ( 64,  64, 255),
            DIM_YELLOW = ( 16,  16,   0),
            BLACK      = (  0,   0,   0)
            )

    led = neopixel.NeoPixel(Pin(16), 1)
    color = Color.BLACK
    
    def __init__(self, color=Color.BLACK, on=True):
        self.color = color
        self.led[0] = color.value
        if on:
            self.led.write()    
    
    def setColor(self, color, on=True):
        self.color = color
        self.led[0] = color.value
        if on:
            self.led.write()    

    def getColor(self):
        return self.color
    
    def turnOn(self):
        self.led[0] = self.color.value
        self.led.write()    
        
    def turnOff(self):
        self.led[0] = LED.Color.BLACK.value
        self.led.write()    

if __name__ == '__main__':
    import time
    led = LED()
    while True:
        for i in range(1):
            led.setColor(LED.Color.RED)
            time.sleep(0.25)
            led.turnOff()
            time.sleep(0.25)
        time.sleep(0.5)
        for i in range(2):
            led.setColor(LED.Color.GREEN)
            time.sleep(0.25)
            led.turnOff()
            time.sleep(0.25)
        time.sleep(0.5)
        for i in range(3):
            led.setColor(LED.Color.BLUE)
            time.sleep(0.25)
            led.turnOff()
            time.sleep(0.25)
        time.sleep(0.5)
            
            
