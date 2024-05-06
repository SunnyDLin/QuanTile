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
# Module: variant
#
# Description:
#   This file implements functions to support other modules running on both
#   CPython and MicroPython.
#
# Platforms:
#   MicroPython, CPython3
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

import sys

is_cpython = sys.implementation.name == "cpython"
is_micropython = sys.implementation.name == "micropython"

class Log:
    _file = None
    _file_name = None
    _stdout = sys.stdout    # handle to the original stdout

    def redirect_stdout(self, file_name):
        self._file_name = file_name
        self._file = open(file_name, 'w')
        if is_cpython:
            sys.stdout = self._file
        else:
            import uos
            uos.dupterm(self._file)
            

    # Reset stdout and print messages from the file.
    def read(self):
        if self._file is None:
            raise RuntimeError("Standard output was not redirected.")
        
        self._file.close()
        if is_cpython:
            sys.stdout = self._stdout
            print(open(self._file_name, 'r').read())
        else:
            import uos
            uos.dupterm(None)
        
        self._file = None

