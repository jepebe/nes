from enum import Enum
from io import SEEK_CUR
from typing import Union

from mappers import MAPPERS


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

    def cart_format(self):
        cartridge_type = 'Unknown'
        if self.name == b'NES\x1A':
            cartridge_type = 'iNES'

        if cartridge_type == 'iNES' and (self.mapper2 & 0x0C) == 0x08:
            cartridge_type = 'NES20'
        return cartridge_type


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
        self._mapped_read_addr = None

        self.read_cartridge()

    def read_cartridge(self):
        with open(self.filename, 'rb') as f:
            header = NesHeader.create_header(f)
            self.mapper_id = ((header.mapper2 >> 4) << 4) | (header.mapper1 >> 4)
            self.mirror = Mirror(header.mapper1 & 0x01)

            print(f'Cartridge: {self.filename}')
            print(f'Type: {header.cart_format()}')
            print(f'Mapper ID: {self.mapper_id:03d}')
            print(f'Scrolling mode: {self.mirror.name}')
            print(f'PRG banks: {header.prg_rom_chunks}')
            print(f'CHR banks: {header.chr_rom_chunks}')

            # if (header.tv_system2 >> 4) & 0x01:
            if (header.mapper1 >> 1) & 0x01:
                print(f'PRG RAM size: {header.prg_ram_size}')

            if header.mapper1 & 0x04:
                print('skipping training data')
                f.seek(512, SEEK_CUR)

            file_type = 1

            if file_type == 0:
                pass
            elif file_type == 1:
                self.prg_banks = header.prg_rom_chunks
                prg_size = self.prg_banks * 16384
                print(f'PRG ROM size: {prg_size}')
                data = f.read(prg_size)
                self.prg_memory = [int(b) for b in data]

                self.chr_banks = header.chr_rom_chunks
                if self.chr_banks == 0:
                    print(f'No CHR ROM creating CHR RAM @ 8192 bytes')
                    self.chr_memory = [0x00] * 8192
                else:
                    chr_size = self.chr_banks * 8192
                    print(f'CHR ROM size: {chr_size}')
                    data = f.read(chr_size)
                    self.chr_memory = [int(b) for b in data]
            elif file_type == 2:
                pass

            self.mapper = MAPPERS[self.mapper_id](self.prg_banks, self.chr_banks)

    def cpu_write(self, addr: int, data: int):
        mapped_addr = self.mapper.cpu_map_write(addr, data)
        if mapped_addr is not None:
            self.prg_memory[mapped_addr] = data

    def cpu_read(self, addr: int, read_only=False) -> Union[int, None]:
        mapped_addr = self.mapper.cpu_map_read(addr)
        if mapped_addr is not None:
            return self.prg_memory[mapped_addr]
        return None

    def cpu_read_2(self, addr: int, read_only=False) -> (int, int):
        addr1 = self.mapper.cpu_map_read(addr)
        addr2 = self.mapper.cpu_map_read(addr + 1)
        if addr1 is not None and addr2 is not None:
            return self.prg_memory[addr1], self.prg_memory[addr2]
        return None

    def ppu_write(self, addr: int, data: int) -> bool:
        map_addr = self.mapper.ppu_map_write(addr, data)
        if map_addr is not None:
            self.chr_memory[map_addr] = data
            return True
        return False

    def ppu_read(self, addr: int) -> Union[int, None]:
        mapped_addr = self.mapper.ppu_map_read(addr)
        return self.chr_memory[mapped_addr] if mapped_addr else None

