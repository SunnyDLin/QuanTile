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
