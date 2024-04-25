# ------------------------------------------------------------------------------
# Module: qu_tile
#
# Description:
#   This file implements a class representing a physical tile.  An instance of
#   QuTile specifies its tile type.  The main functionalities include reading
#   state from its previous tile, performing the specified operation of the tile
#   type, and handles state requests from the next tile.
#
# Platforms:
#   MicroPython, Python3
#
#   This module is intended to run with MicroPython with ULab.  However,
#   it supports Python3 as extensive and sensible as possible to ease the
#   development on a desktop PC.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

from qu_states import QuantumBitState, GateOperators, GateTypes
import time
import sys

from comm_util import Comm

# packages to adapt both CPython and MicroPython
from variant import is_cpython, Log

if is_cpython:
    from threading import Thread
else:
    import _thread


class QuTile:
    outState = QuantumBitState()
    comm = Comm()

    def __init__(self, gate_type: object = GateTypes.IDENTITY) -> object:
        self._type = gate_type
        self._name = gate_type.name
        self._operator = eval('GateOperators.' + self._name)
        self.requestThreadRunning = False
        self.serviceThreadRunning = False

        # Set up callback function for CommUtil to get data from here.
        def getQuantumState():
            return self.outState.theta, self.outState.phi
        self.comm.setStateRequestCallback(getQuantumState)

        def getComponentType():
            return self._type
        self.comm.setComponentTypeRequestCallback(getComponentType)

        def replaceOperator(name):
            self._operator = eval('GateOperators.' + name)
            self._type = eval('GateTypes.' + name)
            self._name = name
        self.comm.setReplaceOperatorCallback(replaceOperator)

    def getOperator(self):
        return self._operator

    def setOperator(self, operator):
        self._operator = operator

    # State update routine: Periodically requests state from the previous gate.
    # TODO: Stop using this function.
    # This implementation puts request and process response on the same thread.
    # This is not idea because it is harder to manage many differ requests, which
    # typically running with different request frequency and response latency.
    # We cannot remove it because QuTile cannot support more than two threads.
    # As a result, it cannot use `TimeoutRoutine` like Measurement and Configurator.
    def updateStateRoutine(self):
        self.requestThreadRunning = True

        while self.requestThreadRunning:
            theta, phi = self.comm.requestInputState()
            
            state = QuantumBitState(theta, phi)
            state.operate(self._operator, update=True)
            self.outState = state
            print("[QuTile] Output state:", self.outState.getBlochSphereState())

            time.sleep(0.01)

    # Service routine
    def serviceThread(self):
        self.serviceThreadRunning = True
        while self.serviceThreadRunning:
            self.comm.serviceRequest()

    # Start running the tile
    def start(self):
        # Launch two threads, one for input state update and the other for request service.
        if is_cpython:  # it is c python
            # Despite this code only intended to run on a QuTile with Micro Python,
            # C Python is supported here for debugging purpose.
            if self.requestThreadRunning:
                raise RuntimeError("Starting an update thread which is already running.")
            Thread(target=self.updateStateRoutine).start()
            
            if self.serviceThreadRunning:
                raise RuntimeError("Starting a service thread which is already running.")
            Thread(target=self.serviceThread).start()
        else:  # it is micro python
            _thread.start_new_thread(self.updateStateRoutine, ())

            # Probably due to a thread limitation, MicroPython doesn't run the second thread.
            # Call serviceThread() instead of _thread.start_new_thread(self.service, ())
            self.serviceThread()

    # Stop running the tile
    def stop(self):
        self.requestThreadRunning = False
        self.serviceThreadRunning = False


# Unit test for the main class in this script.
def unitTest():
    # setup to redirect stdout to a log file
    unit_test_dir = 'unit_test'
    if is_cpython:
        import os
        file_name = unit_test_dir + '/' + os.path.basename(__file__) + ".log"
    else:
        file_name = unit_test_dir + "/qu_tile.py.log"
    tee = Log()
    tee.redirect_stdout(file_name)

    # Unit test starts here.
    tile = QuTile()

    tile.start()
    time.sleep(3)
    tile.stop()

    tee.read()     # reset stdout and print from the file


def __run__():
    from led import LED
    led = LED()
    led.setColor(LED.Color.DIM_YELLOW)
    
    tile = QuTile(gate_type=GateTypes.HADAMARD)
    tile.start()


if __name__ == '__main__':
    __run__()
