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

        self.controller_state = [0x00, 0x00]
        self.controller = [0x00, 0x00]

        self._dma_page = 0x00
        self._dma_addr = 0x00
        self._dma_data = 0x00
        self._dma_transfer = False
        self._dma_dummy = True

    def cpu_write(self, addr: int, data: int):
        if self.cart.cpu_write(addr, data) is not None:
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            self.cpu_ram[addr & 0x7FF] = data
        elif 0x2000 <= addr <= 0x3FFF:
            self.ppu.cpu_write(addr & 0x0007, data)
        elif addr == 0x4014:
            self._dma_page = data & 0xFF
            self._dma_addr = 0x00
            self._dma_transfer = True
        elif 0x4016 == addr:
            if data & 0x01 == 1:  # joypad poll (latch)
                # if self.controller[0] != 0:
                #     print(f'latching controller with {self.controller[0]}')
                self.controller_state[0] = self.controller[0]
                self.controller_state[1] = self.controller[1]
            else:
                # joypad/controller unlatch
                self.controller[0] = 0x00
                self.controller[1] = 0x00
        elif addr == 0x4017:
            pass

    def cpu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        if (cart_data := self.cart.cpu_read(addr)) is not None:
            data = cart_data
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.cpu_ram[addr & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF:
            data = self.ppu.cpu_read(addr & 0x0007, read_only=read_only)
        elif addr == 0x4016:
            # return more bits for other devices
            # Joy pad 1 read
            data = 1 if (self.controller_state[0] & 0x80) > 0 else 0
            self.controller_state[0] <<= 1
        elif addr == 0x4017:
            # Joy pad 2 read
            data = 1 if (self.controller_state[1] & 0x80) > 0 else 0
            self.controller_state[1] <<= 1

        return data

    def cpu_read_2(self, addr: int, read_only=False) -> int:
        data = (0x00, 0x00)

        if (cart_data := self.cart.cpu_read_2(addr)) is not None:
            data = cart_data
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.cpu_ram[addr & 0x07FF], self.cpu_ram[(addr + 1) & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF:
            a = self.ppu.cpu_read(addr & 0x0007, read_only=read_only)
            b = self.ppu.cpu_read((addr + 1) & 0x0007, read_only=read_only)
            data = a, b
        elif 0x4016 <= addr <= 0x4017:
            print('reading 2 bytes from controller!!!')

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
            if self._dma_transfer:
                self._do_dma_transfer()
            else:
                self.cpu.clock()

        if self.ppu.nmi:
            self.ppu.nmi = False
            self.cpu.nmi()

        self.system_clock_counter += 1

    def _do_dma_transfer(self):
        if self._dma_dummy:
            if self.system_clock_counter % 2 == 1:
                self._dma_dummy = False
        else:
            if self.system_clock_counter % 2 == 0:
                addr = (self._dma_page << 8) | self._dma_addr
                self._dma_data = self.cpu_read(addr)
            else:
                self.ppu._oam[self._dma_addr] = self._dma_data
                self._dma_addr += 1

                if self._dma_addr & 0xFF == 0x00:
                    self._dma_transfer = False
                    self._dma_dummy = True
