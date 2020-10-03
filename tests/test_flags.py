from nes.cpu_6502 import CPU6502
from nes.flags_6502 import FLAGS6502


class CPU:
    def __init__(self):
        self.status = 0x00


def test_flags():
    cpu = CPU()

    for flag in FLAGS6502:
        assert not CPU6502.get_flag(cpu, flag)
        CPU6502.set_flag(cpu, flag, True)
        assert CPU6502.get_flag(cpu, flag) == 1
        assert cpu.status & flag.value == flag.value

    assert cpu.status == 0xff

    for flag in FLAGS6502:
        CPU6502.set_flag(cpu, flag, False)
        assert cpu.status & flag.value == 0

    assert cpu.status == 0x00


def test_flags():
    status = 0xff
    status &= ~FLAGS6502.B.value
    assert status == 239
    status &= ~FLAGS6502.U.value
    assert status == 207
