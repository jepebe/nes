from typing import Union


class Mapper:
    def __init__(self, prg_banks, chr_banks):
        self.prg_banks = prg_banks
        self.chr_banks = chr_banks

    def cpu_map_read(self, addr: int) -> Union[int, None]: pass

    def cpu_map_write(self, addr: int) -> Union[int, None]: pass

    def ppu_map_read(self, addr: int) -> Union[int, None]: pass

    def ppu_map_write(self, addr: int) -> Union[int, None]: pass


class Mapper000(Mapper):
    def __init__(self, prg_banks, chr_banks):
        super().__init__(prg_banks, chr_banks)
        self.cpu_map = {}
        for addr in range(0x8000, 0xFFFF + 1):
            if self.prg_banks > 1:
                map_addr = addr & 0x7FFF
            else:
                map_addr = addr & 0x3FFF
            self.cpu_map[addr] = map_addr

    def cpu_map_read(self, addr: int) -> int:
        return self.cpu_map.get(addr)

    def cpu_map_write(self, addr: int) -> int:
        return self.cpu_map.get(addr)

    def ppu_map_read(self, addr: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            return addr
        return None

    def ppu_map_write(self, addr: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            if self.chr_banks == 0:
                print(f'writing to cartridge RAM? Mapper000')
                return addr

        return None



