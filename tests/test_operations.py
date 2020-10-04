import pytest

from nes.cpu_6502 import CPU6502
from nes.flags_6502 import Flags6502
import nes._opcodes_6502 as opcodes


class CPU:
    def __init__(self):
        self.pc = 0x00
        self.stkp = 0xFD
        self.a = 0x00
        self._fetched = 0x00
        self._addr_abs = 0x0000
        self._addr_rel = 0x00
        self.status = 0x00
        self.values = [0x00, 0x01, 0xff]
        self._cycles = 0
        self._data = {}

    def fetch(self):
        self._fetched = self.values.pop(0)
        return self._fetched

    def get_flag(self, flag: Flags6502):
        return CPU6502.get_flag(self, flag)

    def set_flag(self, flag: Flags6502, value: bool):
        CPU6502.set_flag(self, flag, value)

    def cpu_write(self, addr, value):
        self._data[addr] = value

    def cpu_read(self, addr):
        return self._data[addr]

    def _load_program_counter_from_addr(self, addr):
        CPU6502._load_program_counter_from_addr(self, addr)


@pytest.fixture()
def cpu():
    yield CPU()


def test_logic_operators(cpu):
    cpu.a = 0x01
    assert opcodes.AND(cpu) == 1
    assert cpu.a == 0x00
    assert cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)

    cpu.a = 0x01
    assert opcodes.AND(cpu) == 1
    assert cpu.a == 0x01
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)

    cpu.a = 0xff
    assert opcodes.AND(cpu) == 1
    assert cpu.a == 0xff
    assert not cpu.get_flag(Flags6502.Z)
    assert cpu.get_flag(Flags6502.N)


def branching(cpu, op, flag, branch_on_set_flag):
    pc = cpu.pc
    cpu._addr_rel = 0x55
    cpu.set_flag(flag, not branch_on_set_flag)
    assert op(cpu) == 0
    assert cpu.pc == pc

    cpu.pc = 0x7f
    cpu._addr_rel = 0x25
    cpu.set_flag(flag, branch_on_set_flag)
    assert op(cpu) == 0
    assert cpu.pc == 0x7f + 0x25

    cpu.pc = 0xff
    cpu._addr_rel = 0xFB | 0xff00  # should be -5
    assert op(cpu) == 0
    assert cpu.pc == 0xff - 0x05


def test_branching_bcs(cpu):
    branching(cpu, opcodes.BCS, Flags6502.C, True)


def test_branching_bcc(cpu):
    branching(cpu, opcodes.BCC, Flags6502.C, False)


def test_branching_beq(cpu):
    branching(cpu, opcodes.BEQ, Flags6502.Z, True)


def test_branching_bmi(cpu):
    branching(cpu, opcodes.BMI, Flags6502.N, True)


def test_branching_bne(cpu):
    branching(cpu, opcodes.BNE, Flags6502.Z, False)


def test_branching_bpl(cpu):
    branching(cpu, opcodes.BPL, Flags6502.N, False)


def test_branching_bvc(cpu):
    branching(cpu, opcodes.BVC, Flags6502.V, False)


def test_branching_bvs(cpu):
    branching(cpu, opcodes.BVS, Flags6502.V, True)


def test_flag_functions(cpu):
    assert opcodes.SEC(cpu) == 0
    assert opcodes.SED(cpu) == 0
    assert opcodes.SEI(cpu) == 0
    cpu.set_flag(Flags6502.V, True)

    assert cpu.get_flag(Flags6502.C)
    assert cpu.get_flag(Flags6502.D)
    assert cpu.get_flag(Flags6502.I)
    assert cpu.get_flag(Flags6502.V)

    assert opcodes.CLC(cpu) == 0
    assert not cpu.get_flag(Flags6502.C)
    assert opcodes.CLD(cpu) == 0
    assert not cpu.get_flag(Flags6502.D)
    assert opcodes.CLI(cpu) == 0
    assert not cpu.get_flag(Flags6502.I)
    assert opcodes.CLV(cpu) == 0
    assert not cpu.get_flag(Flags6502.V)


def test_add_with_carry(cpu):
    cpu.a = 0x00
    cpu.values = [0x00]
    assert opcodes.ADC(cpu) == 1
    assert not cpu.get_flag(Flags6502.C)
    assert cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == 0

    cpu.a = 0x13
    cpu.values = [0x01]
    cpu.set_flag(Flags6502.C, 1)
    assert opcodes.ADC(cpu) == 1
    assert not cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x15

    cpu.a = 0x7f
    cpu.values = [0xff]
    assert opcodes.ADC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == (0x7f + 0xff) & 0xff
    cpu.set_flag(Flags6502.C, 0)

    # positive + positive = negative -> overflow
    cpu.a = 0x02
    cpu.values = [0x7f]
    assert opcodes.ADC(cpu) == 1
    assert not cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert cpu.get_flag(Flags6502.N)
    assert cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x7f + 0x02

    # negative + negative = positive -> overflow
    cpu.a = 0x81
    cpu.values = [0xfd]
    assert opcodes.ADC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x81 - 0x03


def test_subtract_with_carry(cpu):
    # 0 - 0 = 0 -> Z = True and N = True
    cpu.a = 0x00
    cpu.values = [0x00]
    cpu.set_flag(Flags6502.C, 1)  # subtract without borrow
    assert opcodes.SBC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == 0

    cpu.a = 0x13
    cpu.values = [0x01]
    cpu.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x12

    cpu.a = 0x13
    cpu.values = [0x01]
    cpu.set_flag(Flags6502.C, 0)  # subtract WITH borrow
    assert opcodes.SBC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x11

    cpu.a = 0x81
    cpu.values = [0xff]
    cpu.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert not cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert cpu.get_flag(Flags6502.N)
    assert not cpu.get_flag(Flags6502.V)
    assert cpu.a == (0x81 - 0xff) & 0xff
    cpu.set_flag(Flags6502.C, 0)

    # positive + positive = negative -> overflow
    cpu.a = 0x02
    cpu.values = [0x80]
    cpu.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert not cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert cpu.get_flag(Flags6502.N)
    assert cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x02 + 0x80

    # negative + negative = positive -> overflow
    cpu.a = 0x81
    cpu.values = [0x03]
    cpu.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert cpu.get_flag(Flags6502.C)
    assert not cpu.get_flag(Flags6502.Z)
    assert not cpu.get_flag(Flags6502.N)
    assert cpu.get_flag(Flags6502.V)
    assert cpu.a == 0x81 - 0x03


def test_stack_operations(cpu):
    cpu.a = 0x7f
    assert opcodes.PHA(cpu) == 0
    assert cpu.stkp == 0xFD - 1
    assert cpu._data[0x0100 + 0xFD] == 0x7f

    cpu.a = 0
    assert opcodes.PLA(cpu) == 0
    assert cpu.stkp == 0xFD
    assert cpu.a == 0x7f

    stkp = cpu.stkp
    cpu.a = 0xDE
    opcodes.PHA(cpu)
    cpu.a = 0xAD
    opcodes.PHA(cpu)
    cpu.a = 0b10101010
    opcodes.PHA(cpu)

    assert opcodes.RTI(cpu) == 0
    assert cpu.pc == 0xDEAD
    assert cpu.status == 0b10001010
    assert cpu.stkp == stkp