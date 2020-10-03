from nes.bus import Bus


def test_ram():
    bus = Bus()

    for addr in range(0x0000, 0x800):
        bus.cpu_write(addr, 0xff)
        assert bus.cpu_read(addr) == 0xff
