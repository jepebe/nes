import pyglet
import pyglet.gl as gl
from typing import Dict

from nes.bus import Bus
from _opcodes_6502 import disassembler
from flags_6502 import FLAGS6502

WHITE = (255, 255, 255, 255)
GREEN = (0, 255, 0, 255)
RED = (255, 0, 0, 255)
YELLOW = (255, 255, 0, 255)
MONOCHROME_GREEN = (32, 180, 32, 255)


class HackerWindow(pyglet.window.Window):

    def __init__(self, bus: Bus, asm_map: Dict[int, str], width=720, height=480):
        super().__init__(width, height, vsync=False)
        self.fps_display = pyglet.window.FPSDisplay(window=self)
        self.bus = bus
        self.asm_map = asm_map

        self.scale_x = 0.2
        self.scale_y = 0.2
        gl.glScalef(self.scale_x, self.scale_y, 1.0)
        self._label = pyglet.text.Label()

        # pyglet.clock.schedule_interval(self.update, 1 / 100)
        # pyglet.clock.schedule(self.update)
        # pyglet.clock.set_fps_limit(128)

    def update(self, dt):
        pass

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
        self.fps_display.draw()

    def _color_for_flag_state(self, flag):
        return GREEN if self.bus.cpu.status & flag.value else RED

    def draw_cpu(self, x, y):
        cpu = self.bus.cpu

        self.draw_string(x, y, 'STATUS:')
        self.draw_string(x + 64, y, "N", self._color_for_flag_state(FLAGS6502.N))
        self.draw_string(x + 80, y, "V", self._color_for_flag_state(FLAGS6502.V))
        self.draw_string(x + 96, y, "-", self._color_for_flag_state(FLAGS6502.U))
        self.draw_string(x + 112, y, "B", self._color_for_flag_state(FLAGS6502.B))
        self.draw_string(x + 128, y, "D", self._color_for_flag_state(FLAGS6502.D))
        self.draw_string(x + 144, y, "I", self._color_for_flag_state(FLAGS6502.I))
        self.draw_string(x + 160, y, "Z", self._color_for_flag_state(FLAGS6502.Z))
        self.draw_string(x + 178, y, "C", self._color_for_flag_state(FLAGS6502.C))
        self.draw_string(x, y + 10, f'PC: ${cpu.pc & 0xffff:04X}')
        self.draw_string(x, y + 20, f'A: ${cpu.a & 0xff:02X} [{cpu.a}]')
        self.draw_string(x, y + 30, f'X: ${cpu.x & 0xff:02X} [{cpu.x}]')
        self.draw_string(x, y + 40, f'Y: ${cpu.y & 0xff:02X} [{cpu.y}]')
        self.draw_string(x, y + 50, f'Stack P: ${cpu.stkp & 0xffff:04X}')

    def draw_ram(self, x, y, addr, rows, columns):
        cpu = self.bus.cpu
        for row in range(rows):
            data = f'${addr & 0xffff:04X}:'
            for column in range(columns):
                value = cpu.cpu_read(addr)
                data += f' {value & 0xff:02X}'
                addr += 1
            self.draw_string(x, y, data)
            y += 10

    def draw_code(self, x, y, lines):
        current_line = self.asm_map[self.bus.cpu.pc]
        asm_lines = [current_line]

        count = lines
        current = self.bus.cpu.pc
        while count >= 0 and current <= 0xFFFF:
            current += 1
            if current in self.asm_map:
                asm_lines.append(self.asm_map[current])
                count -= 1

        count = lines
        current = self.bus.cpu.pc
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
        if symbol == pyglet.window.key.SPACE:
            while True:
                self.bus.cpu.clock()
                if self.bus.cpu.complete():
                    break

        if symbol == pyglet.window.key.R:
            self.bus.cpu.reset()

        if symbol == pyglet.window.key.I:
            self.bus.cpu.irq()

        if symbol == pyglet.window.key.N:
            self.bus.cpu.nmi()


if __name__ == '__main__':
    bus = Bus()
    """
        *= $8000
        LDX  # 10
        STX $0000
        LDX  # 3
        STX $0001
        LDY $0000
        LDA  # 0
        CLC
        loop
        ADC $0001
        DEY
        BNE
        loop
        STA $0002
        NOP
        NOP
        NOP
    """
    prg = [0xA2, 0x0A, 0x8E, 0x00, 0x00, 0xA2, 0x03, 0x8E, 0x01, 0x00, 0xAC, 0x00, 0x00,
           0xA9, 0x00, 0x18, 0x6D, 0x01, 0x00, 0x88, 0xD0, 0xFA, 0x8D, 0x02, 0x00, 0xEA,
           0xEA, 0xEA]
    bus.cpu_ram[0x8000:0x8000 + len(prg)] = prg
    bus.cpu_ram[0xFFFC:0xFFFE] = [0x00, 0x80]  # Reset vector
    bus.cpu.reset()

    asm_map = disassembler(bus, 0x0000, 0xffff)
    window = HackerWindow(bus, asm_map)

    pyglet.app.run()
