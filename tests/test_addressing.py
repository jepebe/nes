import pytest

import nes._opcodes_6502 as opcodes
from cpu_6502 import CPU6502State


class CPU:
    def __init__(self):
        self.state = CPU6502State()
        self._fetched = 0x00
        self.ram = [0x00] * (64 * 1024)
        self.ram[0:10] = [0xA8, 0xA7, 0xA6, 0xA5, 0xA4, 0xA3, 0xFF, 0xA1, 0xA0, 0x02]

    def cpu_read(self, addr):
        print(f'reading from {addr} = {hex(self.ram[addr])}')
        return self.ram[addr]

    def cpu_read_2(self, addr):
        return self.ram[addr:addr + 2]


@pytest.fixture()
def cpu():
    yield CPU()


def test_addressing_modes_implied(cpu):
    assert opcodes.IMP(cpu) == 0
    assert cpu._fetched == cpu.state.a


def test_addressing_modes_immediate(cpu):
    assert opcodes.IMM(cpu) == 0
    assert cpu.state.addr_abs == cpu.state.pc - 1


def test_addressing_modes_zero_page(cpu):
    cpu.state.pc = 1
    assert opcodes.ZP0(cpu) == 0
    assert cpu.state.pc == 2
    assert cpu.state.addr_abs == 0xA7

    cpu.state.x = 0x24
    assert opcodes.ZPX(cpu) == 0
    assert cpu.state.pc == 3
    assert cpu.state.addr_abs == cpu.ram[2] + cpu.state.x

    cpu.state.x = 0xff  # test overflow -> wrap around
    cpu.state.pc = 2
    assert opcodes.ZPX(cpu) == 0
    assert cpu.state.pc == 3
    assert cpu.state.addr_abs == (cpu.ram[2] + cpu.state.x) & 0x00ff

    cpu.state.y = 0x27
    assert opcodes.ZPY(cpu) == 0
    assert cpu.state.pc == 4
    assert cpu.state.addr_abs == cpu.ram[3] + cpu.state.y

    cpu.state.y = 0xff  # test overflow -> wrap around
    cpu.state.pc = 2
    assert opcodes.ZPY(cpu) == 0
    assert cpu.state.pc == 3
    assert cpu.state.addr_abs == (cpu.ram[2] + cpu.state.y) & 0x00ff


def test_addressing_modes_absolute(cpu):
    cpu.state.pc = 4
    assert opcodes.ABS(cpu) == 0
    assert cpu.state.pc == 6
    assert cpu.state.addr_abs == cpu.ram[5] << 8 | cpu.ram[4]

    cpu.state.pc = 0
    cpu.state.x = 0x24
    assert opcodes.ABX(cpu) == 0
    assert cpu.state.pc == 2
    assert cpu.state.addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.state.x

    cpu.state.pc = 0
    cpu.state.x = 0xFF  # test overflow -> extra cycle
    assert opcodes.ABX(cpu) == 1
    assert cpu.state.pc == 2
    assert cpu.state.addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.state.x

    cpu.state.pc = 0
    cpu.state.y = 0x24
    assert opcodes.ABY(cpu) == 0
    assert cpu.state.pc == 2
    assert cpu.state.addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.state.y

    cpu.state.pc = 0
    cpu.state.y = 0xFF  # test overflow -> extra cycle
    assert opcodes.ABY(cpu) == 1
    assert cpu.state.pc == 2
    assert cpu.state.addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.state.y


def test_addressing_modes_indirect(cpu):
    cpu.state.pc = 9
    assert opcodes.IND(cpu) == 0
    assert cpu.state.pc == 11
    assert cpu.state.addr_abs == (cpu.ram[3] << 8 | cpu.ram[2])

    cpu.state.pc = 6
    assert opcodes.IND(cpu) == 0
    assert cpu.state.pc == 8
    assert cpu.state.addr_abs == 0x0000

    cpu.state.pc = 9
    cpu.state.x = 3
    assert opcodes.IZX(cpu) == 0
    assert cpu.state.pc == 10
    assert cpu.state.addr_abs == (cpu.ram[6] << 8 | cpu.ram[5])

    cpu.state.pc = 9
    cpu.state.y = 3
    assert opcodes.IZY(cpu) == 0
    assert cpu.state.pc == 10
    assert cpu.state.addr_abs == (cpu.ram[3] << 8 | cpu.ram[2]) + cpu.state.y

    cpu.state.pc = 9
    cpu.state.y = 0xff
    assert opcodes.IZY(cpu) == 1
    assert cpu.state.pc == 10
    assert cpu.state.addr_abs == (cpu.ram[3] << 8 | cpu.ram[2]) + cpu.state.y


def test_addressing_modes_relative(cpu):
    cpu.state.pc = 9
    assert opcodes.REL(cpu) == 0
    assert cpu.state.addr_rel == 0x02

    cpu.state.pc = 255
    cpu.ram[255] = 0xA3
    assert opcodes.REL(cpu) == 0
    assert cpu.state.addr_rel == cpu.ram[5] | 0xff00
