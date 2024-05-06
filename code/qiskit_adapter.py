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

from qu_states import QuantumBitState


# This class is an adapter for testing Qiskit-like syntax.
class QuantumCircuit:
    registers = []

    def __init__(self):
        pass

    def add_register(self, register):
        self.registers.append(register)

    def __str__(self):
        s = '['
        for i in range(len(self.registers)):
            if i != 0:
                s += ', '
            s += str(self.registers[i])
        s += ']'
        return s


# This class is an adapter for testing Qiskit-like syntax.
class QuantumRegister:
    qubits = []
    name = None

    def __init__(self, num_qubits, name='q'):
        self.name = name
        for i in range(num_qubits):
            self.qubits.append(QuantumBitState)

    def getNumQubit(self):
        return len(self.qubits)

    def __str__(self):
        return '{}({}, \'{}\')'.format(self.__class__.__name__, len(self.qubits), self.name)
