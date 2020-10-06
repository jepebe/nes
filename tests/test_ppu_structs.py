from ppu_2C02_structs import PPUStatus, LoopyRegister


def test_status():
    status = PPUStatus(0xff)
    assert status.vertical_blank == 1
    status.vertical_blank = 0
    assert status.vertical_blank == 0

    status.sprite_overflow = 0
    assert status.sprite_overflow == 0

    status.sprite_zero_hit = 0
    assert status.sprite_zero_hit == 0

    assert status.unused == 0x1F


def test_loop_register():
    lr = LoopyRegister(0xffff)

    assert lr.coarse_x == 0x1F
    lr.coarse_x = 0b10101
    assert lr.coarse_x == 0b10101

    assert lr.coarse_y == 0x1F

    lr.coarse_y = 0b01110
    assert lr.coarse_y == 0b01110
    assert lr.coarse_x == 0b10101

    assert lr.nametable_x == 0x01
    lr.nametable_x = 0x00
    assert lr.nametable_x == 0x00
    assert lr.coarse_y == 0b01110
    assert lr.coarse_x == 0b10101

    assert lr.nametable_y == 0x01
    lr.nametable_y = 0x00
    assert lr.nametable_y == 0x00
    assert lr.nametable_x == 0x00
    assert lr.coarse_y == 0b01110
    assert lr.coarse_x == 0b10101

    assert lr.fine_y == 0b111
    lr.fine_y = 0b010
    assert lr.fine_y == 0b010
    assert lr.nametable_y == 0x00
    assert lr.nametable_x == 0x00
    assert lr.coarse_y == 0b01110
    assert lr.coarse_x == 0b10101

    assert lr.unused == 0x01
    lr.unused = 0x00
    assert lr.unused == 0x00
    assert lr.fine_y == 0b010
    assert lr.nametable_y == 0x00
    assert lr.nametable_x == 0x00
    assert lr.coarse_y == 0b01110
    assert lr.coarse_x == 0b10101

    lr.nametable_x = ~lr.nametable_x
    assert lr.nametable_x == 1
    lr.nametable_y = ~lr.nametable_y
    assert lr.nametable_y == 1

    lr.fine_y = 0b101
    assert lr.fine_y == 0b101
    # print(f'{lr.reg:0b}')