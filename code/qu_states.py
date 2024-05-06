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
# Module: qu_states
#
# Description:
#   This file implements classes related to quantum state.  QuStates class
#   supports multi-qubit state.  It includes QuantumBitState class to support
#   single-qubit state.  A QuantumBitState object holds state of a qubit and
#   operators which can be applied to the qubit and alter the state as a result.
#
# Platforms:
#   MicroPython, CPython3
#
#   This module is intended to run with MicroPython with ULab.  However,
#   it supports CPython3 as extensive and sensible as possible to ease the
#   development on a desktop PC.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

import math     # supports basic mathmatics
import cmath    # handles complex numbers

# CPython has a enum package but MicroPython doesn't.
from mpy_enum import Enum   # Use mpy_enum for both interpreters.

# packages to adapt both CPython and MicroPython
from variant import is_cpython, Log
import pseudo_numpy as psnp

if is_cpython:
    import numpy as np
else:
    from ulab import numpy as np

# Enumeration of component types.  Keys should be all upper case.
GateTypes = Enum(
    UNDEFINED      = 0x00,
    IDENTITY       = 0x01,
    PAULI_X        = 0x02,
    PAULI_Y        = 0x03,
    PAULI_Z        = 0x04,
    HADAMARD       = 0x05,
    RX_PI_DIV2     = 0x06,
    RY_PI_DIV2     = 0x07,
    RZ_PI_DIV2     = 0x08,
    RX_PI_DIV4     = 0x09,
    RY_PI_DIV4     = 0x0a,
    RZ_PI_DIV4     = 0x0b,
    PHASE          = 0x0e,
    TWIRL          = 0x0f,
    CONTROLLED_NOT = 0x41,
    CONTROLLED_Z   = 0x42,
    SWAP           = 0x43,
    TOFFOLI        = 0x81,
)

# Definitions of unitary matrices of known quantum operators.
# This list includes single and multiple qubits.
# https://en.wikipedia.org/wiki/Quantum_logic_gate#Representation
GateOperators = Enum(
    IDENTITY =
        [[1, 0],
         [0, 1]],       # I
    PAULI_X =
        [[0, 1],
         [1, 0]],       # X
    PAULI_Y =
        [[0, -1j],
         [1j,  0]],      # Y
    PAULI_Z =
        [[1,  0],
         [0, -1]],      # Z
    HADAMARD =
        [[1/math.sqrt(2.0),  1/math.sqrt(2.0)],
         [1/math.sqrt(2.0), -1/math.sqrt(2.0)]],      # H
    RX_PI_DIV2 =
        [[      math.cos(math.pi/4), -1j * math.sin(math.pi/4)],
         [-1j * math.sin(math.pi/4),       math.cos(math.pi/4)]],
    RY_PI_DIV2 =
        [[math.cos(math.pi/4), - math.sin(math.pi/4)],
         [math.sin(math.pi/4),   math.cos(math.pi/4)]],
    RZ_PI_DIV2 =
        [[cmath.exp(-1j * math.pi/4), 0],
         [0,  cmath.exp(1j * math.pi/4)]],
    RX_PI_DIV4 =
        [[      math.cos(math.pi/8), -1j * math.sin(math.pi/8)],
         [-1j * math.sin(math.pi/8),       math.cos(math.pi/8)]],
    RY_PI_DIV4 =
        [[math.cos(math.pi/8), - math.sin(math.pi/8)],
         [math.sin(math.pi/8),   math.cos(math.pi/8)]],
    RZ_PI_DIV4 =
        [[cmath.exp(-1j * math.pi/8), 0],
         [0,  cmath.exp(1j * math.pi/8)]],
    PHASE =
        [[1,  0],
         [0, 1j]],          # P or S
    TWIRL =
        [[1, 0],
         [0, cmath.exp(1j * math.pi/4)]],      # T
    CONTROLLED_NOT =
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]],      # CNOT, CX
    CONTROLLED_Z =
        [[1,  0,  0,  0],
         [0,  1,  0,  0],
         [0,  0,  1,  0],
         [0,  0,  0, -1]],   # CZ
    SWAP =
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1]],      # swap
    TOFFOLI =
        [[1, 0, 0, 0, 0, 0, 0, 0],
         [0, 1, 0, 0, 0, 0, 0, 0],
         [0, 0, 1, 0, 0, 0, 0, 0],
         [0, 0, 0, 1, 0, 0, 0, 0],
         [0, 0, 0, 0, 1, 0, 0, 0],
         [0, 0, 0, 0, 0, 1, 0, 0],
         [0, 0, 0, 0, 0, 0, 0, 1],
         [0, 0, 0, 0, 0, 0, 1, 0]],      # CCNOT, CCX, TOFF
    )


class QuantumBitState:
    def __init__(self, theta=0.0, phi=0.0):
        # range:
        #   0.0 <= theta <= math.pi
        #   0.0 <= phi   <= 2 * math.pi:
        while theta < 0.0:
            theta += math.pi * 2
        while theta > math.pi * 2:
            theta -= math.pi * 2
        if theta > math.pi:
            # mirror on Z axis
            theta = math.pi * 2 - theta
            phi += math.pi
        while phi < 0.0:
            phi += math.pi * 2
        while phi > math.pi * 2:
            phi -= math.pi * 2
        # if theta < 0.0 or theta > math.pi or phi < 0.0 or phi >= 2 * math.pi:
        #     raise ValueError("Initial value out of range (theta, phi)=({}, {})".format(theta, phi))

        self.theta = theta
        self.phi = phi

    def getBlochSphereState(self):
        return self.theta, self.phi

    def setBlochSphereState(self, theta, phi):
        self.theta = theta
        self.phi = phi

    def getStandardBasisState(self):
        alpha = math.cos(self.theta / 2)
        beta = cmath.exp(1j * self.phi) * math.sin(self.theta / 2)
        return alpha, beta

    def setStandardBasisState(self, alpha, beta):
        st = psnp.c_array([alpha, beta])

        # Several ways to normalize a vector, but MicroPython does not support them.  The last one works.
        # alpha, beta = st / np.linalg.norm(st)                 # np.linagl.norm() is not available in ULab
        # alpha, beta = st / np.sqrt(np.sum(np.abs(st) ** 2))   # np.abs is not available in ULab
        alpha, beta = st / np.sqrt(np.sum(np.real(st)**2 + np.imag(st)**2))  # This line works in both NumPy and ULab
        
        # determine theta and phi from alpha and beta
        self.theta = 2 * math.acos(abs(alpha))
        if alpha == 0:
            global_phase = 1
        else:
            global_phase = abs(alpha) / alpha  # consider global phase equivalence
        self.phi = cmath.phase(beta * global_phase)
        if self.theta == 0.0:
            self.phi = 0.0

    def getVector(self):
        return math.sin(self.theta) * math.cos(self.phi), \
               math.sin(self.theta) * math.sin(self.phi), \
               math.cos(self.theta)

    def rotate(self, matrix, update=True):
        state = psnp.c_array(self.getStandardBasisState())
        mat = psnp.c_array(matrix)

        # np.matmul(mat, state) is available in cpython by not ULab.
        # psnp.mat_vec_mul is a wrapper of np.matmul in NumPy and
        # implemntation to support ULab.
        new_state = psnp.mat_vec_mul(mat, state)
        
        if update:
            self.setStandardBasisState(new_state[0], new_state[1])
        return new_state

    def rotX(self, phi, update=True):
        mat = [[math.cos(phi / 2.0), -1j * math.sin(phi / 2.0)],
             [-1j * math.sin(phi / 2.0), math.cos(phi / 2.0)]]
        return self.rotate(mat, update)

    def rotY(self, phi, update=True):
        mat = [[math.cos(phi / 2.0), -math.sin(phi / 2.0)],
             [math.sin(phi / 2.0), math.cos(phi / 2.0)]]
        return self.rotate(mat, update)

    def rotZ(self, phi, update=True):
        mat = [[cmath.exp(-1j * phi / 2.0), 0],
             [0, cmath.exp(1j * phi / 2.0)]]
        return self.rotate(mat, update)

    def operate(self, operator, update=True):
        if len(operator.value) != 2 or len(operator.value[0]) != 2:
            raise ValueError("Operator matrix for a single qubit requires 2x2.  Provided size = {}x{}".
                             format(len(operator.value), len(operator.value[0])))
        return self.rotate(operator.value, update)


class QuStates:
    states = []          # a list of qubits holding QuState's

    # Constructor:
    # init_states is a list of tuples of (theta, phi)
    # if init_states is not provided, create "bits" qubits of (theta, phi)'s.
    def __init__(self, init_states=None, num_bits=1, theta=0.0, phi=0.0):
        if init_states is None:
            if num_bits <= 0:
                raise ValueError("Number of qubit less than 1: num_bits={}".format(num_bits))
            for i in range(num_bits):
                self.states.append(QuantumBitState(theta, phi))
        else:
            for i in range(len(init_states)):
                if len(init_states[i]) != 2:
                    raise ValueError("State at position {} has a wrong data length.".format(i))
                self.states.append(QuantumBitState(init_states[i][0], init_states[i][1]))

    def getNumBits(self):
        return len(self.states)

    def getBlochSphereState(self):
        vec = []
        for i in range(len(self.states)):
            vec.append(self.states[i].getBlochSphereState())
        return vec

    def getStandardBasisState(self):
        vec = []
        for i in range(len(self.states)):
            vec.append(self.states[i].getStandardBasisState())
        return vec

    def tensor_product(self, mat):
        if len(mat) == 1:
            return mat[0]
        return psnp.kronecker_product(mat[0], self.tensor_product(mat[1:]))

    def getTensorState(self):
        return self.tensor_product(psnp.c_array(self.getStandardBasisState()))

    def operate_multi_qu(self, operator):
        if len(operator.value) != 2 ** len(self.states):
            raise ValueError("{} has a matrix size of ({}x{}) which does not fit the number of qubits ({}).".
                             format(operator, len(operator.value), len(operator.value[0]), len(self.states)))

        st = self.getTensorState()
        
        # np.matmul(mat, state) is available in cpython by not ULab.
        # psnp.mat_vec_mul is a wrapper of np.matmul in NumPy and
        # implemntation to support ULab.
        new_states = psnp.mat_vec_mul(np.array(operator.value), st)

        for i in range(len(self.states)):
            self.states[i].setStandardBasisState(new_states[i*2], new_states[i*2+1])
        return st


# Unit test for the classes in this script.
def unitTest():
    # setup to redirect stdout to a log file
    unit_test_dir = 'unit_test'
    if is_cpython:
        import os
        file_name = unit_test_dir + '/' + os.path.basename(__file__) + ".log"
    else:
        file_name = unit_test_dir + "/qu_states.py.log"
    tee = Log()
    tee.redirect_stdout(file_name)

    # Unit test starts here.
    circuit = QuStates(num_bits=2)
    circuit.states[0].operate(GateOperators.HADAMARD)
    circuit.operate_multi_qu(GateOperators.CONTROLLED_NOT)
    state = QuantumBitState()          # initialize to cat 0
    print("Initial state:  0 cat")
    print("  (theta phi) = {}".format(state.getBlochSphereState()))
    print("  (alpha beta) = {}".format(state.getStandardBasisState()))
    print("  vector = {}".format(state.getVector()))
    print()

    state.rotY(math.pi/2)
    print("After the first rotation:")
    print("  (theta phi) = {}".format(state.getBlochSphereState()))
    print("  (alpha beta) = {}".format(state.getStandardBasisState()))
    print("  vector = {}".format(state.getVector()))
    print()

    state.rotZ(math.pi)
    print("After the second rotation:")
    print("  (theta phi) = {}".format(state.getBlochSphereState()))
    print("  (alpha beta) = {}".format(state.getStandardBasisState()))
    print("  vector = {}".format(state.getVector()))

    tee.read()     # reset stdout and print from the file


if __name__ == '__main__':
    unitTest()

