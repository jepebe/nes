import time

import pyglet
import pyglet.gl as gl
from typing import Dict

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

    def __init__(self, nes: Bus, asm_map: Dict[int, str], width=720, height=480):
        super().__init__(width, height, vsync=False)
        self.fps_display = pyglet.window.FPSDisplay(window=self)
        self.nes = nes
        self.asm_map = asm_map

        self.scale_x = 0.2
        self.scale_y = 0.2
        gl.glScalef(self.scale_x, self.scale_y, 1.0)
        self._label = pyglet.text.Label()

        self._emulation_run = False
        self._residual_time = 0.0
        # pyglet.clock.schedule_interval(self.update, 1 / 100)
        # pyglet.clock.schedule(self.update)
        # pyglet.clock.set_fps_limit(128)

    def update(self, dt):
        if self._emulation_run:
            if self._residual_time > 0.0:
                self._residual_time -= dt

            else:
                self._residual_time += (1.0 / 60.0) - dt
                while True:
                    self.nes.clock()
                    if self.nes.ppu.frame_complete:
                        break
                self.nes.ppu.frame_complete = False
            pyglet.clock.schedule_once(self.update, 0)

    def flipity(self, y, size=0):
        return self.height // self.scale_y - y - size

    def draw_string(self, x, y, msg, color=MONOCHROME_GREEN):
        font_size = 30
        self._label.text = msg
        self._label.x = x // self.scale_x
        self._label.y = self.flipity(y // self.scale_y, size=font_size)
        self._label.font_name = 'Jetbrains Mono'
        self._label.font_name = 'C64 Pro Mono'
        self._label.font_size = font_size
        self._label.bold = True
        self._label.color = color
        self._label.draw()

    def on_draw(self):
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        self.clear()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        self.draw_ram(2, 2, 0x0000, 16, 16)
        self.draw_ram(2, 182, 0x8000, 16, 16)
        self.draw_cpu(448, 2)
        self.draw_code(448, 72, 26)
        self.draw_string(10, 370,
                         "SPACE = Step Instruction    R = RESET    I = IRQ    N = NMI")
        self.draw_string(10, 390, f'Current cycle: {self.nes.system_clock_counter}')
        self.fps_display.draw()

    def _color_for_flag_state(self, flag):
        return GREEN if self.nes.cpu.status & flag else RED

    def draw_cpu(self, x, y):
        cpu = self.nes.cpu

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
        if not self.nes.cpu.pc in self.asm_map:
            print(f'missing instruction {self.nes.cpu.pc}')
        else:
            current_line = self.asm_map[self.nes.cpu.pc]
            asm_lines = [current_line]

            count = lines
            current = self.nes.cpu.pc
            while count >= 0 and current <= 0xFFFF:
                current += 1
                if current in self.asm_map:
                    asm_lines.append(self.asm_map[current])
                    count -= 1

            count = lines
            current = self.nes.cpu.pc
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
        if not self._emulation_run:
            if symbol == pyglet.window.key.C:
                while True:
                    self.nes.clock()
                    if self.nes.cpu.complete():
                        break
                while True:
                    self.nes.clock()
                    if not self.nes.cpu.complete():
                        break

            if symbol == pyglet.window.key.F:
                while True:
                    self.nes.clock()
                    if self.nes.ppu.frame_complete:
                        break
                while True:
                    self.nes.clock()
                    if self.nes.cpu.complete():
                        break
                self.nes.ppu.frame_complete = False

        if symbol == pyglet.window.key.SPACE:
            self._emulation_run = not self._emulation_run
            pyglet.clock.schedule_once(self.update, 0)

        if symbol == pyglet.window.key.R:
            self.nes.cpu.reset()



if __name__ == '__main__':
    nes = Bus()
    cart = Cartridge('tests/nestest.nes')
    nes.insert_cartridge(cart)

    asm_map = disassembler(nes, 0x0000, 0xffff)
    nes.reset()

    # ops = 0
    # now = time.time()
    # while True:
    #     bus.clock()
    #     ops += 1
    #     if bus.ppu.frame_count >= 22:
    #         break
    # diff = time.time() - now
    # print(f'{diff} {ops / diff}')
    # print(f'Frame count: {bus.ppu.frame_count} FPS: {bus.ppu.frame_count / diff}')
    window = HackerWindow(nes, asm_map)
    pyglet.app.run()
