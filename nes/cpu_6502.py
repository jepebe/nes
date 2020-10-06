from dataclasses import dataclass, fields
from typing import Union

from flags_6502 import Flags6502


@dataclass
class CPU6502State:
    a: int = 0x00  # Accumulator Register
    x: int = 0x00  # X Register
    y: int = 0x00  # Y Register
    stkp: int = 0x00  # Stack pointer (points to location on bus)
    pc: int = 0x0000  # Program Counter
    status: int = 0x00  # Status register
    clock_count: int = 0  # Number clock ticks
    opcode: int = 0x00  # Current opcode

    _addr_abs: int = 0x0000
    _addr_rel: int = 0x00
    _cycles: int = 0
    _implied: int = None  # Temporary value for IMP mode

    def reset(self):
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.stkp = 0xFD
        self.status = 0x00 | Flags6502.U | Flags6502.I

        self._addr_rel = 0x0000
        self._addr_abs = 0x0000
        self._implied = None

        self._cycles = 8

    def get_flag(self, flag: int):
        return 1 if (self.status & flag) else 0

    def set_flag(self, flag: int, value: Union[bool, int]):
        if value:
            self.status |= flag
        else:
            self.status &= ~flag

    def copy_to(self, target):
        for field in fields(CPU6502State):
            setattr(target, field.name, getattr(self, field.name))

    def print_flags(self):
        flags = 'C' if self.get_flag(Flags6502.C) else '.'
        flags += 'Z' if self.get_flag(Flags6502.Z) else '.'
        flags += 'I' if self.get_flag(Flags6502.I) else '.'
        flags += 'D' if self.get_flag(Flags6502.D) else '.'
        flags += 'B' if self.get_flag(Flags6502.B) else '.'
        flags += 'U' if self.get_flag(Flags6502.U) else '.'
        flags += 'V' if self.get_flag(Flags6502.V) else '.'
        flags += 'N' if self.get_flag(Flags6502.N) else '.'
        print(flags)



class CPU6502:
    def __init__(self, bus):
        self.bus = bus
        self.cpu_state = CPU6502State()

        # local import due to cycle in my imports
        import _opcodes_6502
        self.OPCODES = _opcodes_6502.lookup

    # addr is a 16 bit address and data is a single 8 bit byte
    def cpu_write(self, addr: int, data: int):
        self.bus.cpu_write(addr, data)

    # addr is a 16 bit address and returns a 8 bit byte
    def cpu_read(self, addr: int) -> int:
        return self.bus.cpu_read(addr)

    def cpu_read_2(self, addr: int) -> int:
        return self.bus.cpu_read_2(addr)

    def complete(self):
        return self.cpu_state._cycles == 0

    def clock(self):
        cpu_state = self.cpu_state
        if cpu_state._cycles == 0:
            opcode = self.cpu_read(cpu_state.pc)
            cpu_state.pc += 1
            self.cpu_state.opcode = opcode
            self.cpu_state._implied = None
            instruction = self.OPCODES[opcode]
            cpu_state._cycles = instruction.cycles
            additional_cycle1 = instruction.addr_mode(cpu_state, self)
            additional_cycle2 = instruction.operate(cpu_state, self)

            cpu_state._cycles += (additional_cycle1 & additional_cycle2)

        cpu_state._cycles -= 1
        cpu_state.clock_count += 1

    def fetch(self):
        if self.cpu_state._implied is not None:
            return self.cpu_state._implied
        else:
            return self.cpu_read(self.cpu_state._addr_abs)

    def reset(self):
        self.cpu_state.reset()
        self._load_program_counter_from_addr(0xFFFC)

    def irq(self):
        if not self.cpu_state.get_flag(Flags6502.I):
            self._push_program_counter_on_stack()
            self._push_interrupt_state_on_stack()
            self._load_program_counter_from_addr(0xFFFE)
            self.cpu_state._cycles = 7

    def nmi(self):
        self._push_program_counter_on_stack()
        self._push_interrupt_state_on_stack()
        self._load_program_counter_from_addr(0xFFFA)
        self.cpu_state._cycles = 8

    def _push_interrupt_state_on_stack(self):
        self.cpu_state.set_flag(Flags6502.B, 0)
        self.cpu_state.set_flag(Flags6502.U, 1)
        self.cpu_state.set_flag(Flags6502.I, 1)
        self.cpu_write(0x0100 + self.cpu_state.stkp, self.cpu_state.status & 0x00ff)
        self.cpu_state.stkp -= 1

    def _push_program_counter_on_stack(self):
        self.cpu_write(0x0100 + self.cpu_state.stkp, (self.cpu_state.pc >> 8) & 0x00ff)
        self.cpu_state.stkp -= 1
        self.cpu_write(0x0100 + self.cpu_state.stkp, self.cpu_state.pc & 0x00ff)
        self.cpu_state.stkp -= 1

    def _load_program_counter_from_addr(self, addr):
        lo = self.cpu_read(addr)
        hi = self.cpu_read(addr + 1)
        self.cpu_state.pc = (hi << 8) | lo

    def _pop_program_counter_from_stack(self):
        self.cpu_state.stkp += 1
        lo = self.cpu_read(0x0100 + self.cpu_state.stkp) & 0xff
        self.cpu_state.stkp += 1
        hi = self.cpu_read(0x0100 + self.cpu_state.stkp) & 0xff
        self.cpu_state.pc = (hi << 8) | lo
