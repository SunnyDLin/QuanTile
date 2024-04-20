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

