import numpy as np

from _nes_palette import _create_palette
from cartridge import Cartridge, Mirror
from ppu_2C02_structs import PPUCtrl, PPUMask, PPUStatus, LoopyRegister


def _create_sprite(w, h):
    array = np.arange(w * h * 3, dtype=np.uint8)
    array.shape = h, w, 3
    return array


class PPU2C02:
    def __init__(self, bus):
        self.bus = bus
        self.cart: Cartridge = None

        self._control = PPUCtrl(0x00)
        self._mask = PPUMask(0x00)
        self._status = PPUStatus(0x00)
        self.nmi = False
        self._address_latch = 0x00
        self._ppu_data_buffer = 0x00

        self._vram_addr = LoopyRegister(0x0000)
        self._tram_addr = LoopyRegister(0x0000)
        self._fine_x = 0x00

        self._bg_next_tile_id = 0x00
        self._bg_next_tile_attrib = 0x00
        self._bg_next_tile_lsb = 0x00
        self._bg_next_tile_msb = 0x00

        self._bg_shifter_ptrn_lo = 0x0000
        self._bg_shifter_ptrn_hi = 0x0000
        self._bg_shifter_attrib_lo = 0x0000
        self._bg_shifter_attrib_hi = 0x0000

        self._cycle = 0
        self._scanline = 0
        self.frame_count = 0
        self.frame_complete = False

        self.name_table = [[0x00] * 1024, [0x00] * 1024]
        self.pattern_table = [[0x00] * 4096, [0x00] * 4096]
        self.palette_table = [0x00] * 32

        self.pal_screen = _create_palette()
        self.spr_pattern_table = [_create_sprite(128, 128), _create_sprite(128, 128)]
        self.spr_screen = _create_sprite(256, 240)

    def cpu_write(self, addr: int, data: int):
        data = data & 0xFF
        if addr == 0x0000:  # Control
            self._control.set_reg(data)
            self._tram_addr.nametable_x = self._control.nametable_x
            self._tram_addr.nametable_y = self._control.nametable_y

        elif addr == 0x0001:  # Mask
            self._mask.set_reg(data)

        elif addr == 0x0002:  # Status
            pass

        elif addr == 0x0003:  # OAM Address
            pass

        elif addr == 0x0004:  # OAM Data
            pass

        elif addr == 0x0005:  # Scroll
            if self._address_latch == 0:
                self._fine_x = data & 0x07
                self._tram_addr.coarse_x = data >> 3
                self._address_latch = 1
            else:
                self._tram_addr.fine_y = data & 0x07
                self._tram_addr.coarse_y = data >> 3
                self._address_latch = 0

        elif addr == 0x0006:  # PPU Address
            if self._address_latch == 0:
                self._tram_addr.reg = (self._tram_addr.reg & 0x00FF) | (data << 8)
                self._address_latch = 1
            else:
                self._tram_addr.reg = (self._tram_addr.reg & 0xFF00) | data
                self._vram_addr.reg = self._tram_addr.reg
                self._address_latch = 0

        elif addr == 0x0007:  # PPU Data
            self.ppu_write(self._vram_addr.reg, data)
            inc = 32 if self._control.increment_mode else 1
            self._vram_addr.reg += inc

    def cpu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        if addr == 0x0000:  # Control
            pass
        elif addr == 0x0001:  # Mask
            pass
        elif addr == 0x0002:  # Status
            data = (self._status.reg & 0xE0) | (self._ppu_data_buffer & 0x1F)
            self._status.vertical_blank = 0
            self._address_latch = 0
        elif addr == 0x0003:  # OAM Address
            pass
        elif addr == 0x0004:  # OAM Data
            pass
        elif addr == 0x0005:  # Scroll
            pass
        elif addr == 0x0006:  # PPU Address
            pass
        elif addr == 0x0007:  # PPU Data
            data = self._ppu_data_buffer
            self._ppu_data_buffer = self.ppu_read(self._vram_addr.reg)

            if self._vram_addr.reg >= 0x3F00:
                data = self._ppu_data_buffer
            inc = 32 if self._control.increment_mode else 1
            self._vram_addr.reg += inc
        return data

    def ppu_write(self, addr: int, data: int):
        addr &= 0x3FFF

        cart_data = self.cart.ppu_write(addr, data)
        if cart_data:
            pass
        elif 0x0000 <= addr <= 0x1FFF:
            self.pattern_table[(addr & 0x1000) >> 12][addr & 0x0FFF] = data
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            if self.cart.mirror == Mirror.VERTICAL:
                if 0x0000 <= addr <= 0x03FF:
                    self.name_table[0][addr & 0x03FF] = data
                if 0x0400 <= addr <= 0x07FF:
                    self.name_table[1][addr & 0x03FF] = data
                if 0x0800 <= addr <= 0x0BFF:
                    self.name_table[0][addr & 0x03FF] = data
                if 0x0C00 <= addr <= 0x0FFF:
                    self.name_table[1][addr & 0x03FF] = data

            elif self.cart.mirror == Mirror.HORIZONTAL:
                if 0x0000 <= addr <= 0x03FF:
                    self.name_table[0][addr & 0x03FF] = data
                if 0x0400 <= addr <= 0x07FF:
                    self.name_table[0][addr & 0x03FF] = data
                if 0x0800 <= addr <= 0x0BFF:
                    self.name_table[1][addr & 0x03FF] = data
                if 0x0C00 <= addr <= 0x0FFF:
                    self.name_table[1][addr & 0x03FF] = data

        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr == 0x0010:
                addr = 0x0000
            if addr == 0x0014:
                addr = 0x0004
            if addr == 0x0018:
                addr = 0x0008
            if addr == 0x001C:
                addr = 0x000C
            self.palette_table[addr] = data

    def ppu_read(self, addr: int, read_only=False) -> int:
        data = 0x00
        addr &= 0x3FFF

        cart_data = self.cart.ppu_read(addr)
        if cart_data is not None:
            data = cart_data
        elif 0x0000 <= addr <= 0x1FFF:
            data = self.pattern_table[(addr & 0x1000) >> 12][addr & 0x0FFF]
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            if self.cart.mirror == Mirror.VERTICAL:
                if 0x0000 <= addr <= 0x03FF:
                    data = self.name_table[0][addr & 0x3FF]
                if 0x0400 <= addr <= 0x07FF:
                    data = self.name_table[1][addr & 0x3FF]
                if 0x0800 <= addr <= 0x0BFF:
                    data = self.name_table[0][addr & 0x3FF]
                if 0x0C00 <= addr <= 0x0FFF:
                    data = self.name_table[1][addr & 0x3FF]

            elif self.cart.mirror == Mirror.HORIZONTAL:
                if 0x0000 <= addr <= 0x03FF:
                    data = self.name_table[0][addr & 0x3FF]
                if 0x0400 <= addr <= 0x07FF:
                    data = self.name_table[0][addr & 0x3FF]
                if 0x0800 <= addr <= 0x0BFF:
                    data = self.name_table[1][addr & 0x3FF]
                if 0x0C00 <= addr <= 0x0FFF:
                    data = self.name_table[1][addr & 0x3FF]

        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr == 0x0010:
                addr = 0x0000
            if addr == 0x0014:
                addr = 0x0004
            if addr == 0x0018:
                addr = 0x0008
            if addr == 0x001C:
                addr = 0x000C
            data = self.palette_table[addr]

        return data

    def connect_cartridge(self, cartridge: Cartridge):
        self.cart = cartridge

    def get_screen(self):
        return self.spr_screen

    def get_color_from_palette_ram(self, palette, pixel):
        addr = (0x3F00 + (palette << 2) + pixel)
        return self.pal_screen[self.ppu_read(addr) & 0x3F]

    def get_pattern_table(self, i, palette):
        for tile_y in range(0, 16):
            for tile_x in range(0, 16):
                offset = tile_y * 256 + tile_x * 16
                for row in range(0, 8):
                    tile_lsb = self.ppu_read(i * 0x1000 + offset + row)
                    tile_msb = self.ppu_read(i * 0x1000 + offset + row + 8)
                    for col in range(0, 8):
                        pixel = (tile_lsb & 0x01) + (tile_msb & 0x01)
                        tile_lsb >>= 1
                        tile_msb >>= 1
                        x = tile_x * 8 + (7 - col)
                        y = tile_y * 8 + row
                        color = self.get_color_from_palette_ram(palette, pixel)
                        self.spr_pattern_table[i][y, x] = color

        return self.spr_pattern_table[i]

    def get_name_table(self, i):
        return self.spr_name_table[i]

    def clock(self):
        # simplify reading (read only)
        scanline = self._scanline
        cycle = self._cycle

        # simplify reading and writing
        vram = self._vram_addr

        if -1 <= scanline < 240:

            if scanline == -1 and cycle == 1:
                self._status.vertical_blank = 0

            if 2 <= cycle < 258 or 321 <= cycle < 338:
                update_shifters(self, self._mask)

                case = (cycle - 1) % 8
                if case == 0:
                    load_background_shifters(self)
                    addr = 0x2000 | (vram.reg & 0x0FFF)
                    self._bg_next_tile_id = self.ppu_read(addr)

                elif case == 2:
                    addr = (
                            0x23C0
                            | (vram.nametable_y << 11)
                            | (vram.nametable_x << 10)
                            | ((vram.coarse_y >> 2) << 3)
                            | (vram.coarse_x >> 2)
                    )
                    self._bg_next_tile_attrib = self.ppu_read(addr)
                    if vram.coarse_y & 0x02:
                        self._bg_next_tile_attrib >>= 4
                    if vram.coarse_x & 0x02:
                        self._bg_next_tile_attrib >>= 2
                    self._bg_next_tile_attrib &= 0x03

                elif case == 4:
                    addr = (
                            (self._control.pattern_background << 12)
                            + ((self._bg_next_tile_id << 4) & 0xFFFF)
                            + (vram.fine_y + 0)
                    )
                    self._bg_next_tile_lsb = self.ppu_read(addr & 0xFFFF)

                elif case == 6:
                    addr = (
                            ((self._control.pattern_background << 12) & 0xFFFF)
                            + ((self._bg_next_tile_id << 4) & 0xFFFF)
                            + vram.fine_y + 8
                    )
                    self._bg_next_tile_msb = self.ppu_read(addr & 0xFFFF)

                elif case == 7:
                    increment_scroll_x(self._vram_addr, self._mask)

            if cycle == 256:
                increment_scroll_y(self._vram_addr, self._mask)

            if cycle == 257:
                load_background_shifters(self)
                transfer_address_x(self._vram_addr, self._tram_addr, self._mask)

            if scanline == -1 and 280 <= cycle < 305:
                transfer_address_y(self._vram_addr, self._tram_addr, self._mask)

        if scanline == 240:
            # post render scanline
            pass

        if scanline == 241 and cycle == 1:
            self._status.vertical_blank = 1

            if self._control.enable_nmi:
                self.nmi = True

        bg_pixel = 0x00
        bg_palette = 0x00

        if self._mask.render_background:
            bit_mux = 0x8000 >> self._fine_x
            p0_pixel = 1 if (self._bg_shifter_ptrn_lo & bit_mux) > 0 else 0
            p1_pixel = 1 if (self._bg_shifter_ptrn_hi & bit_mux) > 0 else 0
            bg_pixel = (p1_pixel << 1) | p0_pixel

            bg_pal0 = 1 if (self._bg_shifter_attrib_lo & bit_mux) > 0 else 0
            bg_pal1 = 1 if (self._bg_shifter_attrib_hi & bit_mux) > 0 else 0
            bg_palette = (bg_pal1 << 1) | bg_pal0

        if 0 <= scanline < 240 and 2 <= cycle < 258:
            color = self.get_color_from_palette_ram(bg_palette, bg_pixel)
            self.spr_screen[scanline, cycle - 2] = color

        self._cycle += 1
        if self._cycle >= 341:
            self._cycle = 0
            self._scanline += 1
            if self._scanline >= 261:
                self._scanline = -1
                self.frame_complete = True
                self.frame_count += 1


def increment_scroll_x(vram: LoopyRegister, mask: PPUMask):
    if mask.render_background or mask.render_sprites:
        if vram.coarse_x == 31:
            vram.coarse_x = 0
            vram.nametable_x = ~vram.nametable_x
        else:
            vram.coarse_x += 1


def increment_scroll_y(vram: LoopyRegister, mask: PPUMask):
    if mask.render_background or mask.render_sprites:
        if vram.fine_y < 7:
            vram.fine_y += 1
        else:
            vram.fine_y = 0

            if vram.coarse_y == 29:
                vram.coarse_y = 0
                vram.nametable_y = ~vram.nametable_y
            elif vram.coarse_y == 31:
                vram.coarse_y = 0
            else:
                vram.coarse_y += 1


def transfer_address_x(vram: LoopyRegister, tram: LoopyRegister, mask: PPUMask):
    if mask.render_background or mask.render_sprites:
        vram.nametable_x = tram.nametable_x
        vram.coarse_x = tram.coarse_x


def transfer_address_y(vram: LoopyRegister, tram: LoopyRegister, mask: PPUMask):
    if mask.render_background or mask.render_sprites:
        vram.fine_y = tram.fine_y
        vram.nametable_y = tram.nametable_y
        vram.coarse_y = tram.coarse_y


def load_background_shifters(ppu: PPU2C02):
    ppu._bg_shifter_ptrn_lo = (ppu._bg_shifter_ptrn_lo & 0xFF00) | ppu._bg_next_tile_lsb
    ppu._bg_shifter_ptrn_hi = (ppu._bg_shifter_ptrn_hi & 0xFF00) | ppu._bg_next_tile_msb

    tile_attrib_lo = 0xFF if ppu._bg_next_tile_attrib & 0x01 else 0x00
    ppu._bg_shifter_attrib_lo = (ppu._bg_shifter_attrib_lo & 0xFF00) | tile_attrib_lo

    tile_attrib_hi = 0xFF if ppu._bg_next_tile_attrib & 0x02 else 0x00
    ppu._bg_shifter_attrib_hi = (ppu._bg_shifter_attrib_hi & 0xFF00) | tile_attrib_hi


def update_shifters(ppu: PPU2C02, mask: PPUMask):
    if mask.render_background:
        ppu._bg_shifter_ptrn_lo <<= 1
        ppu._bg_shifter_ptrn_hi <<= 1
        ppu._bg_shifter_attrib_lo <<= 1
        ppu._bg_shifter_attrib_hi <<= 1
