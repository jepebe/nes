from typing import Union

from mappers.mapper import Mapper


#
# Source https://wiki.nesdev.com/w/index.php/RAMBO-1
#

# Tengen RAMBO-1
class Mapper064(Mapper):
    def __init__(self, prg_banks, chr_banks):
        super().__init__(prg_banks, chr_banks)
        self.prg_rom = [0, 1, 2, prg_banks - 1]
        self.current_chr_bank = 0

        self.r = 0
        self.chr_mode = 0
        self.prg_mode = 0
        self.chr_inversion = 0
        self.mirror_mode = 0  # 0: vertical; 1: horizontal

    def cpu_map_read(self, addr: int) -> Union[int, None]:
        if 0x8000 <= addr <= 0x9FFF:
            addr &= 0x1FFF
            addr += 0x2000 * self.prg_rom[0]
        elif 0xA000 <= addr <= 0xBFFF:
            addr &= 0x1FFF
            addr += 0x2000 * self.prg_rom[1]
        elif 0xC000 <= addr <= 0xDFFF:
            addr &= 0x1FFF
            addr += 0x2000 * self.prg_rom[2]
        elif 0xE000 <= addr <= 0xFFFF:
            addr &= 0x1FFF
            addr += 0x2000 * self.prg_rom[3]
        else:
            addr = None
        return addr

    def cpu_map_write(self, addr: int, data: int) -> Union[int, None]:
        addr &= 0xFFFF
        if addr & 0x01 == 0:  # Even
            if 0x8000 <= addr <= 0x9FFE:  # bank select
                self.r = data & 0xF
                self.chr_mode = (data >> 5) & 0x1
                self.prg_mode = (data >> 6) & 0x1
                self.chr_inversion = (data >> 7) & 0x1
            elif 0xA000 <= addr <= 0xBFFE:  # Mirroring
                temp = self.mirror_mode
                self.mirror_mode = data & 0x01
                if temp != self.mirror_mode:
                    print(f'mirror mode changed from: {temp} -> {self.mirror_mode}')
            elif 0xC000 <= addr <= 0xDFFE:
                print('IRQ Latching')
                pass
            elif 0xE001 <= addr <= 0xFFFF:
                print('IRQ Enable')
                pass
        else:  # Odd
            if 0x8001 <= addr <= 0x9FFF:
                if self.r == 0b0000:
                    # R0: Select 2 (K=0) or 1 (K=1) KiB CHR bank at PPU $0000 (or $1000)
                    pass
                elif self.r == 0b0001:
                    # R1: Select 2 (K=0) or 1 (K=1) KiB CHR bank at PPU $0800 (or $1800)
                    pass
                elif self.r == 0b0010:
                    # R2: Select 1 KiB CHR bank at PPU $1000-$13FF (or $0000-$03FF)
                    pass
                elif self.r == 0b0011:
                    # R3: Select 1 KiB CHR bank at PPU $1400-$17FF (or $0400-$07FF)
                    pass
                elif self.r == 0b0100:
                    # R4: Select 1 KiB CHR bank at PPU $1800-$1BFF (or $0800-$0BFF)
                    pass
                elif self.r == 0b0101:
                    # R5: Select 1 KiB CHR bank at PPU $1C00-$1FFF (or $0C00-$0FFF)
                    pass
                elif self.r == 0b0110:
                    # R6: Select 8 KiB PRG ROM bank at $8000-$9FFF (or $C000-$DFFF)
                    prg_index = 2 if self.prg_mode else 0
                    print(f'PRG swap {prg_index} := {data:02X}')
                elif self.r == 0b0111:
                    # R7: Select 8 KiB PRG ROM bank at $A000-$BFFF
                    prg_index = 1
                    print(f'PRG swap {prg_index} := {data:02X}')
                elif self.r == 0b1000:
                    # R8: If K=1, Select 1 KiB CHR bank at PPU $0400 (or $1400)
                    pass
                elif self.r == 0b1001:
                    # R9: If K=1, Select 1 KiB CHR bank at PPU $0C00 (or $1C00)
                    pass
                elif self.r == 0b1111:
                    # RF: Select 8 KiB PRG ROM bank at $C000-$DFFF (or $8000-$9FFF)
                    prg_index = 0 if self.prg_mode else 2
                    print(f'PRG swap {prg_index} := {data:02X}')
                else:
                    # print(f'Unknown mode: {self.r:04b}')
                    pass  # do nothing
                # print(f'odd {addr:016b} {self.r:04b} {self.chr_mode} {self.prg_mode} {self.chr_inversion}')
            elif 0xA001 <= addr <= 0xBFFF:
                print('Unused mode?')
                pass

        if 0x8000 <= addr <= 0xFFFF:
            pass
            # self.current_chr_bank = data & 0x03
            # self.current_prg_bank = (data >> 4) & 0x03
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
