from typing import Dict

import pxng
from pxng.keys import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_SPACE, KEY_ESCAPE
from pxng.keys import KEY_P, KEY_Q, KEY_C, KEY_F, KEY_X, KEY_Z, KEY_A, KEY_S

from monitor import draw_cpu, draw_code, draw_sprite_ids, draw_ram, draw_palette
from nes.bus import Bus
from cartridge import Cartridge
from _opcodes_6502 import disassembler


class HackerWindow(pxng.Window):

    def __init__(self, title, nes: Bus, asm_map: Dict[int, str]):
        super(HackerWindow, self).__init__(800, 500, title, scale=1, vsync=False)
        self.set_update_handler(self.draw_screen)
        self.nes: Bus = nes
        self.asm_map = asm_map

        self._emulation_run = False
        self._residual_time = 0.0
        self._dirty = False
        self._selected_palette = 0x00

        self._spr_ptrn_tbl_0 = pxng.Sprite(nes.ppu.spr_pattern_table[0])
        self._spr_ptrn_tbl_1 = pxng.Sprite(nes.ppu.spr_pattern_table[1])
        self._spr_screen = pxng.Sprite(nes.ppu.spr_screen)

    def draw_screen(self, window: pxng.Window):
        self.handle_input()

        if self._emulation_run:
            self.advance_emulator()

        if self._dirty:
            nes.ppu.get_pattern_table(0, self._selected_palette)
            nes.ppu.get_pattern_table(1, self._selected_palette)
            self._spr_screen.update()
            self._spr_ptrn_tbl_0.update()
            self._spr_ptrn_tbl_1.update()
            self._dirty = False

        draw_cpu(self, 516, 2)
        draw_code(self, 516, 72, 25)
        # draw_sprite_ids(self, 516, 72)
        # draw_ram(self, 2, 2, 0x0000, 16, 16)
        # draw_ram(self, 2, 182, 0xC000, 16, 16)
        draw_palette(self, 516, 338, selected=self._selected_palette, swatch_size=7)

        self.draw_sprite(516, 348, self._spr_ptrn_tbl_0)
        self.draw_sprite(648, 348, self._spr_ptrn_tbl_1)
        self.draw_sprite(0, 0, self._spr_screen, scale=2)

    def handle_input(self):
        nes = self.nes
        key_state = self.key_state

        nes.controller[0] = 0x00
        nes.controller[0] |= 0x80 if key_state(KEY_X).held else 0x00  # a or b
        nes.controller[0] |= 0x40 if key_state(KEY_Z).held else 0x00  # a or b
        nes.controller[0] |= 0x20 if key_state(KEY_A).held else 0x00  # select
        nes.controller[0] |= 0x10 if key_state(KEY_S).held else 0x00  # start
        nes.controller[0] |= 0x08 if key_state(KEY_UP).held else 0x00
        nes.controller[0] |= 0x04 if key_state(KEY_DOWN).held else 0x00
        nes.controller[0] |= 0x02 if key_state(KEY_LEFT).held else 0x00
        nes.controller[0] |= 0x01 if key_state(KEY_RIGHT).held else 0x00

        if key_state(KEY_P).pressed:
            self._selected_palette = (self._selected_palette + 1) & 0x07
            self._dirty = True

        if key_state(KEY_Q).pressed or key_state(KEY_ESCAPE).pressed:
            self.close_window()

        if key_state(KEY_SPACE).pressed:
            self._emulation_run = not self._emulation_run

        if not self._emulation_run:
            if key_state(KEY_C).pressed:
                while True:
                    self.nes.clock()
                    if self.nes.cpu.complete():
                        break
                while True:
                    self.nes.clock()
                    if not self.nes.cpu.complete():
                        break
                self._dirty = True

            if key_state(KEY_F).pressed:
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

    def advance_emulator(self):
        while True:
            self.nes.clock()
            if self.nes.ppu.frame_complete:
                break
        self.nes.ppu.frame_complete = False
        self._dirty = True

    # def update(self, dt):
    #     if self._emulation_run:
    #         # if self._residual_time > 0.0:
    #         #     self._residual_time -= dt
    #         #     print(f'{self._residual_time} {dt}')
    #         #
    #         # else:
    #         #     self._residual_time += (1.0 / 60.0) - dt
    #         while True:
    #             self.nes.clock()
    #             if self.nes.ppu.frame_complete:
    #                 break
    #         self.nes.ppu.frame_complete = False
    #         self._dirty = True
    #

    # def draw_name_table(self, x, y):
    #     table = self.nes.ppu.name_table[0]
    #     ptrn = self.nes.ppu.spr_pattern_table[0]
    #     ptrns = {}
    #     for id in range(16 * 16):
    #         sx = (id & 0x0F) << 3
    #         sy = ((id >> 4) & 0x0F) << 3
    #         view = ptrn[sy: sy + 8, sx: sx + 8]
    #         img = ArrayInterfaceImage(view)
    #         ptrns[id] = (img, pyglet.sprite.Sprite(img, 0, 0))
    #
    #     for y in range(30):
    #         for x in range(32):
    #             id = table[y * 32 + x]
    #             p = ptrns[id]
    #             self.draw_sprite(p[1], x * 16, y * 16, ratio=2)
    #


# # def on_draw(self):
# #     gl.glClearColor(0.0, 0.0, 0.0, 1.0)
# #     self.clear()
# #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
# #     gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
# #     self.draw_ram(2, 2, 0x0000, 16, 16)
# #     self.draw_ram(2, 182, 0x8000, 16, 16)
# #     self.draw_cpu(448, 2)
# #     self.draw_code(448, 72, 26)
# #     self.draw_string(10, 370,
# #                      "SPACE = Step Instruction    R = RESET    I = IRQ    N = NMI")
# #     self.draw_string(10, 390, f'Current cycle: {self.nes.system_clock_counter}')
# #     self.fps_display.draw()
#

if __name__ == '__main__':
    nes = Bus()
    # cart = Cartridge('tests/nestest.nes')         # 000
    cart = Cartridge('roms/donkeykong.nes')  # 000
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

    # cart = Cartridge('tests/test_roms/test_cpu_exec_space_ppuio.nes')  #
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
    window.start_event_loop()
