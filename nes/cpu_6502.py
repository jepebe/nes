from typing import Union

from flags_6502 import Flags6502


class CPU6502:
    def __init__(self, bus):
        self.bus = bus

        self.a = 0x00  # Accumulator Register
        self.x = 0x00  # X Register
        self.y = 0x00  # Y Register
        self.stkp = 0x00  # Stack pointer (points to location on bus)
        self.pc = 0x0000  # Program Counter
        self.status = 0x00  # Status register

        self._fetched = 0x00
        self._addr_abs = 0x0000
        self._addr_rel = 0x00
        self._opcode = 0x00
        self._cycles = 0
        self._implied = None  # Temporary value for IMP mode

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

    def get_flag(self, flag: int):
        return 1 if (self.status & flag) else 0

    def set_flag(self, flag: int, value: Union[bool, int]):
        if value:
            self.status |= flag
        else:
            self.status &= ~flag

    def complete(self):
        return self._cycles == 0

    def clock(self):
        if self._cycles == 0:
            opcode = self.cpu_read(self.pc)
            self.pc += 1

            self._cycles = self.OPCODES[opcode].cycles
            additional_cycle1 = self.OPCODES[opcode].addr_mode(self)
            additional_cycle2 = self.OPCODES[opcode].operate(self)

            if additional_cycle1 is None or additional_cycle2 is None:
                print(f'opcode returning None: {self.OPCODES[opcode]}')
            else:
                self._cycles += (additional_cycle1 & additional_cycle2)

        self._cycles -= 1

    def fetch(self):
        if self._implied:
            self._fetched = self._implied
            self._implied = None
        else:
            self._fetched = self.cpu_read(self._addr_abs)
        return self._fetched

    def reset(self):
        self.a = 0x00
        self.x = 0x00
        self.y = 0x00
        self.stkp = 0xFD
        self.status = 0x00 | Flags6502.U

        self._load_program_counter_from_addr(0xFFFC)

        self._addr_rel = 0x0000
        self._addr_abs = 0x0000
        self._fetched = 0x00

        self._cycles = 8

    def irq(self):
        if not self.get_flag(Flags6502.I):
            self._store_program_counter_from_stack()
            self._store_interrupt_state_on_stack()
            self._load_program_counter_from_addr(0xFFFE)
            self._cycles = 7

    def nmi(self):
        self._store_program_counter_from_stack()
        self._store_interrupt_state_on_stack()
        self._load_program_counter_from_addr(0xFFFA)
        self._cycles = 8

    def _store_interrupt_state_on_stack(self):
        self.set_flag(Flags6502.B, 0)
        self.set_flag(Flags6502.U, 1)
        self.set_flag(Flags6502.I, 1)
        self.cpu_write(0x0100 + self.stkp, self.status & 0x00ff)
        self.stkp -= 1

    def _store_program_counter_from_stack(self):
        self.cpu_write(0x0100 + self.stkp, (self.pc >> 8) & 0x00ff)
        self.stkp -= 1
        self.cpu_write(0x0100 + self.stkp, self.pc & 0x00ff)
        self.stkp -= 1

    def _load_program_counter_from_addr(self, addr):
        lo = self.cpu_read(addr)
        hi = self.cpu_read(addr + 1)
        self.pc = (hi << 8) | lo
