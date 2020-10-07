import pytest

from nes.cpu_6502 import CPU6502State, CPU6502
from nes.flags_6502 import Flags6502
import nes._opcodes_6502 as opcodes


class CPU:
    def __init__(self):
        self.state = CPU6502State()
        self._fetched = 0x00
        self.values = [0x00, 0x01, 0xff]
        self._data = {}
        self.state.reset()

    def fetch(self):
        self._fetched = self.values.pop(0)
        return self._fetched

    def cpu_write(self, addr, value):
        self._data[addr] = value

    def cpu_read(self, addr):
        return self._data[addr]

    def load_program_counter_from_addr(self, addr):
        CPU6502.load_program_counter_from_addr(self, addr)


@pytest.fixture()
def cpu():
    yield CPU()


def test_logic_operators(cpu):
    cpu.state.a = 0x01
    assert opcodes.AND(cpu) == 1
    assert cpu.state.a == 0x00
    assert cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)

    cpu.state.a = 0x01
    assert opcodes.AND(cpu) == 1
    assert cpu.state.a == 0x01
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)

    cpu.state.a = 0xff
    assert opcodes.AND(cpu) == 1
    assert cpu.state.a == 0xff
    assert not cpu.state.get_flag(Flags6502.Z)
    assert cpu.state.get_flag(Flags6502.N)


def branching(cpu, op, flag, branch_on_set_flag):
    pc = cpu.state.pc
    cpu.state.addr_rel = 0x55
    cpu.state.set_flag(flag, not branch_on_set_flag)
    assert op(cpu) == 0
    assert cpu.state.pc == pc

    cpu.state.pc = 0x7f
    cpu.state.addr_rel = 0x25
    cpu.state.set_flag(flag, branch_on_set_flag)
    assert op(cpu) == 0
    assert cpu.state.pc == 0x7f + 0x25

    cpu.state.pc = 0xff
    cpu.state.addr_rel = 0xFB | 0xff00  # should be -5
    assert op(cpu) == 0
    assert cpu.state.pc == 0xff - 0x05


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
    cpu.state.set_flag(Flags6502.V, True)

    assert cpu.state.get_flag(Flags6502.C)
    assert cpu.state.get_flag(Flags6502.D)
    assert cpu.state.get_flag(Flags6502.I)
    assert cpu.state.get_flag(Flags6502.V)

    assert opcodes.CLC(cpu) == 0
    assert not cpu.state.get_flag(Flags6502.C)
    assert opcodes.CLD(cpu) == 0
    assert not cpu.state.get_flag(Flags6502.D)
    assert opcodes.CLI(cpu) == 0
    assert not cpu.state.get_flag(Flags6502.I)
    assert opcodes.CLV(cpu) == 0
    assert not cpu.state.get_flag(Flags6502.V)


def test_add_with_carry(cpu):
    cpu.state.a = 0x00
    cpu.values = [0x00]
    assert opcodes.ADC(cpu) == 1
    assert not cpu.state.get_flag(Flags6502.C)
    assert cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0

    cpu.state.a = 0x13
    cpu.values = [0x01]
    cpu.state.set_flag(Flags6502.C, 1)
    assert opcodes.ADC(cpu) == 1
    assert not cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x15

    cpu.state.a = 0x7f
    cpu.values = [0xff]
    assert opcodes.ADC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == (0x7f + 0xff) & 0xff
    cpu.state.set_flag(Flags6502.C, 0)

    # positive + positive = negative -> overflow
    cpu.state.a = 0x02
    cpu.values = [0x7f]
    assert opcodes.ADC(cpu) == 1
    assert not cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert cpu.state.get_flag(Flags6502.N)
    assert cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x7f + 0x02

    # negative + negative = positive -> overflow
    cpu.state.a = 0x81
    cpu.values = [0xfd]
    assert opcodes.ADC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x81 - 0x03


def test_subtract_with_carry(cpu):
    # 0 - 0 = 0 -> Z = True and N = True
    cpu.state.a = 0x00
    cpu.values = [0x00]
    cpu.state.set_flag(Flags6502.C, 1)  # subtract without borrow
    assert opcodes.SBC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0

    cpu.state.a = 0x13
    cpu.values = [0x01]
    cpu.state.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x12

    cpu.state.a = 0x13
    cpu.values = [0x01]
    cpu.state.set_flag(Flags6502.C, 0)  # subtract WITH borrow
    assert opcodes.SBC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x11

    cpu.state.a = 0x81
    cpu.values = [0xff]
    cpu.state.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert not cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert cpu.state.get_flag(Flags6502.N)
    assert not cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == (0x81 - 0xff) & 0xff
    cpu.state.set_flag(Flags6502.C, 0)

    # positive + positive = negative -> overflow
    cpu.state.a = 0x02
    cpu.values = [0x80]
    cpu.state.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert not cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert cpu.state.get_flag(Flags6502.N)
    assert cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x02 + 0x80

    # negative + negative = positive -> overflow
    cpu.state.a = 0x81
    cpu.values = [0x03]
    cpu.state.set_flag(Flags6502.C, 1)
    assert opcodes.SBC(cpu) == 1
    assert cpu.state.get_flag(Flags6502.C)
    assert not cpu.state.get_flag(Flags6502.Z)
    assert not cpu.state.get_flag(Flags6502.N)
    assert cpu.state.get_flag(Flags6502.V)
    assert cpu.state.a == 0x81 - 0x03


def test_stack_operations(cpu):
    cpu.state.a = 0x7f
    assert opcodes.PHA(cpu) == 0
    assert cpu.state.stkp == 0xFD - 1
    assert cpu._data[0x0100 + 0xFD] == 0x7f

    cpu.state.a = 0
    assert opcodes.PLA(cpu) == 0
    assert cpu.state.stkp == 0xFD
    assert cpu.state.a == 0x7f

    stkp = cpu.state.stkp
    cpu.state.a = 0xDE
    opcodes.PHA(cpu)
    cpu.state.a = 0xAD
    opcodes.PHA(cpu)
    cpu.state.a = 0b10101010
    opcodes.PHA(cpu)

    assert opcodes.RTI(cpu) == 0
    assert cpu.state.pc == 0xDEAD
    # print(f'{cpu.status:02b} ')
    assert cpu.state.status == 0b10101010
    assert cpu.state.stkp == stkp