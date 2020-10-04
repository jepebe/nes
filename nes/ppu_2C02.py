from cartridge import Cartridge


class PPU2C02:
    def __init__(self, bus):
        self.bus = bus
        self.cart: Cartridge = None

        self._cycle = 0
        self._scanline = 0
        self.frame_count = 0
        self.frame_complete = False

        self.name_table = [[0x00] * 1024, [0x00] * 1024]
        self.palette_table = [0x00] * 32

    def cpu_write(self, addr: int, data: int):
        if addr == 0x0000:  # Control
            pass
        elif addr == 0x0001:  # Mask
            pass
        elif addr == 0x0002:  # Status
            pass
        elif addr == 0x0003:  # OAM Address
            pass
        elif addr == 0x0004:  # OAM Data
            pass
        elif addr == 0x0005:  # Scroll
            pass
        elif addr == 0x0006:  # PPU Address
            pass
        elif addr == 0x0007:  # PPU Data
            pass

    def cpu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        if addr == 0x0000:  # Control
            pass
        elif addr == 0x0001:  # Mask
            pass
        elif addr == 0x0002:  # Status
            pass
        elif addr == 0x0003:  # OAM Address
            pass
        elif addr == 0x0004:  # OAM Data
            pass
        elif addr == 0x0005:  # Scroll
            pass
        elif addr == 0x0006:  # PPU Address
            pass
        elif addr == 0x0007:  # PPU Data
            pass
        return data

    def ppu_write(self, addr: int, data: int):
        addr &= 0x3FFF
        if self.cart.ppu_write(addr, data):
            pass

    def ppu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        addr &= 0x3FFF

        cart_data = self.cart.ppu_read(addr)
        if cart_data is not None:
            data = cart_data
        return data

    def connect_cartridge(self, cartridge: Cartridge):
        self.cart = cartridge

    def clock(self):
        self._cycle += 1
        if self._cycle >= 341:
            self._cycle = 0
            self._scanline += 1
            if self._scanline >= 261:
                self._scanline = -1
                self.frame_complete = True
                self.frame_count += 1
