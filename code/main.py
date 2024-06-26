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

from qu_tile import QuTile
from qu_states import GateTypes

from led import LED
led = LED()
led.setColor(LED.Color.DIM_YELLOW)

confFileName = 'gate.cfg'
try:
    with open(confFileName, 'r') as file:
        # Read the entire content of the file
        gate = file.read()
        gate = gate.upper()

    tile = QuTile(gate_type=eval('GateTypes.' + gate))
    print('Configure the tile as ' + gate + ' gate as specified in ' + confFileName)
except:
    tile = QuTile(gate_type=GateTypes.IDENTITY)
    print('Configure the tile as default HADAMARD gate')

tile.start()
