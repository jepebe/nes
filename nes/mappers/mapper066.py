from typing import Union

from mappers.mapper import Mapper


class Mapper066(Mapper):
    def __init__(self, prg_banks, chr_banks):
        super().__init__(prg_banks, chr_banks)

        self.current_prg_bank = 0
        self.current_chr_bank = 0

    def cpu_map_read(self, addr: int) -> Union[int, None]:
        if 0x8000 <= addr <= 0xFFFF:
            addr &= 0x7FFF
            addr += 0x8000 * self.current_prg_bank
            return addr
        return None

    def cpu_map_write(self, addr: int, data: int) -> Union[int, None]:
        if 0x8000 <= addr <= 0xFFFF:
            self.current_chr_bank = data & 0x03
            self.current_prg_bank = (data >> 4) & 0x03
        return None

    def ppu_map_read(self, addr: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            if self.chr_banks > 0:
                addr = 0x2000 * self.current_chr_bank + addr
            return addr
        return None

    def ppu_map_write(self, addr: int, data: int) -> Union[int, None]:
        if 0x0000 <= addr <= 0x1FFF:
            if self.chr_banks > 0:
                addr = 0x2000 * self.current_chr_bank + addr
            return addr
        return None
