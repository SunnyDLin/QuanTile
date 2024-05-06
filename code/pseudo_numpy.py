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
# Module: pseudo_numpy
#
# This module is a container of NumPy functions which are not suppoprted in ULab
# or behaves differently from the regular NumPy.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

import math     # supports basic mathmatics
import cmath    # handles complex numbers

import variant

if variant.is_cpython:
    import numpy as np
else:
    from ulab import numpy as np


# This function take a vector b and transform with matrix a.
# The function np.matmul(a,b) is available in cpython by not ULab.
# It is to replace np.matmul to support ULab.
# The function psnp.mat_vec_mul is a wrapper of np.matmul in NumPy
# and implemntation to support ULab.
def mat_vec_mul(a, b):
    if variant.is_cpython:
        return np.matmul(a, b)
    else:
        if len(b.shape) == 1:
            c = np.zeros((a.shape[0]), dtype=np.complex)
            for i in range(a.shape[0]):
                for k in range(a.shape[1]):
                    c[i] += a[i][k] * b[k]
        else:
            c = np.zeros((a.shape[0], b.shape[-1]), dtype=np.complex)
            for i in range(a.shape[0]):
                for j in range(b.shape[-1]):
                    for k in range(a.shape[1]):
                        c[i][j] += a[i][k] * b[k][j]
        return c


# This function creates a complex array from a list.
# The ULab np.array supports dtype value for complex numbers differently from NumPi in CPython.
def c_array(li):
    if variant.is_cpython:
        return np.array(li, dtype=np.cdouble)
    else:
        return np.array(li, dtype=np.complex)


# This function replace np.kron(a,b) for MicroPython.
def kronecker_product(a, b):
    if variant.is_cpython:
        return np.kron(a, b)
    else:
        if len(a.shape) > 1:
            if len(b.shape) > 1:
                m, n = a.shape
                p, q = b.shape
                result = np.zeros((m * p, n * q), dtype=np.complex)
                for i in range(m):
                    for j in range(n):
                        result[i * p:(i + 1) * p, j * q:(j + 1) * q] = a[i, j] * b
            else:
                m, n = a.shape
                p = b.shape[0]
                result = np.zeros((m * p, n), dtype=np.complex)
                for i in range(m):
                    for j in range(n):
                        result[i * p:(i + 1) * p, j:(j + 1)] = a[i, j] * b
        else:
            if len(b.shape) > 1:
                m = a.shape[0]
                p, q = b.shape
                result = np.zeros((m * p, q), dtype=np.complex)
                for i in range(m):
                    result[i * p:(i + 1) * p, 0:q] = a[i] * b
            else:
                m = a.shape[0]
                p = b.shape[0]
                result = np.zeros(m * p, dtype=np.complex)
                for i in range(m):
                    result[i * p:(i + 1) * p] = a[i] * b
    return result
