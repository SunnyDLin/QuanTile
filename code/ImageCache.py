# ------------------------------------------------------------------------------
# Module Name: ImageCache
#
# Description:
#   This module implements a cache of images used to display tile symbols and operation matrices.
#   It offers two member functions, getSymbolImage(name) and getMatrixImage(name), to the caller.
#   The functions take a text string as name to find the associate Tkinter image.
#   If it is available, typically it was used and loaded before, simply return the image.
#   Otherwise, it loads the image from the file system and store it locally for potential future use,
#   and then return the loaded image to the caller.

# Platforms:
#   CPython3 on Raspberry Pi 2 and up, excluding Zero and Pico.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

from tkinter import PhotoImage


class ImageCache:
    def __init__(self):
        self._symbol_cache = {}
        self._matrix_cache = {}

    def getSymbolImage(self, name):
        if name in self._symbol_cache:
            return self._symbol_cache[name]
        else:
            try:
                fileName = f"images/{name}-symbol.gif"
                image = PhotoImage(file=fileName)
                self._symbol_cache[name] = image
                return image
            except FileNotFoundError:
                return None

    def getMatrixImage(self, name):
        if name in self._matrix_cache:
            return self._matrix_cache[name]
        else:
            try:
                fileName = f"images/{name}-matrix.gif"
                image = PhotoImage(file=fileName)
                self._matrix_cache[name] = image
                return image
            except FileNotFoundError:
                return None
