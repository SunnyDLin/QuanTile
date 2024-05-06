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
