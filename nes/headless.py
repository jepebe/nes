import time

from bus import Bus
from cartridge import Cartridge

if __name__ == '__main__':
    nes = Bus()
    # cart = Cartridge('tests/nestest.nes')
    cart = Cartridge('roms/donkeykong.nes')
    # cart = Cartridge('roms/smb.nes')
    # cart = Cartridge('roms/ducktales.nes')
    nes.insert_cartridge(cart)

    nes.reset()

    frame_count = 20
    now = time.time()
    while True:
        nes.clock()
        if nes.ppu.frame_count == frame_count:
            break
    diff = time.time() - now

    print('------------')
    print(f'Ran for {frame_count} frames.')
    print(f'Running time: {diff:.{2}f} seconds')
    print(f'Frames per second: {frame_count / diff:.{3}f} FPS')
    print(f'Quality (60 FPS expected): {(frame_count / diff) / 60:.{2}f}')

    # Best so far:
    # 2020-10-06
    # Ran for 20 frames.
    # Running time: 9.36 seconds
    # Frames per second: 2.138 FPS
    # Quality (60 FPS expected): 0.04
