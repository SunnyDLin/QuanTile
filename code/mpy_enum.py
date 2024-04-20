# ------------------------------------------------------------------------------
# This module is to implement Enum class for the functions needed for QuanTile.
# Enum class is not available in MicroPython as a built-in package.
#
# Authors:
#   Sunny Lin
# ------------------------------------------------------------------------------

class Enum:
    def __init__(self, **kwargs):
        self._members = {}
        for name, value in kwargs.items():
            enum_value = self.EnumValue(name, value)
            setattr(self, name, enum_value)
            self._members[name] = enum_value

    def __str__(self):
        return self.name()

    def __repr__(self):
        return self.name()

    def members(self):
        return self._members

    # def name(self):
    #     for name, value in self._members.items():
    #         if value == self:
    #             return name
    #
    # def value(self):
    #     return self._members[self.name()].value

    def name(self, value):
        for name, enum_value in self._members.items():
            if enum_value.value == value:
                return name
        return None

    def value(self, name):
        return self._members[name].value

    class EnumValue:
        def __init__(self, name, value):
            self.name = name
            self.value = value

        def __str__(self):
            return self.name

        def __repr__(self):
            return self.name


# Unit test for the classes in this script.
def unitTest():
    colors = Enum(
        RED=1,
        GREEN=2,
        BLUE=3,
        )

    print(colors.RED)            # Output: RED
    print(colors.GREEN)          # Output: GREEN
    print(colors.BLUE)           # Output: BLUE

    print(colors.GREEN.value)      # Output: 1
    print(colors.GREEN.name)       # Output: RED


if __name__ == '__main__':
    unitTest()
