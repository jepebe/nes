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

    addr_abs: int = 0x0000
    addr_rel: int = 0x00
    cycles: int = 0
    _implied: int = None  # Temporary value for IMP mode

    def reset(self):
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.stkp = 0xFD
        self.status = 0x00 | Flags6502.U | Flags6502.I

        self.addr_rel = 0x0000
        self.addr_abs = 0x0000
        self._implied = None

        self.cycles = 8

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
        print(self.flags_to_string())

    def flags_to_string(self):
        flags = 'C' if self.get_flag(Flags6502.C) else '.'
        flags += 'Z' if self.get_flag(Flags6502.Z) else '.'
        flags += 'I' if self.get_flag(Flags6502.I) else '.'
        flags += 'D' if self.get_flag(Flags6502.D) else '.'
        flags += 'B' if self.get_flag(Flags6502.B) else '.'
        flags += 'U' if self.get_flag(Flags6502.U) else '.'
        flags += 'V' if self.get_flag(Flags6502.V) else '.'
        flags += 'N' if self.get_flag(Flags6502.N) else '.'
        return flags

    def print_state(self):
        print(f'PC: ${self.pc:04X}')
        print(f'A: {self.a:02X}')
        print(f'X: {self.x:02X}')
        print(f'Y: {self.y:02X}')
        print(f'StkP: ${self.stkp:02X}')
        print(f'Status: [{self.flags_to_string()}]')
        print(f'Addr. Abs.: ${self.addr_abs:04X}')
        print(f'Addr. Rel.: ${self.addr_rel:04X}')
        print(f'Implied val.: {self._implied}')

    def check_state(self):
        if (self.a & 0xFF00) != 0:
            print(f'a is larger than 8 bits')
            return False
        if (self.x & 0xFF00) != 0:
            print(f'x is larger than 8 bits')
            return False
        if (self.y & 0xFF00) != 0:
            print(f'y is larger than 8 bits')
            return False
        if (self.pc & 0xFF0000) != 0:
            print(f'pc is larger than 16 bits')
            return False
        if (self.addr_abs & 0xFF0000) != 0:
            print(f'addr_abs is larger than 16 bits')
            return False
        if (self.addr_rel & 0xFF0000) != 0:
            print(f'addr_rel is larger than 16 bits')
            return False
        if (self.addr_rel & 0xFF00) != 0:
            if (self.addr_rel & 0xFF00) != 0xFF00:
                print(f'addr_rel should only have 1s over 8 bits')
                return False
        if (self.stkp & 0xFF00) != 0:
            print(f'stkp is larger than 8 bits')
            return False
        if (self.status & 0xFF00) != 0:
            print(f'status is larger than 8 bits')
            return False

        return True


class CPU6502:
    def __init__(self, bus):
        self.bus = bus
        self.state = CPU6502State()

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
        return self.state.cycles == 0

    def clock(self):
        state = self.state
        if state.cycles == 0:
            opcode = self.cpu_read(state.pc)
            state.pc += 1
            state.opcode = opcode
            state._implied = None
            instruction = self.OPCODES[opcode]
            state.cycles = instruction.cycles
            additional_cycle1 = instruction.addr_mode(self)
            additional_cycle2 = instruction.operate(self)

            state.cycles += (additional_cycle1 & additional_cycle2)

        state.cycles -= 1
        state.clock_count += 1

    def fetch(self):
        if self.state._implied is not None:
            return self.state._implied
        else:
            return self.cpu_read(self.state.addr_abs)

    def reset(self):
        self.state.reset()
        self.load_program_counter_from_addr(0xFFFC)

    def irq(self):
        if not self.state.get_flag(Flags6502.I):
            self.push_program_counter_on_stack()
            self.push_interrupt_state_on_stack()
            self.load_program_counter_from_addr(0xFFFE)
            self.state.cycles = 7

    def nmi(self):
        self.push_program_counter_on_stack()
        self.push_interrupt_state_on_stack()
        self.load_program_counter_from_addr(0xFFFA)
        self.state.cycles = 8

    def push_interrupt_state_on_stack(self):
        self.state.set_flag(Flags6502.B, 0)
        self.state.set_flag(Flags6502.U, 1)
        self.state.set_flag(Flags6502.I, 1)
        self.cpu_write(0x0100 + self.state.stkp, self.state.status & 0x00ff)
        self.state.stkp -= 1

    def push_program_counter_on_stack(self):
        self.cpu_write(0x0100 + self.state.stkp, (self.state.pc >> 8) & 0x00ff)
        self.state.stkp -= 1
        self.cpu_write(0x0100 + self.state.stkp, self.state.pc & 0x00ff)
        self.state.stkp -= 1

    def load_program_counter_from_addr(self, addr):
        lo = self.cpu_read(addr)
        hi = self.cpu_read(addr + 1)
        self.state.pc = (hi << 8) | lo

    def pop_program_counter_from_stack(self):
        self.state.stkp += 1
        lo = self.cpu_read(0x0100 + self.state.stkp) & 0xff
        self.state.stkp += 1
        hi = self.cpu_read(0x0100 + self.state.stkp) & 0xff
        self.state.pc = (hi << 8) | lo

    def push_value_on_stack(self, value):
        self.cpu_write(0x0100 + self.state.stkp, value & 0xFF)
        self.state.stkp -= 1
        self.state.stkp &= 0xFF

    def pop_value_from_stack(self):
        self.state.stkp += 1
        self.state.stkp &= 0xFF
        return self.cpu_read(0x0100 + self.state.stkp) & 0xFF

