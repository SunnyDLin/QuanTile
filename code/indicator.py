
# packages to adapt both CPython and MicroPython
from variant import is_micropython


if is_micropython:
    from led import LED


class Indicator:
    led = None

    def __init__(self):
        if is_micropython:
            self.led = LED()

    # Indicates the input is open
    def showOpenInput(self):
        if self.led:
            self.led.setColor(LED.Color.BLUE)


    # Indicates the input has a valid state
    def showValidInput(self):
        if self.led:
            self.led.setColor(LED.Color.GREEN)


    # Indicates the input has an invalid state
    def showInvalidInput(self):
        if self.led:
            led.setColor(LED.Color.RED)
