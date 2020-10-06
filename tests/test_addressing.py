import pytest

import nes._opcodes_6502 as opcodes


class CPU:
    def __init__(self):
        self.pc = 0x0000
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self._fetched = 0x00
        self._addr_abs = 0x0000
        self._addr_rel = 0x00
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
    assert opcodes.IMP(cpu, cpu) == 0
    assert cpu._fetched == cpu.a


def test_addressing_modes_immediate(cpu):
    assert opcodes.IMM(cpu, cpu) == 0
    assert cpu._addr_abs == cpu.pc - 1


def test_addressing_modes_zero_page(cpu):
    cpu.pc = 1
    assert opcodes.ZP0(cpu, cpu) == 0
    assert cpu.pc == 2
    assert cpu._addr_abs == 0xA7

    cpu.x = 0x24
    assert opcodes.ZPX(cpu, cpu) == 0
    assert cpu.pc == 3
    assert cpu._addr_abs == cpu.ram[2] + cpu.x

    cpu.x = 0xff  # test overflow -> wrap around
    cpu.pc = 2
    assert opcodes.ZPX(cpu, cpu) == 0
    assert cpu.pc == 3
    assert cpu._addr_abs == (cpu.ram[2] + cpu.x) & 0x00ff

    cpu.y = 0x27
    assert opcodes.ZPY(cpu, cpu) == 0
    assert cpu.pc == 4
    assert cpu._addr_abs == cpu.ram[3] + cpu.y

    cpu.y = 0xff  # test overflow -> wrap around
    cpu.pc = 2
    assert opcodes.ZPY(cpu, cpu) == 0
    assert cpu.pc == 3
    assert cpu._addr_abs == (cpu.ram[2] + cpu.y) & 0x00ff


def test_addressing_modes_absolute(cpu):
    cpu.pc = 4
    assert opcodes.ABS(cpu, cpu) == 0
    assert cpu.pc == 6
    assert cpu._addr_abs == cpu.ram[5] << 8 | cpu.ram[4]

    cpu.pc = 0
    cpu.x = 0x24
    assert opcodes.ABX(cpu, cpu) == 0
    assert cpu.pc == 2
    assert cpu._addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.x

    cpu.pc = 0
    cpu.x = 0xFF  # test overflow -> extra cycle
    assert opcodes.ABX(cpu, cpu) == 1
    assert cpu.pc == 2
    assert cpu._addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.x

    cpu.pc = 0
    cpu.y = 0x24
    assert opcodes.ABY(cpu, cpu) == 0
    assert cpu.pc == 2
    assert cpu._addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.y

    cpu.pc = 0
    cpu.y = 0xFF  # test overflow -> extra cycle
    assert opcodes.ABY(cpu, cpu) == 1
    assert cpu.pc == 2
    assert cpu._addr_abs == (cpu.ram[1] << 8 | cpu.ram[0]) + cpu.y


def test_addressing_modes_indirect(cpu):
    cpu.pc = 9
    assert opcodes.IND(cpu, cpu) == 0
    assert cpu.pc == 11
    assert cpu._addr_abs == (cpu.ram[3] << 8 | cpu.ram[2])

    cpu.pc = 6
    assert opcodes.IND(cpu, cpu) == 0
    assert cpu.pc == 8
    assert cpu._addr_abs == 0x0000

    cpu.pc = 9
    cpu.x = 3
    assert opcodes.IZX(cpu, cpu) == 0
    assert cpu.pc == 10
    assert cpu._addr_abs == (cpu.ram[6] << 8 | cpu.ram[5])

    cpu.pc = 9
    cpu.y = 3
    assert opcodes.IZY(cpu, cpu) == 0
    assert cpu.pc == 10
    assert cpu._addr_abs == (cpu.ram[3] << 8 | cpu.ram[2]) + cpu.y

    cpu.pc = 9
    cpu.y = 0xff
    assert opcodes.IZY(cpu, cpu) == 1
    assert cpu.pc == 10
    assert cpu._addr_abs == (cpu.ram[3] << 8 | cpu.ram[2]) + cpu.y


def test_addressing_modes_relative(cpu):
    cpu.pc = 9
    assert opcodes.REL(cpu, cpu) == 0
    assert cpu._addr_rel == 0x02

    cpu.pc = 255
    cpu.ram[255] = 0xA3
    assert opcodes.REL(cpu, cpu) == 0
    assert cpu._addr_rel == cpu.ram[5] | 0xff00
