################################################################################
# QuanTile Proprietary License
#
# Copyright 2024 Sunny Lin
#
# All rights reserved.
# 
# The hardware and software designs associated with QuanTile are the proprietary
# property of Sunny Lin Permission is hereby granted to schools and educational
# institutions to use the Designs for educational purposes only. Any use of the
# designs for commercial purposes, including but not limited to reproduction,
# modification, distribution, or incorporation into other products, without the
# express written permission of Sunny Lin is strictly prohibited.
# 
# For inquiries regarding commercial use, please contact
# 
# Sunny Lin
# sunny.khh@gmail.com
################################################################################


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
