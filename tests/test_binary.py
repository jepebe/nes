def test_binary_ops():
    a = 0b01101011
    b = 0b00000111
    assert a & b == 0b00000011

    c = 0b00011000

    assert (a & c) >> 3 == 0b00000001

    assert a & 0b00100000
    assert a & 0x20
    assert 0x20 == 0b00100000
    assert not a & 0b00010000

    d = 0b10000000
    e = 0b101 << 2
    d |= e
    assert d == 0b10010100
    print(hex(d), hex(~d & 0xff), hex(0b01101011))
    assert (~d & 0xff) == 0b01101011

    f = 0b10111011
    g = 0b00100000
    assert f ^ g == 0b10011011
