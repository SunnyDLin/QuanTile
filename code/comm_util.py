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

# ------------------------------------------------------------------------------
# Module: comm_util
#
# Description:
#   This file implements a communication module to handle inter-device connection.
#
# Platforms:
#   MicroPython, Python3
#
#   This module is intended to run on both MicroPython with ULab and Python3 on a PC.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

# packages to adapt both CPython and MicroPython
from variant import is_cpython, is_micropython, Log

# CPython has an enum package but MicroPython doesn't.
from mpy_enum import Enum   # Use mpy_enum for both interpreters.

if is_micropython:  # it is micro python
    import machine
    import ustruct
    import _thread
else:  # it is c python
    import serial
    import struct
    from threading import Thread

import time
from indicator import Indicator

from qu_states import GateTypes, GateOperators

class OpCode(Enum):
    QuantumStateRequest = 0x01
    ComponentTypeRequest = 0x02
    ComponentTypeChangeRequest = 0x03
    QuantumStateResponse = 0x81
    ComponentTypeResponse = 0x82


class DataFormatEnum:
    UNSPECIFIED = 0
    THETA_PHI = 1


class Comm:
    indicator = Indicator()

    # This is a message header required to send before each data transfer.
    _MsgHeader = bytes([0x7f, 0xff, 0xff, 0xff])
    
    uart_in = None
    uart_out = None

    # Use port_name to specify port name of the UART channel on a PC.
    # It would be something like 'COMx' or '/dev/ttyusbx'.
    # It is not used in MicroPython.
    # PC is used as a measurement device. State is not forwarded to next stage, so uart_out is not necessary.
    def __init__(self, port='COM0',
                 baudrate=115200,
                 parity=None,
                 bits=8,
                 stop=1,
                 timeout=100):

        self.updateInputStateCallbackData = 0
        if is_micropython:
            self.uart_in = machine.UART(0, baudrate,
                                        parity=parity, bits=bits,
                                        stop=stop, timeout=timeout)  # connect to left side of a tile
            self.uart_out = machine.UART(1, baudrate,
                                         parity=parity, bits=bits,
                                         stop=stop, timeout=timeout)  # connect to right side of a tile
        else:  # if is_cpython
            self.uart_in = serial.Serial(port, baudrate,
                                         parity=serial.PARITY_NONE,
                                         bytesize=bits,
                                         stopbits=stop,
                                         timeout=timeout)

        if is_cpython:  # it is c python
            if self.messageServiceRoutineRunning:
                raise RuntimeError("Starting message service thread which is already running.")
            self.messageServiceThread = Thread(target=self.messageServiceRoutine)
            self.messageServiceThread.start()
        # else:
        #     # Here is a problem for QuTile.  It fails on the thread.
        #     # This method in MicroPython seems support only one thread in addition to the main one.
        #     # We should either find a way to support more threads or pseudo threads.
        #     # In QuTile, we cannot apply TimeoutRoutine.
        #     self.messageServiceThread = _thread.start_new_thread(self.messageServiceRoutine, ())

    # Set up a function to get component type.
    getComponentType = None

    def setComponentTypeRequestCallback(self, func):
        self.getComponentType = func

    # Set up a function replace the operator in a tile.
    replaceOperator = None

    def setReplaceOperatorCallback(self, func):
        self.replaceOperator = func

    # Function to check is a specified pattern is received on a UART port.
    def waitForPattern(self, uart, pattern, timeout=0.0):
        timeEscape = 0.0
        while True:
            for i in range(len(pattern)):
                if is_cpython:
                    dataAvail = uart.in_waiting
                else:  # if is_micropython
                    dataAvail = uart.any()
                if dataAvail >= 1:
                    data = uart.read(1)
                    if data[0] != pattern[i]:
                        break
                else:
                    break
                if i == len(pattern) - 1:
                    return True
            waitTime = 0.001
            time.sleep(waitTime)
            if timeout > 0.0:
                timeEscape += waitTime
                if timeEscape >= timeout:
                    return False

    def sendSync(self, uart):
        uart.write(self._MsgHeader)

    def sendStateRequest(self, uart=uart_in):
        self.sendSync(uart)
        # Send a state request.
        buf = bytearray(4)
        buf[0] = int(OpCode.QuantumStateRequest)  # command
        buf[1] = 1                                # num qubits
        buf[2] = DataFormatEnum.THETA_PHI         # data format
        buf[3] = 0                                # icd rev
        uart.write(buf)

    def sendComponentTypeRequest(self, uart=uart_in):
        self.sendSync(uart)
        # Send a component type request.
        buf = bytearray(4)
        buf[0] = int(OpCode.ComponentTypeRequest)  # command
        buf[1] = 0                                 # spare
        buf[2] = 0                                 # spare
        buf[3] = 0                                 # icd rev
        uart.write(buf)

    def sendComponentTypeChangeRequest(self, type_id, uart=uart_in):
        self.sendSync(uart)
        # Send a component type change request.
        buf = bytearray(4)
        buf[0] = int(OpCode.ComponentTypeChangeRequest)  # command
        buf[1] = int(type_id)                            # component type ID
        buf[2] = 0                                       # spare
        buf[3] = 0                                       # icd rev
        uart.write(buf)

    # Set up a function to get quantum state from a tile.
    getQuantumState = None

    def setStateRequestCallback(self, func):
        self.getQuantumState = func

    # Set up a function to handle input state change.
    updateInputStateCallback = None
    updateInputStateCallbackData = 0

    def setUpdateInputStateCallback(self, func, callback_data=0):
        self.updateInputStateCallback = func
        self.updateInputStateCallbackData = callback_data

    # Set up a function to update gate type.
    updateGateTypeCallback = None
    updateGateTypeCallbackData = 0

    def setUpdateGateTypeCallback(self, func, callback_data=0):
        self.updateGateTypeCallback = func
        self.updateGateTypeCallbackData = callback_data

    messageServiceRoutineRunning = False

    def messageServiceRoutine(self):
        self.messageServiceRoutineRunning = True
        while self.messageServiceRoutineRunning:
            if not self.waitForPattern(self.uart_in, self._MsgHeader, timeout=0.01):
                continue
            if not self.waitForBytes(self.uart_in, 4, timeout=0.01):
                continue
            data = self.uart_in.read(4)

            if data[0] == OpCode.QuantumStateResponse:  # assuming 1 qubit, theta-phi format, and version 0
                self.waitForBytes(self.uart_in, 8)
                data = self.uart_in.read(8)
                if is_micropython:
                    theta, phi = ustruct.unpack('f', data[0:4])[0], ustruct.unpack('f', data[4:8])[0]
                else:
                    theta, phi = struct.unpack('f', data[0:4])[0],  struct.unpack('f', data[4:8])[0]

                self.indicator.showValidInput()

                if self.updateInputStateCallback:
                    self.updateInputStateCallback(theta, phi, self.updateInputStateCallbackData)

            elif data[0] == OpCode.ComponentTypeResponse:
                gateType = int(data[1])
                if self.updateGateTypeCallback:
                    self.updateGateTypeCallback(gateType, self.updateGateTypeCallbackData)

    # Requests state input thread
    # TODO: Stop using this function.
    # We cannot remove it because QuTile cannot support `TimeoutRoutine`.
    def requestInputState(self, raiseException=False):

        print("[client] Send a state request")
        timeLapse = 0
        waitStep = 0.005
        connectionTimeout = 0.01   # timeout before using a default input state
        while True:
            self.sendStateRequest(self.uart_in)

            # Wait for a sync packet.  Set a timeout because there may be no service.
            if self.waitForPattern(self.uart_in, self._MsgHeader, timeout=waitStep):
                break
            elif timeLapse < connectionTimeout:
                timeLapse += waitStep
            else:
                print("[client] Server not reachable, state: (0.0 0.0)")
                self.indicator.showOpenInput()
                if raiseException:
                    raise ConnectionError("No input state available")
                return 0.0, 0.0
        
        # TODO: Using a handler or callback to retrieve state is a better idea.
        # We cannot do it because QuTile cannot support `TimeoutRoutine`.
        # It is however unnecessary for the current stage of implementation.
        # Read state response
        theta = 0.0
        phi = 0.0
        
        self.waitForBytes(self.uart_in, 12, timeout=0.01)
        if is_cpython:
            dataAvail = self.uart_in.in_waiting
        else:  # if is_micropython
            dataAvail = self.uart_in.any()
        if dataAvail >= 12:
            data = self.uart_in.read(12)
            if len(data) == 12 and data[0] == OpCode.QuantumStateResponse:
                if is_micropython:
                    theta = ustruct.unpack('f', data[4:8])[0]
                    phi = ustruct.unpack('f', data[8:12])[0]
                else:
                    theta = struct.unpack('f', data[4:8])[0]
                    phi = struct.unpack('f', data[8:12])[0]
                self.indicator.showValidInput()
            else:
                self.indicator.showInvalidInput()
        else:
            self.indicator.showOpenInput()

        print("[client] Input state: ({0}, {1})".format(theta, phi))
        return theta, phi

    # Waits for `numBytes` of bytes available on `uart`
    def waitForBytes(self, uart, numBytes, waitStep=0.001, timeout=0.01):
        timeLapse = 0.0
        while True:
            if is_cpython:
                dataAvail = uart.in_waiting
            else:  # if is_micropython
                dataAvail = uart.any()
            if dataAvail >= numBytes:
                break
            
            time.sleep(waitStep)
            timeLapse += waitStep
            if timeLapse >= timeout:
                return False
        return True

    # Sends a float value to `uart`
    def sendFloat(self, uart, value):
        data = ustruct.pack("f", value)
        uart.write(data)

    count = 0
    # This function listens to UART out port for a service request.
    def serviceRequest(self):
        # Wait for a state request.
        print("[server] Listening to request....")

        self.waitForPattern(self.uart_out, self._MsgHeader)  # Wait for synchronization message header.

        self.waitForBytes(self.uart_out, 4, timeout=0.01)  # At least 4 bytes needed before proceeding.
        if is_cpython:  # it is c python
            dataAvail = self.uart_out.in_waiting
        else:  # it is micro python
            dataAvail = self.uart_out.any()
        if dataAvail >= 4:
            data = self.uart_out.read(4)
            
            if data[0] == OpCode.QuantumStateRequest:  # This is a state request.
                print("[server] Received a state request")
                self.sendSync(self.uart_out)

                # Client needs the state. Send the state to `uart_out`
                buf = bytearray(4)
                buf[0] = int(OpCode.QuantumStateResponse)  # command
                buf[1] = 1                                 # bits
                buf[2] = DataFormatEnum.THETA_PHI          # data format
                buf[3] = 0                                 # icd rev
                self.uart_out.write(buf)

                if self.getQuantumState:
                    theta, phi = self.getQuantumState()  # The owner of the comm knows the state.  Callback to get it.
                    self.sendFloat(self.uart_out, theta)
                    self.sendFloat(self.uart_out, phi)
                else:
                    raise ValueError("Function for `tateRequestCallback` is not set.")

            elif data[0] == OpCode.ComponentTypeRequest:
                print("[server] Received a component type request")
                self.sendSync(self.uart_out)
                if self.getComponentType:
                    componentType = self.getComponentType()
                else:
                    raise ValueError("Function for `getComponentType` is not set.")

                # Client needs the component type. Send the type to `uart_out`
                buf = bytearray(4)
                buf[0] = int(OpCode.ComponentTypeResponse)  # command
                # # This conversion is incorrect.
                buf[1] = int(componentType.value)           # component type
                buf[2] = 0                                  # additional data length
                buf[3] = 0                                  # icd rev
                self.uart_out.write(buf)

            elif data[0] == OpCode.ComponentTypeChangeRequest:
                componentTypeId = int(data[1])
                confFileName = 'gate.cfg'
                typeNames = [name for name in GateTypes.members()]
                componentTypeName = "UNDEFINED"
                for name in typeNames:
                    member = eval('GateTypes.' + name)
                    if member.value == componentTypeId:
                        componentTypeName = member.name
                        break
                with open(confFileName, 'w') as file:
                    file.write(componentTypeName)

                if self.replaceOperator:
                    self.replaceOperator(componentTypeName)

    def stop(self):
        self.messageServiceRoutineRunning = False
