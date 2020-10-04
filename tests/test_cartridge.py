from cartridge import Cartridge
from mapper import Mapper000


def test_load():
    cart = Cartridge('nestest.nes')
    assert cart.mapper_id == 0
    assert cart.prg_banks == 1
    assert cart.chr_banks == 1
    assert len(cart.prg_memory) == 16384
    assert len(cart.chr_memory) == 8192


def test_mapper_000():
    mapper1 = Mapper000(1, 1)
    mapper2 = Mapper000(2, 2)

    assert mapper1.cpu_map_read(0x0000) is None
    assert mapper1.cpu_map_read(0x80FF) == 0xFF
    assert mapper1.cpu_map_read(0xA0FF) == 0x20FF
    assert mapper1.cpu_map_read(0xC0FF) == 0xFF

    assert mapper2.cpu_map_read(0x0000) is None
    assert mapper2.cpu_map_read(0x80FF) == 0xFF
    assert mapper1.cpu_map_read(0xA0FF) == 0x20FF
    assert mapper2.cpu_map_read(0xC0FF) == 0x40FF

    assert mapper1.ppu_map_read(0x2000) is None
    assert mapper2.ppu_map_read(0x2000) is None
    assert mapper1.ppu_map_read(0x00FF) == 0x00FF
    assert mapper2.ppu_map_read(0x00FF) == 0x00FF
