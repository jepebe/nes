import numpy as np

from nes.cpu_6502 import CPU6502


class Bus:
    def __init__(self):
        self.cpu = CPU6502(self)
        #self.ppu = PPU2C02(self)
        self.cpu_ram = np.zeros(2 * 1024, dtype=np.uint8)


    def cpu_write(self, addr: int, data: np.int):
        if 0x0000 <= addr <= 0xFFFF:
            self.cpu_ram[addr] = data

    def cpu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        if 0x0000 <= addr <= 0x1FFF:
            return self.cpu_ram[addr]

        return data