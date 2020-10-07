from typing import Union


class Mapper:
    def __init__(self, prg_banks, chr_banks):
        self.prg_banks = prg_banks
        self.chr_banks = chr_banks

    def cpu_map_read(self, addr: int) -> Union[int, None]: pass

    def cpu_map_write(self, addr: int, data: int) -> Union[int, None]: pass

    def ppu_map_read(self, addr: int) -> Union[int, None]: pass

    def ppu_map_write(self, addr: int, data: int) -> Union[int, None]: pass











