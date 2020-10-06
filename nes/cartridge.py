from enum import Enum
from io import SEEK_CUR
from typing import Union

from mapper import Mapper000


class NesHeader:
    def __init__(self):
        self.name = None
        self.prg_rom_chunks = None
        self.chr_rom_chunks = None
        self.mapper1 = None
        self.mapper2 = None
        self.prg_ram_size = None
        self.tv_system1 = None
        self.tv_system2 = None
        self.unused = None

    @classmethod
    def create_header(cls, f):
        header = NesHeader()
        header.name = f.read(4)
        header.prg_rom_chunks = f.read(1)[0] & 0xff
        header.chr_rom_chunks = f.read(1)[0] & 0xff
        header.mapper1 = f.read(1)[0] & 0xff
        header.mapper2 = f.read(1)[0] & 0xff
        header.prg_ram_size = f.read(1)[0] & 0xff
        header.tv_system1 = f.read(1)[0] & 0xff
        header.tv_system2 = f.read(1)[0] & 0xff
        header.unused = f.read(5)
        return header


MAPPERS = {
    0: Mapper000
}


class Mirror(Enum):
    HORIZONTAL = 0x00
    VERTICAL = 0x01
    ONESCREEN_LO = 0x02
    ONESCREEN_HI = 0x03


class Cartridge:

    def __init__(self, filename):
        self.filename = filename

        self.prg_memory = None
        self.chr_memory = None
        self.mapper_id = 0x00
        self.mirror = Mirror.HORIZONTAL
        self.prg_banks = 0x00
        self.chr_banks = 0x00
        self.mapper = None

        self.read_cartridge()

    def read_cartridge(self):
        with open(self.filename, 'rb') as f:
            header = NesHeader.create_header(f)
            if header.mapper1 & 0x04:
                print('skipping training data')
                f.seek(512, SEEK_CUR)

            self.mapper_id = ((header.mapper2 >> 4) << 4) | (header.mapper1 >> 4)
            self.mirror = Mirror(header.mapper1 & 0x01)
            file_type = 1

            if file_type == 0:
                pass
            elif file_type == 1:
                self.prg_banks = header.prg_rom_chunks
                prg_size = self.prg_banks * 16384
                data = f.read(prg_size)
                self.prg_memory = [int(b) for b in data]

                self.chr_banks = header.chr_rom_chunks
                chr_size = self.chr_banks * 8192
                data = f.read(chr_size)
                self.chr_memory = [int(b) for b in data]
            elif file_type == 2:
                pass

            self.mapper = MAPPERS[self.mapper_id](self.prg_banks, self.chr_banks)

    def cpu_write(self, addr: int, data: int):
        mapped_addr = self.mapper.cpu_map_write(addr)
        self.prg_memory[mapped_addr] = data

    def cpu_read(self, addr: int, read_only=False) -> int:
        return self.prg_memory[self.mapper.cpu_map_read(addr)]
        # return self.prg_memory[self.mapper.cpu_map[addr]]

    def cpu_read_2(self, addr: int, read_only=False) -> (int, int):
        # return self.prg_memory[self.mapper.cpu_map_read(addr)]
        addr1 = self.mapper.cpu_map[addr]
        addr2 = self.mapper.cpu_map[addr + 1]
        return self.prg_memory[addr1], self.prg_memory[addr2]

    def ppu_write(self, addr: int, data: int) -> bool:
        if (map_addr := self.mapper.ppu_map_write(addr)) is not None:
            self.chr_memory[map_addr] = data
            return True
        return False

    def ppu_read(self, addr: int, read_only=False) -> Union[None, int]:
        if (map_addr := self.mapper.ppu_map_read(addr)) is not None:
            return self.chr_memory[map_addr]
        return None
