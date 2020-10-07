from cpu_6502 import CPU6502, CPU6502State
from flags_6502 import Flags6502


# Addressing Modes
def IMP(cpu: CPU6502):
    cpu.state._implied = cpu.state.a
    return 0


def IMM(cpu: CPU6502):
    cpu.state.addr_abs = cpu.state.pc
    cpu.state.pc += 1
    return 0


def ZP0(cpu: CPU6502):
    cpu.state.addr_abs = cpu.cpu_read(cpu.state.pc)
    cpu.state.pc += 1
    cpu.state.addr_abs &= 0x00ff
    return 0


def ZPX(cpu: CPU6502):
    cpu.state.addr_abs = cpu.cpu_read(cpu.state.pc) + cpu.state.x
    cpu.state.pc += 1
    cpu.state.addr_abs &= 0x00ff
    return 0


def ZPY(cpu: CPU6502):
    cpu.state.addr_abs = cpu.cpu_read(cpu.state.pc) + cpu.state.y
    cpu.state.pc += 1
    cpu.state.addr_abs &= 0x00ff
    return 0


def REL(cpu: CPU6502):
    cpu.state.addr_rel = cpu.cpu_read(cpu.state.pc)
    cpu.state.pc += 1
    if cpu.state.addr_rel & 0x80:
        cpu.state.addr_rel |= 0xff00

    return 0


def ABS(cpu: CPU6502):
    lo, hi = cpu.cpu_read_2(cpu.state.pc)
    cpu.state.pc += 2
    cpu.state.addr_abs = (hi << 8) | lo
    return 0


def ABX(cpu: CPU6502):
    lo, hi = cpu.cpu_read_2(cpu.state.pc)
    cpu.state.pc += 2
    cpu.state.addr_abs = (hi << 8) | lo
    cpu.state.addr_abs += cpu.state.x

    if (cpu.state.addr_abs & 0xff00) != (hi << 8):
        return 1
    else:
        return 0


def ABY(cpu: CPU6502):
    lo, hi = cpu.cpu_read_2(cpu.state.pc)
    cpu.state.pc += 2
    addr = ((hi << 8) | lo) + cpu.state.y
    cpu.state.addr_abs = addr & 0xFFFF

    if (addr & 0xff00) != (hi << 8):
        return 1
    else:
        return 0


def IND(cpu: CPU6502):
    ptr_lo, ptr_hi = cpu.cpu_read_2(cpu.state.pc)
    cpu.state.pc += 2
    ptr = (ptr_hi << 8) | ptr_lo

    if ptr_lo == 0x00ff:  # Simulate page boundary hardware bug
        cpu.state.addr_abs = (cpu.cpu_read(ptr & 0xff00) << 8) | cpu.cpu_read(ptr + 0)
    else:
        cpu.state.addr_abs = (cpu.cpu_read(ptr + 1) << 8) | cpu.cpu_read(ptr + 0)

    return 0


def IZX(cpu: CPU6502):
    t = cpu.cpu_read(cpu.state.pc)
    cpu.state.pc += 1

    lo = cpu.cpu_read((t + cpu.state.x) & 0x00ff)
    hi = cpu.cpu_read((t + cpu.state.x + 1) & 0x00ff)

    cpu.state.addr_abs = (hi << 8) | lo
    return 0


def IZY(cpu: CPU6502):
    t = cpu.cpu_read(cpu.state.pc)
    cpu.state.pc += 1

    lo = cpu.cpu_read(t & 0x00ff)
    hi = cpu.cpu_read((t + 1) & 0x00ff)

    addr = ((hi << 8) | lo) + cpu.state.y
    cpu.state.addr_abs = addr & 0xFFFF

    if (addr & 0xff00) != (hi << 8):
        return 1
    else:
        return 0


# Opcodes
def _add(cpu, fetched):
    a = cpu.state.a
    carry = cpu.state.get_flag(Flags6502.C)
    temp = (a & 0xffff) + (fetched & 0xffff) + (carry & 0xffff)
    cpu.state.set_flag(Flags6502.C, temp > 0xff)
    cpu.state.set_flag(Flags6502.Z, (temp & 0x00ff) == 0)
    cpu.state.set_flag(Flags6502.N, temp & 0x80)
    overflow = ~(a ^ fetched) & (a ^ temp) & 0x0080
    cpu.state.set_flag(Flags6502.V, overflow)
    cpu.state.a = temp & 0x00ff


# add with carry
def ADC(cpu: CPU6502):
    fetched = cpu.fetch()
    _add(cpu, fetched)
    return 1


# ANDs the contents of the A register with an immediate
# value and then moves bit 7 of A into the Carry flag
def ANC(cpu: CPU6502):
    AND(cpu)
    ASL(cpu)
    return 1


# and (with accumulator)
def AND(cpu: CPU6502):
    fetched = cpu.fetch()
    cpu.state.a = cpu.state.a & fetched
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 1


# arithmetic shift left
def ASL(cpu: CPU6502):
    fetched = cpu.fetch()
    cpu.state.set_flag(Flags6502.C, fetched & 0x80)
    fetched = (fetched << 1) & 0xFF
    cpu.state.set_flag(Flags6502.Z, fetched == 0x00)
    cpu.state.set_flag(Flags6502.N, fetched & 0x80)

    if lookup[cpu.state.opcode].addr_mode == IMP:
        cpu.state.a = fetched
    else:
        cpu.cpu_write(cpu.state.addr_abs, fetched)
    return 0


def _branch(cpu: CPU6502):
    cpu.state.cycles += 1
    cpu.state.addr_abs = cpu.state.pc + cpu.state.addr_rel

    if (cpu.state.addr_abs & 0xff00) != (cpu.state.pc & 0xff00):
        cpu.state.cycles += 1
    cpu.state.pc = cpu.state.addr_abs & 0xffff


# branch on carry clear
def BCC(cpu: CPU6502):
    if not cpu.state.get_flag(Flags6502.C):
        _branch(cpu)
    return 0


# branch on carry set
def BCS(cpu: CPU6502):
    if cpu.state.get_flag(Flags6502.C):
        _branch(cpu)
    return 0


# branch on equal (zero set)
def BEQ(cpu: CPU6502):
    if cpu.state.get_flag(Flags6502.Z):
        _branch(cpu)
    return 0


# bit test
def BIT(cpu: CPU6502):
    fetched = cpu.fetch()
    temp = cpu.state.a & fetched
    cpu.state.set_flag(Flags6502.Z, (temp & 0x00FF) == 0x00)
    cpu.state.set_flag(Flags6502.N, fetched & (1 << 7))
    cpu.state.set_flag(Flags6502.V, fetched & (1 << 6))
    return 0


# branch on minus (negative set)
def BMI(cpu: CPU6502):
    if cpu.state.get_flag(Flags6502.N):
        _branch(cpu)
    return 0


# branch on not equal (zero clear)
def BNE(cpu: CPU6502):
    if not cpu.state.get_flag(Flags6502.Z):
        _branch(cpu)
    return 0


# branch on plus (negative clear)
def BPL(cpu: CPU6502):
    if cpu.state.get_flag(Flags6502.N) == 0:
        _branch(cpu)
    return 0


# break / interrupt
def BRK(cpu: CPU6502):
    cpu.state.pc += 1
    cpu.push_program_counter_on_stack()
    cpu.push_value_on_stack(cpu.state.status | Flags6502.B | Flags6502.U)
    cpu.load_program_counter_from_addr(0xFFFE)
    return 0


# branch on overflow clear
def BVC(cpu: CPU6502):
    if not cpu.state.get_flag(Flags6502.V):
        _branch(cpu)
    return 0


# branch on overflow set
def BVS(cpu: CPU6502):
    if cpu.state.get_flag(Flags6502.V):
        _branch(cpu)
    return 0


# clear carry
def CLC(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.C, False)
    return 0


# clear decimal
def CLD(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.D, False)
    return 0


# clear interrupt disable
def CLI(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.I, False)
    return 0


# clear overflow
def CLV(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.V, False)
    return 0


# compare (with accumulator)
def CMP(cpu: CPU6502):
    fetched = cpu.fetch()

    temp = cpu.state.a - fetched
    cpu.state.set_flag(Flags6502.C, (cpu.state.a & 0xFF) >= fetched)
    cpu.state.set_flag(Flags6502.Z, (temp & 0x00ff) == 0x00)
    cpu.state.set_flag(Flags6502.N, temp & 0x80)
    return 1


# compare with X
def CPX(cpu: CPU6502):
    fetched = cpu.fetch()
    temp = cpu.state.x - fetched
    cpu.state.set_flag(Flags6502.C, cpu.state.x >= fetched)
    cpu.state.set_flag(Flags6502.Z, (temp & 0x00ff) == 0x00)
    cpu.state.set_flag(Flags6502.N, temp & 0x80)
    return 1


# compare with Y
def CPY(cpu: CPU6502):
    fetched = cpu.fetch()
    temp = cpu.state.y - fetched
    cpu.state.set_flag(Flags6502.C, cpu.state.y >= fetched)
    cpu.state.set_flag(Flags6502.Z, (temp & 0x00ff) == 0x00)
    cpu.state.set_flag(Flags6502.N, temp & 0x80)
    return 1


# decrement and compare with Accumulator
def DCP(cpu: CPU6502):
    DEC(cpu)
    CMP(cpu)
    return 1


# decrement
def DEC(cpu: CPU6502):
    value = cpu.fetch()
    value -= 1
    cpu.cpu_write(cpu.state.addr_abs, value & 0xff)
    cpu.state.set_flag(Flags6502.Z, (value & 0xff) == 0x00)
    cpu.state.set_flag(Flags6502.N, value & 0x0080)
    return 0


# decrement X
def DEX(cpu: CPU6502):
    cpu.state.x = (cpu.state.x - 0x01) & 0xff
    cpu.state.set_flag(Flags6502.Z, cpu.state.x == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.x & 0x80)
    return 0


# decrement Y
def DEY(cpu: CPU6502):
    cpu.state.y = (cpu.state.y - 0x01) & 0xff
    cpu.state.set_flag(Flags6502.Z, cpu.state.y == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.y & 0x80)
    return 0


# exclusive or (with accumulator)
def EOR(cpu: CPU6502):
    m = cpu.fetch()
    cpu.state.a ^= (m & 0xff)
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 1


# increment
def INC(cpu: CPU6502):
    value = cpu.fetch()
    value += 1
    cpu.cpu_write(cpu.state.addr_abs, value & 0xff)
    cpu.state.set_flag(Flags6502.Z, (value & 0xff) == 0x00)
    cpu.state.set_flag(Flags6502.N, value & 0x0080)
    return 0


# increment X
def INX(cpu: CPU6502):
    cpu.state.x = (cpu.state.x + 0x01) & 0xFF
    cpu.state.set_flag(Flags6502.Z, cpu.state.x == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.x & 0x80)
    return 0


# increment Y
def INY(cpu: CPU6502):
    cpu.state.y = (cpu.state.y + 0x01) & 0xFF
    cpu.state.set_flag(Flags6502.Z, cpu.state.y == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.y & 0x80)
    return 0


# Increment memory with one and then subtract memory from Accumulator
def ISB(cpu: CPU6502):
    INC(cpu)
    SBC(cpu)
    # value = cpu.fetch()
    # value += 1
    # _add(cpu, (value & 0xffff) ^ 0x00ff)
    # cpu.cpu_write(cpu.state.addr_abs, value)
    return 1


# jump
def JMP(cpu: CPU6502):
    cpu.state.pc = cpu.state.addr_abs
    return 0


# jump subroutine
def JSR(cpu: CPU6502):
    cpu.state.pc -= 1
    cpu.push_program_counter_on_stack()
    cpu.state.pc = cpu.state.addr_abs
    return 0


# * load accumulator and x with memory contents
def LAX(cpu: CPU6502):
    value = cpu.fetch() & 0xFF
    cpu.state.a = value
    cpu.state.x = value
    cpu.state.set_flag(Flags6502.Z, value == 0x00)
    cpu.state.set_flag(Flags6502.N, value & 0x80)
    return 1


# load accumulator
def LDA(cpu: CPU6502):
    cpu.state.a = cpu.fetch() & 0xFF
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 1


# load X
def LDX(cpu: CPU6502):
    cpu.state.x = cpu.fetch() & 0xFF
    cpu.state.set_flag(Flags6502.Z, cpu.state.x == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.x & 0x80)
    return 1


# load Y
def LDY(cpu: CPU6502):
    cpu.state.y = cpu.fetch() & 0xFF
    cpu.state.set_flag(Flags6502.Z, cpu.state.y == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.y & 0x80)
    return 1


# logical shift right
def LSR(cpu: CPU6502):
    fetched = cpu.fetch() & 0xFF
    cpu.state.set_flag(Flags6502.C, fetched & 0x01)
    fetched = (fetched >> 1) & 0xFF
    cpu.state.set_flag(Flags6502.Z, fetched == 0x00)
    cpu.state.set_flag(Flags6502.N, 0)

    if lookup[cpu.state.opcode].addr_mode == IMP:
        cpu.state.a = fetched
    else:
        cpu.cpu_write(cpu.state.addr_abs, fetched)
    return 0


# no operation
def NOP(cpu: CPU6502):
    if cpu.state.opcode in (0x1C, 0x3C, 0x5C, 0x7C, 0xDC, 0xFC):
        return 1
    return 0


# or with accumulator
def ORA(cpu: CPU6502):
    m = cpu.fetch()
    cpu.state.a |= (m & 0xff)
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 1


# push accumulator
def PHA(cpu: CPU6502):
    cpu.push_value_on_stack(cpu.state.a)
    return 0


# push processor status (SR)
def PHP(cpu: CPU6502):
    cpu.push_value_on_stack(cpu.state.status | Flags6502.B | Flags6502.U)
    return 0


# pull accumulator
def PLA(cpu: CPU6502):
    cpu.state.a = cpu.pop_value_from_stack()
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 0


# pull processor status (SR)
def PLP(cpu: CPU6502):
    cpu.state.status = cpu.pop_value_from_stack()
    cpu.state.set_flag(Flags6502.U, 1)
    cpu.state.set_flag(Flags6502.B, 0)
    return 0


# rotate memory left and then AND accumulator with memory
def RLA(cpu: CPU6502):
    fetched = cpu.fetch() & 0XFF
    fetched = (fetched << 1) | cpu.state.get_flag(Flags6502.C)
    cpu.state.set_flag(Flags6502.C, fetched & 0xFF00)
    cpu.state.a = cpu.state.a & fetched
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    cpu.cpu_write(cpu.state.addr_abs, fetched & 0xFF)
    return 0


# rotate left
def ROL(cpu: CPU6502):
    fetched = cpu.fetch() & 0XFF
    fetched = (fetched << 1) | cpu.state.get_flag(Flags6502.C)
    cpu.state.set_flag(Flags6502.C, fetched & 0xFF00)
    fetched &= 0xFF
    cpu.state.set_flag(Flags6502.Z, fetched == 0x00)
    cpu.state.set_flag(Flags6502.N, fetched & 0x80)

    if lookup[cpu.state.opcode].addr_mode == IMP:
        cpu.state.a = fetched
    else:
        cpu.cpu_write(cpu.state.addr_abs, fetched)
    return 0


# rotate right
def ROR(cpu: CPU6502):
    fetched = cpu.fetch()
    carry = fetched & 0x01
    fetched = (cpu.state.get_flag(Flags6502.C) << 7) | (fetched >> 1)
    fetched &= 0xFF
    cpu.state.set_flag(Flags6502.C, carry)
    cpu.state.set_flag(Flags6502.Z, fetched == 0x00)
    cpu.state.set_flag(Flags6502.N, fetched & 0x80)

    if lookup[cpu.state.opcode].addr_mode == IMP:
        cpu.state.a = fetched
    else:
        cpu.cpu_write(cpu.state.addr_abs, fetched)
    return 0


# Rotate memory one bit to the right and then add memory to accumulator
def RRA(cpu: CPU6502):
    m = cpu.fetch()
    carry = m & 0x01
    m = (cpu.state.get_flag(Flags6502.C) << 7) | (m >> 1)
    m &= 0xFF
    cpu.state.set_flag(Flags6502.C, carry)
    _add(cpu, m)
    cpu.cpu_write(cpu.state.addr_abs, m & 0xFF)
    return 0


# return from interrupt
def RTI(cpu: CPU6502):
    cpu.state.status = cpu.pop_value_from_stack()
    cpu.state.set_flag(Flags6502.U, 1)
    cpu.state.set_flag(Flags6502.B, 0)

    cpu.pop_program_counter_from_stack()
    return 0


# return from subroutine
def RTS(cpu: CPU6502):
    cpu.pop_program_counter_from_stack()
    cpu.state.pc += 1
    return 0


# AND X with A and store in memory
def SAX(cpu: CPU6502):
    temp = (cpu.state.a & cpu.state.x)
    cpu.cpu_write(cpu.state.addr_abs, temp)
    return 0


# subtract with carry
def SBC(cpu: CPU6502):
    value = cpu.fetch()
    value = (value & 0xffff) ^ 0x00ff
    _add(cpu, value)
    return 1


# set carry
def SEC(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.C, True)
    return 0


# set decimal
def SED(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.D, True)
    return 0


# set interrupt disable
def SEI(cpu: CPU6502):
    cpu.state.set_flag(Flags6502.I, True)
    return 0


# Shift memory left and then OR accumulator with memory
def SLO(cpu: CPU6502):
    m = cpu.fetch() & 0xFF
    m <<= 1

    cpu.state.a |= (m & 0xff)
    cpu.state.set_flag(Flags6502.C, m & 0xFF00)
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)

    cpu.cpu_write(cpu.state.addr_abs, m & 0xFF)
    return 0


# Shift memory one bit right then XOR with accumulator
def SRE(cpu: CPU6502):
    m = cpu.fetch() & 0xFF
    cpu.state.set_flag(Flags6502.C, m & 0x01)
    m = (m >> 1) & 0xFF

    cpu.state.a ^= m
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)

    cpu.cpu_write(cpu.state.addr_abs, m & 0xFF)
    return 0


# store accumulator
def STA(cpu: CPU6502):
    cpu.cpu_write(cpu.state.addr_abs, cpu.state.a)
    return 0


# store X
def STX(cpu: CPU6502):
    cpu.cpu_write(cpu.state.addr_abs, cpu.state.x)
    return 0


# store Y
def STY(cpu: CPU6502):
    cpu.cpu_write(cpu.state.addr_abs, cpu.state.y)
    return 0


# transfer accumulator to X
def TAX(cpu: CPU6502):
    cpu.state.x = cpu.state.a
    cpu.state.set_flag(Flags6502.Z, cpu.state.x == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.x & 0x80)
    return 0


# transfer accumulator to Y
def TAY(cpu: CPU6502):
    cpu.state.y = cpu.state.a
    cpu.state.set_flag(Flags6502.Z, cpu.state.y == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.y & 0x80)
    return 0


# transfer stack pointer to X
def TSX(cpu: CPU6502):
    cpu.state.x = cpu.state.stkp
    cpu.state.set_flag(Flags6502.Z, cpu.state.x == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.x & 0x80)
    return 0


# transfer X to accumulator
def TXA(cpu: CPU6502):
    cpu.state.a = cpu.state.x
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 0


# transfer X to stack pointer
def TXS(cpu: CPU6502):
    cpu.state.stkp = cpu.state.x
    return 0


# transfer Y to accumulator
def TYA(cpu: CPU6502):
    cpu.state.a = cpu.state.y
    cpu.state.set_flag(Flags6502.Z, cpu.state.a == 0x00)
    cpu.state.set_flag(Flags6502.N, cpu.state.a & 0x80)
    return 0


# illegal opcodes
def XXX(cpu: CPU6502):
    print(f'Illegal opcode {cpu.state.opcode:02X} at ${cpu.state.pc:04X}')
    return 0


class Instruction:
    def __init__(self, name, operate, addr_mode, cycles, non_standard=False):
        self.name = name
        self.operate = operate
        self.addr_mode = addr_mode
        self.cycles = cycles
        self.is_non_standard = non_standard

    def __repr__(self):
        name = self.name
        op = self.operate.__name__
        mode = self.addr_mode.__name__
        cycles = self.cycles
        return f'{name} {op} {mode} {cycles}'


# This array represents a 16x16 matrix of possible opcodes
lookup = [
    Instruction("BRK", BRK, IMM, 7),
    Instruction("ORA", ORA, IZX, 6),
    Instruction("???", XXX, IMP, 2),
    Instruction("SLO", SLO, IZX, 8, non_standard=True),
    Instruction("NOP", NOP, ZP0, 3, non_standard=True),
    Instruction("ORA", ORA, ZP0, 3),
    Instruction("ASL", ASL, ZP0, 5),
    Instruction("SLO", SLO, ZP0, 5, non_standard=True),
    Instruction("PHP", PHP, IMP, 3),
    Instruction("ORA", ORA, IMM, 2),
    Instruction("ASL", ASL, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("NOP", NOP, ABS, 4, non_standard=True),
    Instruction("ORA", ORA, ABS, 4),
    Instruction("ASL", ASL, ABS, 6),
    Instruction("SLO", SLO, ABS, 6, non_standard=True),

    Instruction("BPL", BPL, REL, 2),  # 16 0x10
    Instruction("ORA", ORA, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("SLO", SLO, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),
    Instruction("ORA", ORA, ZPX, 4),
    Instruction("ASL", ASL, ZPX, 6),
    Instruction("SLO", SLO, ZPX, 6, non_standard=True),
    Instruction("CLC", CLC, IMP, 2),
    Instruction("ORA", ORA, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("SLO", SLO, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0x1C
    Instruction("ORA", ORA, ABX, 4),
    Instruction("ASL", ASL, ABX, 7),
    Instruction("SLO", SLO, ABX, 7, non_standard=True),

    Instruction("JSR", JSR, ABS, 6),  # 32 0x20
    Instruction("AND", AND, IZX, 6),
    Instruction("???", XXX, IMP, 2),
    Instruction("RLA", RLA, IZX, 8, non_standard=True),
    Instruction("BIT", BIT, ZP0, 3),
    Instruction("AND", AND, ZP0, 3),
    Instruction("ROL", ROL, ZP0, 5),
    Instruction("RLA", RLA, ZP0, 5, non_standard=True),  # 0x27
    Instruction("PLP", PLP, IMP, 4),
    Instruction("AND", AND, IMM, 2),
    Instruction("ROL", ROL, IMP, 2),
    Instruction("ANC", ANC, IMM, 2, non_standard=True),
    Instruction("BIT", BIT, ABS, 4),
    Instruction("AND", AND, ABS, 4),
    Instruction("ROL", ROL, ABS, 6),
    Instruction("RLA", RLA, ABS, 6, non_standard=True),

    Instruction("BMI", BMI, REL, 2),  # 48 0x30
    Instruction("AND", AND, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("RLA", RLA, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),
    Instruction("AND", AND, ZPX, 4),
    Instruction("ROL", ROL, ZPX, 6),
    Instruction("RLA", RLA, ZPX, 6, non_standard=True),
    Instruction("SEC", SEC, IMP, 2),
    Instruction("AND", AND, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("RLA", RLA, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0x3C
    Instruction("AND", AND, ABX, 4),
    Instruction("ROL", ROL, ABX, 7),
    Instruction("RLA", RLA, ABX, 7, non_standard=True),

    Instruction("RTI", RTI, IMP, 6),  # 64 0x40
    Instruction("EOR", EOR, IZX, 6),
    Instruction("???", XXX, IMP, 2),
    Instruction("SRE", SRE, IZX, 8, non_standard=True),
    Instruction("NOP", NOP, ZP0, 3, non_standard=True),
    Instruction("EOR", EOR, ZP0, 3),
    Instruction("LSR", LSR, ZP0, 5),
    Instruction("SRE", SRE, ZP0, 5, non_standard=True),
    Instruction("PHA", PHA, IMP, 3),
    Instruction("EOR", EOR, IMM, 2),
    Instruction("LSR", LSR, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("JMP", JMP, ABS, 3),
    Instruction("EOR", EOR, ABS, 4),
    Instruction("LSR", LSR, ABS, 6),
    Instruction("SRE", SRE, ABS, 6, non_standard=True),

    Instruction("BVC", BVC, REL, 2),  # 80 0x50
    Instruction("EOR", EOR, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("SRE", SRE, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),  # 0x54
    Instruction("EOR", EOR, ZPX, 4),
    Instruction("LSR", LSR, ZPX, 6),
    Instruction("SRE", SRE, ZPX, 6, non_standard=True),
    Instruction("CLI", CLI, IMP, 2),
    Instruction("EOR", EOR, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("SRE", SRE, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0x5C
    Instruction("EOR", EOR, ABX, 4),
    Instruction("LSR", LSR, ABX, 7),
    Instruction("SRE", SRE, ABX, 7, non_standard=True),

    Instruction("RTS", RTS, IMP, 6),  # 96 0x60
    Instruction("ADC", ADC, IZX, 6),
    Instruction("???", XXX, IMP, 2),
    Instruction("RRA", RRA, IZX, 8, non_standard=True),
    Instruction("NOP", NOP, ZP0, 3, non_standard=True),  # 0x64
    Instruction("ADC", ADC, ZP0, 3),
    Instruction("ROR", ROR, ZP0, 5),
    Instruction("RRA", RRA, ZP0, 5, non_standard=True),
    Instruction("PLA", PLA, IMP, 4),
    Instruction("ADC", ADC, IMM, 2),
    Instruction("ROR", ROR, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("JMP", JMP, IND, 5),
    Instruction("ADC", ADC, ABS, 4),
    Instruction("ROR", ROR, ABS, 6),
    Instruction("RRA", RRA, ABS, 6, non_standard=True),

    Instruction("BVS", BVS, REL, 2),  # 112 0x70
    Instruction("ADC", ADC, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("RRA", RRA, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),  # 0x74
    Instruction("ADC", ADC, ZPX, 4),
    Instruction("ROR", ROR, ZPX, 6),
    Instruction("RRA", RRA, ZPX, 6, non_standard=True),
    Instruction("SEI", SEI, IMP, 2),
    Instruction("ADC", ADC, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("RRA", RRA, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0x7C
    Instruction("ADC", ADC, ABX, 4),
    Instruction("ROR", ROR, ABX, 7),
    Instruction("RRA", RRA, ABX, 7, non_standard=True),

    Instruction("NOP", NOP, IMM, 2, non_standard=True),  # 128 0x80
    Instruction("STA", STA, IZX, 6),
    Instruction("???", NOP, IMP, 2),
    Instruction("SAX", SAX, IZX, 6, non_standard=True),
    Instruction("STY", STY, ZP0, 3),
    Instruction("STA", STA, ZP0, 3),
    Instruction("STX", STX, ZP0, 3),
    Instruction("SAX", SAX, ZP0, 3, non_standard=True),
    Instruction("DEY", DEY, IMP, 2),
    Instruction("???", NOP, IMP, 2),
    Instruction("TXA", TXA, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("STY", STY, ABS, 4),
    Instruction("STA", STA, ABS, 4),
    Instruction("STX", STX, ABS, 4),
    Instruction("SAX", SAX, ABS, 4, non_standard=True),

    Instruction("BCC", BCC, REL, 2),  # 144 0x90
    Instruction("STA", STA, IZY, 6),
    Instruction("???", XXX, IMP, 2),
    Instruction("???", XXX, IMP, 6),
    Instruction("STY", STY, ZPX, 4),
    Instruction("STA", STA, ZPX, 4),
    Instruction("STX", STX, ZPY, 4),
    Instruction("SAX", SAX, ZPY, 4, non_standard=True),
    Instruction("TYA", TYA, IMP, 2),
    Instruction("STA", STA, ABY, 5),
    Instruction("TXS", TXS, IMP, 2),
    Instruction("???", XXX, IMP, 5),
    Instruction("???", NOP, IMP, 5),
    Instruction("STA", STA, ABX, 5),
    Instruction("???", XXX, IMP, 5),
    Instruction("???", XXX, IMP, 5),

    Instruction("LDY", LDY, IMM, 2),  # 160 0xA0
    Instruction("LDA", LDA, IZX, 6),
    Instruction("LDX", LDX, IMM, 2),
    Instruction("LAX", LAX, IZX, 6, non_standard=True),
    Instruction("LDY", LDY, ZP0, 3),
    Instruction("LDA", LDA, ZP0, 3),
    Instruction("LDX", LDX, ZP0, 3),
    Instruction("LAX", LAX, ZP0, 3, non_standard=True),
    Instruction("TAY", TAY, IMP, 2),
    Instruction("LDA", LDA, IMM, 2),
    Instruction("TAX", TAX, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("LDY", LDY, ABS, 4),
    Instruction("LDA", LDA, ABS, 4),
    Instruction("LDX", LDX, ABS, 4),
    Instruction("LAX", LAX, ABS, 4, non_standard=True),

    Instruction("BCS", BCS, REL, 2),  # 176 0xB0
    Instruction("LDA", LDA, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("LAX", LAX, IZY, 5, non_standard=True),
    Instruction("LDY", LDY, ZPX, 4),
    Instruction("LDA", LDA, ZPX, 4),
    Instruction("LDX", LDX, ZPY, 4),
    Instruction("LAX", LAX, ZPY, 4, non_standard=True),  # 0xB7
    Instruction("CLV", CLV, IMP, 2),
    Instruction("LDA", LDA, ABY, 4),
    Instruction("TSX", TSX, IMP, 2),
    Instruction("???", XXX, IMP, 4),
    Instruction("LDY", LDY, ABX, 4),
    Instruction("LDA", LDA, ABX, 4),
    Instruction("LDX", LDX, ABY, 4),
    Instruction("LAX", LAX, ABY, 4, non_standard=True),

    Instruction("CPY", CPY, IMM, 2),  # 192 0xC0
    Instruction("CMP", CMP, IZX, 6),
    Instruction("???", NOP, IMP, 2),
    Instruction("DCP", DCP, IZX, 8, non_standard=True),
    Instruction("CPY", CPY, ZP0, 3),
    Instruction("CMP", CMP, ZP0, 3),
    Instruction("DEC", DEC, ZP0, 5),
    Instruction("DCP", DCP, ZP0, 5, non_standard=True),
    Instruction("INY", INY, IMP, 2),
    Instruction("CMP", CMP, IMM, 2),
    Instruction("DEX", DEX, IMP, 2),
    Instruction("???", XXX, IMP, 2),
    Instruction("CPY", CPY, ABS, 4),
    Instruction("CMP", CMP, ABS, 4),
    Instruction("DEC", DEC, ABS, 6),
    Instruction("DCP", DCP, ABS, 6, non_standard=True),

    Instruction("BNE", BNE, REL, 2),  # 208 0xD0
    Instruction("CMP", CMP, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("DCP", DCP, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),
    Instruction("CMP", CMP, ZPX, 4),
    Instruction("DEC", DEC, ZPX, 6),
    Instruction("DCP", DCP, ZPX, 6, non_standard=True),
    Instruction("CLD", CLD, IMP, 2),
    Instruction("CMP", CMP, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("DCP", DCP, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0xDC
    Instruction("CMP", CMP, ABX, 4),
    Instruction("DEC", DEC, ABX, 7),
    Instruction("DCP", DCP, ABX, 7, non_standard=True),

    Instruction("CPX", CPX, IMM, 2),  # 224 0xE0
    Instruction("SBC", SBC, IZX, 6),
    Instruction("???", NOP, IMP, 2),
    Instruction("ISB", ISB, IZX, 8, non_standard=True),
    Instruction("CPX", CPX, ZP0, 3),
    Instruction("SBC", SBC, ZP0, 3),
    Instruction("INC", INC, ZP0, 5),
    Instruction("ISB", ISB, ZP0, 5, non_standard=True),  # 0xE7
    Instruction("INX", INX, IMP, 2),
    Instruction("SBC", SBC, IMM, 2),
    Instruction("NOP", NOP, IMP, 2),
    Instruction("SBC", SBC, IMM, 2, non_standard=True),
    Instruction("CPX", CPX, ABS, 4),
    Instruction("SBC", SBC, ABS, 4),
    Instruction("INC", INC, ABS, 6),
    Instruction("ISB", ISB, ABS, 6, non_standard=True),

    Instruction("BEQ", BEQ, REL, 2),  # 240 0xF0
    Instruction("SBC", SBC, IZY, 5),
    Instruction("???", XXX, IMP, 2),
    Instruction("ISB", ISB, IZY, 8, non_standard=True),
    Instruction("NOP", NOP, ZPX, 4, non_standard=True),
    Instruction("SBC", SBC, ZPX, 4),
    Instruction("INC", INC, ZPX, 6),
    Instruction("ISB", ISB, ZPX, 6, non_standard=True),  # 0xF7
    Instruction("SED", SED, IMP, 2),
    Instruction("SBC", SBC, ABY, 4),
    Instruction("NOP", NOP, IMP, 2, non_standard=True),
    Instruction("ISB", ISB, ABY, 7, non_standard=True),
    Instruction("NOP", NOP, ABX, 4, non_standard=True),  # 0xFC
    Instruction("SBC", SBC, ABX, 4),
    Instruction("INC", INC, ABX, 7),
    Instruction("ISB", ISB, ABX, 7, non_standard=True)
]


class AsmCPU:
    def __init__(self, addr, bus):
        self.bus = bus
        self.state = CPU6502State()
        self.state.reset()
        self.state.pc = addr

    def cpu_read(self, addr):
        return self.bus.cpu_read(addr, read_only=True)

    def cpu_read_2(self, addr):
        return self.bus.cpu_read_2(addr, read_only=True)

    def get_opcode(self):
        opcode = self.cpu_read(self.state.pc)
        self.state.pc += 1
        return opcode & 0xFF


def disassembler(bus: 'bus.Bus', from_addr, to_addr):
    cpu = AsmCPU(from_addr, bus)
    asm_map = {}
    while cpu.state.pc <= to_addr:
        op_addr = cpu.state.pc & 0xffff
        opcode = cpu.get_opcode()
        instruction = lookup[opcode]
        instruction.addr_mode(cpu)

        if instruction.addr_mode == IMM:
            value = bus.cpu_read(cpu.state.addr_abs)
            mem_addr = f'#${value & 0xff:02X} '
        elif instruction.addr_mode == IMP:
            mem_addr = ''
        elif instruction.addr_mode == REL:
            value = cpu.state.addr_rel & 0xff
            rel = cpu.state.addr_rel | 0xff00
            addr = (cpu.state.pc + rel) & 0xffff
            mem_addr = f'${value:02X} [${addr:04X}] '
        else:
            mem_addr = f'#${cpu.state.addr_abs:04X} '

        op_name = instruction.name
        mode_name = instruction.addr_mode.__name__
        asm = f'${op_addr:04X} {op_name} {mem_addr:<12}{{{mode_name}}}'
        asm_map[op_addr] = asm
    return asm_map
