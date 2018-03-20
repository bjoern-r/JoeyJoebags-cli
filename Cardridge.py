class Cartridge(object):
    """
    Base class for a game Cartridge
    """

    rom_size = 0
    ram_size = 0
    header_bytes = []
    reader = None

    def __init__(self, reader) -> None:
        super().__init__()
        self.reader = reader

    def read_header(self):
        pass


class GbCart(Cartridge):
    """
    Classic GameBoy Cartridge
    5V Signalling
    """

    def read_header(self):
        super().read_header()

    def get_rom_title(self):
        pass


class BennVennM64Cart(GbCart):
    """
    256M Flash Cart with 4 RomBanks
    Each bank is organized as 64M Flash and 128k (4*32k) RAM
    """

    def read_ram(self):
        pass

    def set_bank(self, bank):
        pass


class BennVennM256Cart(BennVennM64Cart):
    """
    256M Flash Cart with 4 RomBanks
    Each bank is organized as 64M Flash and 128k (4*32k) RAM
    """

    def read_ram(self):
        pass


class GbaCart(Cartridge):
    """
    GameBoy Advance Cartridge
    """
    pass
