from typing import Union

from mappers.mapper import Mapper


class Mapper002(Mapper):
    def __init__(self, prg_banks, chr_banks):
        super().__init__(prg_banks, chr_banks)
        self.current_prg_bank = 0

    def cpu_map_read(self, addr: int) -> Union[int, None]:
        if 0x8000 <= addr <= 0xBFFF:
            addr &= 0x3FFF
            addr += 0x4000 * self.current_prg_bank
            return addr
        elif 0xC000 <= addr <= 0xFFFF:
            addr &= 0x3FFF
            addr += 0x4000 * (self.prg_banks - 1)
            return addr
        return None

    def cpu_map_write(self, addr: int, data: int) -> Union[int, None]:
        if 0x8000 <= addr <= 0xFFFF:
            self.current_prg_bank = data & 0x0F
        return None

    def ppu_map_read(self, addr: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            return addr
        return None

    def ppu_map_write(self, addr: int, data: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            if self.chr_banks == 0:
                return addr
        return None
