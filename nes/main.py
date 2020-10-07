import time

import pyglet
import pyglet.gl as gl
from typing import Dict

from array_image import ArrayInterfaceImage
from nes.bus import Bus
from cartridge import Cartridge
from _opcodes_6502 import disassembler
from flags_6502 import Flags6502

WHITE = (255, 255, 255, 255)
GREEN = (0, 255, 0, 255)
RED = (255, 0, 0, 255)
YELLOW = (255, 255, 0, 255)
MONOCHROME_GREEN = (32, 180, 32, 255)


class HackerWindow(pyglet.window.Window):

    def __init__(self, title, nes: Bus, asm_map: Dict[int, str], width=800, height=500):
        super().__init__(width, height, caption=title, vsync=False)
        self.fps_display = pyglet.window.FPSDisplay(window=self)
        self.nes = nes
        self.asm_map = asm_map

        self.scale = 0.5
        gl.glScalef(self.scale, self.scale, 1.0)

        self._label = pyglet.text.Label()

        self._emulation_run = False
        self._residual_time = 0.0
        self._dirty = False
        self._selected_palette = 0x00

        self._screen_sprite = ArrayInterfaceImage(nes.ppu.spr_screen)
        self._pattern_table_0 = ArrayInterfaceImage(nes.ppu.spr_pattern_table[0])
        self._pattern_table_1 = ArrayInterfaceImage(nes.ppu.spr_pattern_table[1])

        self._spr_ptrn_tbl_0 = pyglet.sprite.Sprite(self._pattern_table_0)
        self._spr_ptrn_tbl_1 = pyglet.sprite.Sprite(self._pattern_table_1)
        self._spr_screen = pyglet.sprite.Sprite(self._screen_sprite)

        nes.ppu.get_pattern_table(0, self._selected_palette)
        nes.ppu.get_pattern_table(1, self._selected_palette)

        pyglet.clock.schedule_interval_soft(self.update, 1 / 60)

    def update(self, dt):
        if self._emulation_run:
            # if self._residual_time > 0.0:
            #     self._residual_time -= dt
            #     print(f'{self._residual_time} {dt}')
            #
            # else:
            #     self._residual_time += (1.0 / 60.0) - dt
            while True:
                self.nes.clock()
                if self.nes.ppu.frame_complete:
                    break
            self.nes.ppu.frame_complete = False
            self._dirty = True

    def xflipity(self, x, y, size=0):
        scale = self.scale
        return x // scale, self.height // scale - y // scale - size // scale

    def draw_string(self, x, y, msg, color=MONOCHROME_GREEN):
        font_size = 6 // self.scale
        x, y = self.xflipity(x, y, size=font_size)
        self._label.text = msg
        self._label.x = x
        self._label.y = y
        # self._label.font_name = 'Jetbrains Mono'
        self._label.font_name = 'C64 Pro Mono'
        self._label.font_size = font_size
        self._label.bold = True
        self._label.color = color
        self._label.draw()

    # def on_draw(self):
    #     gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    #     self.clear()
    #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    #     self.draw_ram(2, 2, 0x0000, 16, 16)
    #     self.draw_ram(2, 182, 0x8000, 16, 16)
    #     self.draw_cpu(448, 2)
    #     self.draw_code(448, 72, 26)
    #     self.draw_string(10, 370,
    #                      "SPACE = Step Instruction    R = RESET    I = IRQ    N = NMI")
    #     self.draw_string(10, 390, f'Current cycle: {self.nes.system_clock_counter}')
    #     self.fps_display.draw()

    def on_draw(self):
        # Enable alpha blending, required for image.blit.
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

        self.clear()

        nes = self.nes
        if self._dirty:
            self._dirty = False
            self._screen_sprite.dirty()
            nes.ppu.get_pattern_table(0, self._selected_palette)
            nes.ppu.get_pattern_table(1, self._selected_palette)
            self._pattern_table_0.dirty()
            self._pattern_table_1.dirty()

        self.draw_cpu(516, 2)
        self.draw_code(516, 72, 25)
        # self.draw_sprite_ids(516, 72)

        self.draw_palette(516, 338, swatch_size=7)

        # self.draw_ram(2, 2, 0x0000, 16, 16)
        # self.draw_ram(2, 182, 0xC000, 16, 16)

        self.draw_sprite(self._spr_screen, 0, 0, 2)

        self.draw_sprite(self._spr_ptrn_tbl_0, 516, 348)
        self.draw_sprite(self._spr_ptrn_tbl_1, 648, 348)

        # self.draw_name_table(0, 0)

        self.fps_display.draw()

    def draw_sprite_ids(self, x, y):
        nes = self.nes
        for i in range(26):
            spr_x = nes.ppu._oam[i * 4 + 3]
            spr_y = nes.ppu._oam[i * 4 + 0]
            id = nes.ppu._oam[i * 4 + 1]
            attribute = nes.ppu._oam[i * 4 + 1]
            spr = f'{i:02X}: ({spr_x}, {spr_y}) ID: {id:02X} AT: {attribute}'
            self.draw_string(x, y + i * 10, spr)

    def draw_name_table(self, x, y):
        table = self.nes.ppu.name_table[0]
        ptrn = self.nes.ppu.spr_pattern_table[0]
        ptrns = {}
        for id in range(16 * 16):
            sx = (id & 0x0F) << 3
            sy = ((id >> 4) & 0x0F) << 3
            view = ptrn[sy: sy + 8, sx: sx + 8]
            img = ArrayInterfaceImage(view)
            ptrns[id] = (img, pyglet.sprite.Sprite(img, 0, 0))

        for y in range(30):
            for x in range(32):
                id = table[y * 32 + x]
                p = ptrns[id]
                self.draw_sprite(p[1], x * 16, y * 16, ratio=2)

    def draw_palette(self, x, y, swatch_size=6, spacing=10):
        x, y = self.xflipity(x, y, swatch_size)
        swatch_size /= self.scale
        offset = 1 // self.scale
        rect = pyglet.shapes.Rectangle(0, 0, swatch_size, swatch_size)
        rect.x = x + self._selected_palette * (swatch_size * 4 + spacing) - offset
        rect.y = y - offset
        rect.width = swatch_size * 4 + 2 * offset
        rect.height = swatch_size + 2 * offset
        rect.color = WHITE[:3]
        rect.draw()

        for p in range(8):
            for s in range(4):
                rect.x = x + p * (swatch_size * 4 + spacing) + s * swatch_size
                rect.y = y
                rect.color = nes.ppu.get_color_from_palette_ram(p, s)
                rect.width = swatch_size
                rect.height = swatch_size
                rect.draw()

    def draw_sprite(self, sprite: pyglet.sprite.Sprite, x, y, ratio=1.0):
        gl.glPushAttrib(gl.GL_ENABLE_BIT)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

        sprite.position = self.xflipity(x, y)
        sprite.scale_x = ratio // self.scale
        sprite.scale_y = -ratio // self.scale
        sprite.draw()
        gl.glPopAttrib()

    def draw_image(self, img, x, y, ratio=1.0):
        x, y = self.xflipity(x, y, img.height * ratio)
        w = ratio * img.width // self.scale
        h = ratio * img.height // self.scale
        img.blit(x, y, width=w, height=h)

    def _color_for_flag_state(self, flag):
        return GREEN if self.nes.cpu.state.status & flag else RED

    def draw_cpu(self, x, y):
        cpu = self.nes.cpu.state

        self.draw_string(x, y, 'STATUS:')
        self.draw_string(x + 64, y, "N", self._color_for_flag_state(Flags6502.N))
        self.draw_string(x + 80, y, "V", self._color_for_flag_state(Flags6502.V))
        self.draw_string(x + 96, y, "-", self._color_for_flag_state(Flags6502.U))
        self.draw_string(x + 112, y, "B", self._color_for_flag_state(Flags6502.B))
        self.draw_string(x + 128, y, "D", self._color_for_flag_state(Flags6502.D))
        self.draw_string(x + 144, y, "I", self._color_for_flag_state(Flags6502.I))
        self.draw_string(x + 160, y, "Z", self._color_for_flag_state(Flags6502.Z))
        self.draw_string(x + 178, y, "C", self._color_for_flag_state(Flags6502.C))
        self.draw_string(x, y + 10, f'PC: ${cpu.pc & 0xffff:04X}')
        self.draw_string(x, y + 20, f'A: ${cpu.a & 0xff:02X} [{cpu.a}]')
        self.draw_string(x, y + 30, f'X: ${cpu.x & 0xff:02X} [{cpu.x}]')
        self.draw_string(x, y + 40, f'Y: ${cpu.y & 0xff:02X} [{cpu.y}]')
        self.draw_string(x, y + 50, f'Stack P: ${cpu.stkp & 0xffff:04X}')

    def draw_ram(self, x, y, addr, rows, columns):
        cpu = self.nes.cpu
        for row in range(rows):
            data = f'${addr & 0xffff:04X}:'
            for column in range(columns):
                value = cpu.cpu_read(addr)
                data += f' {value & 0xff:02X}'
                addr += 1
            self.draw_string(x, y, data)
            y += 10

    def draw_code(self, x, y, lines):
        nes_state = self.nes.cpu.state.pc
        while nes_state not in self.asm_map:
            # print(f'missing instruction {nes_state:02X}')
            # program counter already moved ahead?
            nes_state -= 1

        current_line = self.asm_map[nes_state]
        asm_lines = [current_line]

        count = lines
        current = nes_state
        while count >= 0 and current <= 0xFFFF:
            current += 1
            if current in self.asm_map:
                asm_lines.append(self.asm_map[current])
                count -= 1

        count = lines
        current = nes_state
        while count >= 0 and current >= 0x0000:
            current -= 1
            if current in self.asm_map:
                asm_lines.append(self.asm_map[current])
                count -= 1

        asm_lines = list(sorted(asm_lines))
        index = asm_lines.index(current_line)
        from_line = max(0, index - lines // 2)
        to_line = min(len(asm_lines), from_line + lines + 1)

        for line in asm_lines[from_line:to_line]:
            color = YELLOW if line == current_line else MONOCHROME_GREEN
            self.draw_string(x, y, line, color=color)
            y += 10

    def on_key_press(self, symbol, modifiers):
        pygkey = pyglet.window.key

        nes.controller[0] = 0x00
        nes.controller[0] |= 0x80 if symbol == pygkey.X else 0x00  # a or b
        nes.controller[0] |= 0x40 if symbol == pygkey.Z else 0x00  # a or b
        nes.controller[0] |= 0x20 if symbol == pygkey.A else 0x00  # select
        nes.controller[0] |= 0x10 if symbol == pygkey.S else 0x00  # start
        nes.controller[0] |= 0x08 if symbol == pygkey.UP else 0x00
        nes.controller[0] |= 0x04 if symbol == pygkey.DOWN else 0x00
        nes.controller[0] |= 0x02 if symbol == pygkey.LEFT else 0x00
        nes.controller[0] |= 0x01 if symbol == pygkey.RIGHT else 0x00

        if not self._emulation_run:
            if symbol == pygkey.C:
                while True:
                    self.nes.clock()
                    if self.nes.cpu.complete():
                        break
                while True:
                    self.nes.clock()
                    if not self.nes.cpu.complete():
                        break
                self._dirty = True

            if symbol == pygkey.F:
                while True:
                    self.nes.clock()
                    if self.nes.ppu.frame_complete:
                        break
                while True:
                    self.nes.clock()
                    if self.nes.cpu.complete():
                        break
                self.nes.ppu.frame_complete = False
                self._dirty = True

        if symbol == pygkey.SPACE:
            self._emulation_run = not self._emulation_run
            pyglet.clock.schedule_once(self.update, 0.1)

        if symbol == pygkey.R:
            self._emulation_run = False
            self.nes.reset()
            self._dirty = True

        if symbol == pygkey.P:
            self._selected_palette = (self._selected_palette + 1) & 0x07
            self._dirty = True

        if symbol in (pygkey.ESCAPE, pygkey.Q):
            pyglet.app.exit()


if __name__ == '__main__':
    nes = Bus()
    # cart = Cartridge('tests/nestest.nes')         # 000
    # cart = Cartridge('roms/donkeykong.nes')       # 000
    # cart = Cartridge('roms/smb.nes')              # 000
    # cart = Cartridge('roms/kungfu.nes')           # 000
    # cart = Cartridge('roms/kungfueu.nes')         # 000
    # cart = Cartridge('roms/balloonfight.nes')     # 000
    # cart = Cartridge('roms/ducktales.nes')        # 002
    # cart = Cartridge('roms/megaman.nes')          # 002
    # cart = Cartridge('roms/bomber_man.nes')       # 064
    # cart = Cartridge('roms/klax.nes')             # 064
    # cart = Cartridge('roms/galaga.nes')           # 064
    # cart = Cartridge('roms/smb2.nes')             # 004
    # cart = Cartridge('roms/smb3.nes')             # 004
    # cart = Cartridge('roms/kirbysadventure.nes')  # 004

    cart = Cartridge('tests/test_roms/test_cpu_exec_space_ppuio.nes')  #
    # cart = Cartridge('tests/test_roms/test_cpu_exec_space_apu.nes')  #
    # cart = Cartridge('tests/test_roms/1.Branch_Basics.nes')  # passed
    # cart = Cartridge('tests/test_roms/2.Backward_Branch.nes')  # passed
    # cart = Cartridge('tests/test_roms/3.Forward_Branch.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/01-implied.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/02-immediate.nes')  # failed
    # cart = Cartridge('tests/test_roms/instructions/03-zero_page.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/04-zp_xy.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/05-absolute.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/06-abs_xy.nes')  # failed
    # cart = Cartridge('tests/test_roms/instructions/07-ind_x.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/08-ind_y.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/09-branches.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/10-stack.nes')  # passed
    # cart = Cartridge('tests/test_roms/instructions/11-special.nes')  # failed -> bug in test?
    # cart = Cartridge('tests/test_roms/instructions/all_instrs.nes-kopi')  # mapper 1
    # cart = Cartridge('tests/test_roms/instructions/official_only.nes')  # mapper 1
    nes.insert_cartridge(cart)

    asm_map = disassembler(nes, 0x0000, 0xffff)
    nes.reset()

    # ops = 0
    # now = time.time()
    # while True:
    #     nes.clock()
    #     ops += 1
    #     if nes.ppu.frame_count >= 22:
    #         break
    # diff = time.time() - now
    # print(f'{diff} {ops / diff}')
    # print(f'Frame count: {nes.ppu.frame_count} FPS: {nes.ppu.frame_count / diff}')
    window = HackerWindow(cart.filename, nes, asm_map)
    pyglet.app.run()
