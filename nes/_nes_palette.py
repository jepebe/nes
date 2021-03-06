from typing import List, Tuple


def _create_palette() -> List[Tuple[int, int, int]]:
    pal = [0x00] * 0x40
    pal[0x00] = (84, 84, 84)
    pal[0x01] = (0, 30, 116)
    pal[0x02] = (8, 16, 144)
    pal[0x03] = (48, 0, 136)
    pal[0x04] = (68, 0, 100)
    pal[0x05] = (92, 0, 48)
    pal[0x06] = (84, 4, 0)
    pal[0x07] = (60, 24, 0)
    pal[0x08] = (32, 42, 0)
    pal[0x09] = (8, 58, 0)
    pal[0x0A] = (0, 64, 0)
    pal[0x0B] = (0, 60, 0)
    pal[0x0C] = (0, 50, 60)
    pal[0x0D] = (0, 0, 0)
    pal[0x0E] = (0, 0, 0)
    pal[0x0F] = (0, 0, 0)

    pal[0x10] = (152, 150, 152)
    pal[0x11] = (8, 76, 196)
    pal[0x12] = (48, 50, 236)
    pal[0x13] = (92, 30, 228)
    pal[0x14] = (136, 20, 176)
    pal[0x15] = (160, 20, 100)
    pal[0x16] = (152, 34, 32)
    pal[0x17] = (120, 60, 0)
    pal[0x18] = (84, 90, 0)
    pal[0x19] = (40, 114, 0)
    pal[0x1A] = (8, 124, 0)
    pal[0x1B] = (0, 118, 40)
    pal[0x1C] = (0, 102, 120)
    pal[0x1D] = (0, 0, 0)
    pal[0x1E] = (0, 0, 0)
    pal[0x1F] = (0, 0, 0)

    pal[0x20] = (236, 238, 236)
    pal[0x21] = (76, 154, 236)
    pal[0x22] = (120, 124, 236)
    pal[0x23] = (176, 98, 236)
    pal[0x24] = (228, 84, 236)
    pal[0x25] = (236, 88, 180)
    pal[0x26] = (236, 106, 100)
    pal[0x27] = (212, 136, 32)
    pal[0x28] = (160, 170, 0)
    pal[0x29] = (116, 196, 0)
    pal[0x2A] = (76, 208, 32)
    pal[0x2B] = (56, 204, 108)
    pal[0x2C] = (56, 180, 204)
    pal[0x2D] = (60, 60, 60)
    pal[0x2E] = (0, 0, 0)
    pal[0x2F] = (0, 0, 0)

    pal[0x30] = (236, 238, 236)
    pal[0x31] = (168, 204, 236)
    pal[0x32] = (188, 188, 236)
    pal[0x33] = (212, 178, 236)
    pal[0x34] = (236, 174, 236)
    pal[0x35] = (236, 174, 212)
    pal[0x36] = (236, 180, 176)
    pal[0x37] = (228, 196, 144)
    pal[0x38] = (204, 210, 120)
    pal[0x39] = (180, 222, 120)
    pal[0x3A] = (168, 226, 144)
    pal[0x3B] = (152, 226, 180)
    pal[0x3C] = (160, 214, 228)
    pal[0x3D] = (160, 162, 160)
    pal[0x3E] = (0, 0, 0)
    pal[0x3F] = (0, 0, 0)
    return pal

