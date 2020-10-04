from nes.bus import Bus

class TestCartridge:
    def cpu_write(self, addt, value):
        return None

    def cpu_read(self, addr):
        return None


def test_ram():
    bus = Bus()
    bus.insert_cartridge(TestCartridge())

    for addr in range(0x0000, 0x800):
        bus.cpu_write(addr, 0xff)
        assert bus.cpu_read(addr) == 0xff

    bus.cpu_write(0x700, 0x7f)
    assert bus.cpu_read(0x700) == 0x7f
    assert bus.cpu_read(0x700 + 0x800) == 0x7f
    assert bus.cpu_read(0x700 + 0x800 * 2) == 0x7f
    assert bus.cpu_read(0x700 + 0x800 * 3) == 0x7f

