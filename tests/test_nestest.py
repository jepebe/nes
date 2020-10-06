import pytest

from _opcodes_6502 import IMM, ZP0, IMP, REL, LSR, ASL, ROR, ROL, IZX, IZY, IND, ABY, \
    ZPX, ZPY, ABX, ABS, JMP, JSR
from bus import Bus
from cartridge import Cartridge
from cpu_6502 import CPU6502State


def color(text, value=0):
    return '\u001b[38;5;%im%s\u001b[0m' % (value, text)


def red(text):
    return color(text, 196)


def green(text):
    return color(text, 34)


def blue(text):
    return color(text, 69)


def yellow(text):
    return color(text, 226)


def print_context(results, index, instruction, mock_cpu, expected_line):
    for i in range(max(index - 25, 0), index + 1):
        result = results[i]
        text = f'{i + 1:<3} -> {result}'
        if i == index:
            text = red(text)
        print(text)
    print(green(f'{index + 1:<3} -> {expected_line}'))
    mock_cpu.cpu_state.print_flags()
    print(instruction.name, instruction.addr_mode.__name__,
          f'{mock_cpu.cpu_state._addr_abs:04X}')


@pytest.fixture
def expected():
    with open('nestest.data', 'r') as f:
        lines = f.readlines()
    yield [line.strip() for line in lines]


class CPU:
    def __init__(self, bus):
        self.bus = bus
        self.fetches = []
        self.cpu_state = CPU6502State()

    def cpu_read(self, addr):
        value = self.bus.cpu_read(addr)
        self.fetches.append(value)
        return value

    def cpu_read_2(self, addr):
        lo, hi = self.bus.cpu_read_2(addr)
        self.fetches.append(lo)
        self.fetches.append(hi)
        return lo, hi

    def reset(self):
        self.bus.cpu.cpu_state.copy_to(self.cpu_state)
        self.fetches.clear()


def clock(nes):
    while True:
        nes.clock()
        if nes.cpu.complete():
            break
    while True:
        nes.clock()
        if not nes.cpu.complete():
            break


def test_nesttest(expected):
    nes = Bus()
    cart = Cartridge('nestest.nes')
    nes.insert_cartridge(cart)

    nes.cpu_write(0xFFFC, 0x00)
    nes.reset()

    assert nes.cpu_read(0xFFFC) == 0x00
    assert nes.cpu_read(0xFFFd) == 0xC0
    while True:
        nes.clock()
        if nes.cpu.complete():
            break

    mock_cpu = CPU(nes)

    results = {}
    print('\n### Nestest ###')
    for index, expected_line in enumerate(expected):
        mock_cpu.reset()

        pc = nes.cpu.cpu_state.pc
        a = nes.cpu.cpu_state.a
        x = nes.cpu.cpu_state.x
        y = nes.cpu.cpu_state.y
        p = nes.cpu.cpu_state.status
        sp = nes.cpu.cpu_state.stkp
        cycle_count = nes.cpu.cpu_state.clock_count
        ppu_cycle = nes.ppu._cycle
        ppu_scanline = nes.ppu._scanline

        opcode = nes.cpu.cpu_read(pc)
        mock_cpu.cpu_state.pc += 1
        instruction = nes.cpu.OPCODES[opcode]

        instruction.addr_mode(mock_cpu.cpu_state, mock_cpu)

        address = create_address_line(nes, mock_cpu, instruction, opcode)
        op_name = f'{instruction.name} {address}'

        op_bytes = f'{opcode:02X}'
        for data in mock_cpu.fetches:
            op_bytes += f' {data:02X}'

        ns = '*' if instruction.is_non_standard else ' '
        result = (f'{pc:04X}  {op_bytes:<9}{ns}{op_name:<32}A:{a:02X} '
                  f'X:{x:02X} Y:{y:02X} P:{p:02X} SP:{sp:02X} '
                  f'PPU:{ppu_scanline:>3},{ppu_cycle:>3} CYC:{cycle_count}')

        results[index] = result
        if not result[:78] == expected_line[:78]:
            print_context(results, index, instruction, mock_cpu, expected_line)

        assert result[:78] == expected_line[:78]
        # print(f'{nes.cpu_read(0xc002):02X} {nes.cpu_read(0xc002):02X}')
        # assert nes.cpu_read(0xc002) == 0x00
        try:
            clock(nes)
        except TypeError:
            msg = f'Operator {instruction.operate.__name__} not implemented!'
            print(red(msg))
            print_context(results, index, instruction, mock_cpu, expected_line)
            raise UserWarning(msg)


def create_address_line(nes, mock_cpu, instruction, opcode):
    if instruction.addr_mode == IMM:
        value = nes.cpu.cpu_read(mock_cpu.cpu_state.pc - 1)
        mock_cpu.fetches.append(value)
        address = f'#${value:02X}'

    elif instruction.addr_mode == IMP:
        address = ''
        if instruction.operate in (LSR, ASL, ROR, ROL):
            address = 'A'

    elif instruction.addr_mode == IZX:
        ptr = mock_cpu.fetches[0]
        addr = mock_cpu.cpu_state._addr_abs & 0xFFFF
        value = nes.cpu.cpu_read(addr)
        dest = (mock_cpu.fetches.pop(-1) << 8) | mock_cpu.fetches.pop(-1)
        ptr_off = (ptr + mock_cpu.cpu_state.x) & 0xFF
        ptr_loc = f'(${ptr:02X},X) @'
        address = f'{ptr_loc} {ptr_off:02X} = {dest:04X} = {value:02X}'

    elif instruction.addr_mode == IZY:
        ptr = mock_cpu.fetches[0]
        addr = mock_cpu.cpu_state._addr_abs & 0xFFFF
        value = nes.cpu.cpu_read(addr)
        dest = (mock_cpu.fetches.pop(-1) << 8) | mock_cpu.fetches.pop(-1)
        ptr_loc = f'(${ptr:02X})'
        address = f'{ptr_loc},Y = {dest:04X} @ {addr:04X} = {value:02X}'

    elif instruction.addr_mode in (ABY, ABX):
        addr = mock_cpu.cpu_state._addr_abs & 0xFFFF
        value = nes.cpu.cpu_read(addr)
        reg = instruction.addr_mode.__name__[-1]
        dest = (mock_cpu.fetches[-1] << 8) | mock_cpu.fetches[-2]
        address = f'${dest:04X},{reg} @ {addr:04X} = {value:02X}'

    elif instruction.addr_mode == IND:
        mock_cpu.fetches.pop(-1)
        mock_cpu.fetches.pop(-1)
        dest = (mock_cpu.fetches[-1] << 8) | mock_cpu.fetches[-2]
        addr = mock_cpu.cpu_state._addr_abs & 0xFFFF
        address = f'(${dest:04X}) = {addr:04X}'

    elif instruction.addr_mode == ZP0:
        addr = mock_cpu.cpu_state._addr_abs & 0x00FF
        value = nes.cpu.cpu_read(addr)
        address = f'${addr :02X} = {value:02X}'

    elif instruction.addr_mode == ZPX:
        ptr = mock_cpu.fetches[0]
        addr = mock_cpu.cpu_state._addr_abs & 0x00FF
        value = nes.cpu.cpu_read(addr)
        address = f'${ptr:02X},X @ {addr:02X} = {value:02X}'

    elif instruction.addr_mode == ZPY:
        ptr = mock_cpu.fetches[0]
        addr = mock_cpu.cpu_state._addr_abs & 0x00FF
        value = nes.cpu.cpu_read(addr)
        address = f'${ptr:02X},Y @ {addr:02X} = {value:02X}'

    elif instruction.addr_mode == REL:
        rel = mock_cpu.cpu_state._addr_rel & 0xFF
        if rel & 0x80:
            rel = -(rel ^ 0xFF) - 1
        addr = mock_cpu.cpu_state.pc + rel
        address = f'${addr:04X}'

    elif instruction.addr_mode == ABS:
        if instruction.operate in (JMP, JSR):
            address = f'${mock_cpu.cpu_state._addr_abs:04X}'
        else:
            addr = mock_cpu.cpu_state._addr_abs
            value = nes.cpu.cpu_read(addr)
            address = f'${addr :04X} = {value:02X}'

    return address
