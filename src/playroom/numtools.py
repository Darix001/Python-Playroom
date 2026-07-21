from math import ceil


def bytes_of_int(x: int, /):
    """Returns number of bytes necessary to represent x"""

    return ceil(x.bit_length() / 8)
