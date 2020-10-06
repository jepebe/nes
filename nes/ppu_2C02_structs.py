class PPUStatus:
    def __init__(self, reg):
        self.reg = 0x00
        self.set_reg(reg)

    @property
    def unused(self):
        return self.reg & 0x1F

    @property
    def sprite_overflow(self):
        return (self.reg >> 5) & 0x01

    @sprite_overflow.setter
    def sprite_overflow(self, value):
        self.set_bit(5, value)

    @property
    def sprite_zero_hit(self):
        return (self.reg >> 6) & 0x01

    @sprite_zero_hit.setter
    def sprite_zero_hit(self, value):
        self.set_bit(6, value)

    @property
    def vertical_blank(self):
        return (self.reg >> 7) & 0x01

    @vertical_blank.setter
    def vertical_blank(self, value):
        self.set_bit(7, value)

    def set_reg(self, reg):
        self.reg = reg & 0xff

    def set_bit(self, n, value):
        bit = 1 << n
        if value:
            self.reg |= bit
        else:
            self.reg &= ~bit

class PPUMask:
    def __init__(self, reg):
        self.reg = 0x00
        self.set_reg(reg)

    @property
    def grayscale(self):
        return (self.reg >> 0) & 0x01

    @property
    def render_background_left(self):
        return (self.reg >> 1) & 0x01

    @property
    def render_sprites_left(self):
        return (self.reg >> 2) & 0x01

    @property
    def render_background(self):
        return (self.reg >> 3) & 0x01

    @property
    def render_sprites(self):
        return (self.reg >> 4) & 0x01

    @property
    def enhance_red(self):
        return (self.reg >> 5) & 0x01

    @property
    def enhance_green(self):
        return (self.reg >> 6) & 0x01

    @property
    def enhance_blue(self):
        return (self.reg >> 7) & 0x01

    def set_reg(self, reg):
        self.reg = reg & 0xff

    def set_bit(self, n, value):
        bit = 1 << n
        if value:
            self.reg |= bit
        else:
            self.reg &= ~bit


class PPUCtrl:
    def __init__(self, reg):
        self.reg = 0x00
        self.set_reg(reg)

    @property
    def nametable_x(self):
        return (self.reg >> 0) & 0x01

    @property
    def nametable_y(self):
        return (self.reg >> 1) & 0x01

    @property
    def increment_mode(self):
        return (self.reg >> 2) & 0x01

    @property
    def pattern_sprite(self):
        return (self.reg >> 3) & 0x01

    @property
    def pattern_background(self):
        return (self.reg >> 4) & 0x01

    @property
    def sprite_size(self):
        return (self.reg >> 5) & 0x01

    @property
    def slave_mode(self):  # unused
        return (self.reg >> 6) & 0x01

    @property
    def enable_nmi(self):
        return (self.reg >> 7) & 0x01

    def set_reg(self, reg):
        self.reg = reg & 0xff

    def set_bit(self, n, value):
        bit = 1 << n
        if value:
            self.reg |= bit
        else:
            self.reg &= ~bit


class LoopyRegister:
    def __init__(self, reg):
        self.reg = 0x0000
        self.set_reg(reg)

    @property
    def coarse_x(self):
        return self.reg & 0x001F

    @coarse_x.setter
    def coarse_x(self, value):
        self.reg = self.reg & (~0x001f) | (value & 0x001F)

    @property
    def coarse_y(self):
        return (self.reg >> 5) & 0x001F

    @coarse_y.setter
    def coarse_y(self, value):
        self.reg = (self.reg & ~(0x001f << 5)) | (value & 0x001F) << 5

    @property
    def nametable_x(self):
        return (self.reg >> 10) & 0x0001

    @nametable_x.setter
    def nametable_x(self, value):
        self.reg = (self.reg & ~(0x0001 << 10)) | (value & 0x0001) << 10

    @property
    def nametable_y(self):
        return (self.reg >> 11) & 0x0001

    @nametable_y.setter
    def nametable_y(self, value):
        self.reg = (self.reg & ~(0x0001 << 11)) | (value & 0x0001) << 11

    @property
    def fine_y(self):
        return (self.reg >> 12) & 0x07

    @fine_y.setter
    def fine_y(self, value):
        self.reg = (self.reg & ~(0x0007 << 12)) | (value & 0x0007) << 12

    @property
    def unused(self):
        return (self.reg >> 15) & 0x0001

    @unused.setter
    def unused(self, value):
        self.reg = (self.reg & ~(0x0001 << 15)) | (value & 0x0001) << 15

    def set_reg(self, reg):
        self.reg = reg & 0xffff

