from cpu_6502 import CPU6502
from ppu_2C02 import PPU2C02
from cartridge import Cartridge


class Bus:
    def __init__(self):
        self.cpu = CPU6502(self)
        self.ppu = PPU2C02(self)
        self.cart: Cartridge = None
        self.cpu_ram = [0x00] * 2048
        self.system_clock_counter = 0

    def cpu_write(self, addr: int, data: int):
        if 0x8000 <= addr <= 0xFFFF:
            self.cart.cpu_write(addr, data)
        elif 0x0000 <= addr <= 0x1FFF:
            self.cpu_ram[addr & 0x7FF] = data
        elif 0x2000 <= addr <= 0x3FFF:
            self.ppu.cpu_write(addr & 0x0007, data)

    def cpu_read(self, addr: int, read_only=False) -> int:
        data = 0x00

        if 0x8000 <= addr <= 0xFFFF:
            data = self.cart.cpu_read(addr)
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.cpu_ram[addr & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF:
            data = self.ppu.cpu_read(addr & 0x0007, read_only=read_only)

        return data

    def cpu_read_2(self, addr: int, read_only=False) -> int:
        data = (0x00, 0x00)

        if 0x8000 <= addr <= 0xFFFF:
            data = self.cart.cpu_read_2(addr)
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.cpu_ram[addr & 0x07FF], self.cpu_ram[(addr + 1) & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF:
            a = self.ppu.cpu_read(addr & 0x0007, read_only=read_only)
            b = self.ppu.cpu_read((addr + 1) & 0x0007, read_only=read_only)
            data = a, b

        return data

    def insert_cartridge(self, cartridge: Cartridge):
        self.cart = cartridge
        self.ppu.connect_cartridge(cartridge)

    def reset(self):
        self.cpu.reset()
        self.system_clock_counter = 0

    def clock(self):
        self.ppu.clock()

        if self.system_clock_counter % 3 == 0:
            self.cpu.clock()

        if self.ppu.nmi:
            self.ppu.nmi = False
            self.cpu.nmi()

        self.system_clock_counter += 1
