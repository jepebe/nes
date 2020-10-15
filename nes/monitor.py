from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import HackerWindow
# ^ Hack to avoid cyclic import exception during typing

from pxng.colors import GREEN, RED, YELLOW, WHITE
from flags_6502 import Flags6502

MONOCHROME_GREEN = (0.125, 0.7, 0.125, 1)


def _flag_color(flag, status):
    return GREEN if status & flag else RED


def draw_cpu(window: HackerWindow, x, y):
    cpu = window.nes.cpu.state
    status = cpu.status
    tint = window.tint
    window.tint = MONOCHROME_GREEN
    window.draw_text(x, y, 'STATUS:')
    window.draw_text(x + 64, y, "N", tint=_flag_color(Flags6502.N, status))
    window.draw_text(x + 80, y, "V", tint=_flag_color(Flags6502.V, status))
    window.draw_text(x + 96, y, "-", tint=_flag_color(Flags6502.U, status))
    window.draw_text(x + 112, y, "B", tint=_flag_color(Flags6502.B, status))
    window.draw_text(x + 128, y, "D", tint=_flag_color(Flags6502.D, status))
    window.draw_text(x + 144, y, "I", tint=_flag_color(Flags6502.I, status))
    window.draw_text(x + 160, y, "Z", tint=_flag_color(Flags6502.Z, status))
    window.draw_text(x + 178, y, "C", tint=_flag_color(Flags6502.C, status))
    window.draw_text(x, y + 10, f'PC: ${cpu.pc & 0xffff:04X}')
    window.draw_text(x, y + 20, f'A: ${cpu.a & 0xff:02X} [{cpu.a}]')
    window.draw_text(x, y + 30, f'X: ${cpu.x & 0xff:02X} [{cpu.x}]')
    window.draw_text(x, y + 40, f'Y: ${cpu.y & 0xff:02X} [{cpu.y}]')
    window.draw_text(x, y + 50, f'Stack P: ${cpu.stkp & 0xffff:04X}')
    window.tint = tint


def draw_code(window: HackerWindow, x, y, lines):
    asm_map = window.asm_map
    nes_state = window.nes.cpu.state.pc

    tint = window.tint
    window.tint = MONOCHROME_GREEN

    while nes_state not in asm_map:
        # print(f'missing instruction {nes_state:02X}')
        # program counter already moved ahead?
        nes_state -= 1

    current_line = asm_map[nes_state]
    asm_lines = [current_line]

    count = lines
    current = nes_state
    while count >= 0 and current <= 0xFFFF:
        current += 1
        if current in asm_map:
            asm_lines.append(asm_map[current])
            count -= 1

    count = lines
    current = nes_state
    while count >= 0 and current >= 0x0000:
        current -= 1
        if current in asm_map:
            asm_lines.append(asm_map[current])
            count -= 1

    asm_lines = list(sorted(asm_lines))
    index = asm_lines.index(current_line)
    from_line = max(0, index - lines // 2)
    to_line = min(len(asm_lines), from_line + lines + 1)

    for line in asm_lines[from_line:to_line]:
        color = YELLOW if line == current_line else MONOCHROME_GREEN
        window.draw_text(x, y, line, tint=color)
        y += 10
    window.tint = tint


def draw_ram(window: HackerWindow, x, y, addr, rows, columns):
    cpu = window.nes.cpu
    tint = window.tint
    window.tint = MONOCHROME_GREEN
    for row in range(rows):
        data = f'${addr & 0xffff:04X}:'
        for column in range(columns):
            value = cpu.cpu_read(addr)
            data += f' {value & 0xff:02X}'
            addr += 1
        window.draw_text(x, y, data)
        y += 10
    window.tint = tint


def draw_sprite_ids(window: HackerWindow, x, y):
    nes = window.nes
    tint = window.tint
    window.tint = MONOCHROME_GREEN
    for i in range(26):
        spr_x = nes.ppu._oam[i * 4 + 3]
        spr_y = nes.ppu._oam[i * 4 + 0]
        id = nes.ppu._oam[i * 4 + 1]
        attribute = nes.ppu._oam[i * 4 + 1]
        spr = f'{i:02X}: ({spr_x}, {spr_y}) ID: {id:02X} AT: {attribute}'
        window.draw_text(x, y + i * 10, spr)
    window.tint = tint


def draw_palette(window: HackerWindow, x, y, selected, swatch_size=6, spacing=5):
    nes = window.nes
    offset = 1
    sx = x + selected * (swatch_size * 4 + spacing) - offset
    sy = y - offset
    width = swatch_size * 4 + 2 * offset
    height = swatch_size + 2 * offset
    window.fill_rect(sx, sy, width, height, tint=WHITE)

    for p in range(8):
        for s in range(4):
            sx = x + p * (swatch_size * 4 + spacing) + s * swatch_size
            sy = y
            color = nes.ppu.get_color_from_palette_ram(p, s)
            color = color[0] / 255, color[1] / 255, color[2] / 255
            width = swatch_size
            height = swatch_size
            window.fill_rect(sx, sy, width, height, tint=color)
