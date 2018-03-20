import usb.core
import usb.util


def dbg(text):
    print("+DBG", text)


class Programmer(object):
    def diconnect(self):
        pass


class JoeyJoebags(Programmer):
    _command = dict(Get_Version=[0x00], Get_ROM=[0x10], Set_Bank=[0x08], Flash_ROM=[0x20])
    _Command_Get_Version = [0x00]
    _Command_Get_ROM = [0x10]
    _Command_Set_Bank = [0x08]
    _Command_Flash_ROM = [0x20]

    def __init__(self) -> None:
        super().__init__()
        self._dev = usb.core.find(idVendor=0x046d, idProduct=0x1234)

    def diconnect(self):
        usb.util.dispose_resources(self._dev)

    def get_version(self):
        self._dev.write(0x01, self._Command_Get_Version)
        dat = self._dev.read(0x81, 64)
        sdat = ""
        for x in range(5):
            sdat = sdat + chr(dat[x])
        D = (SDID_Read())
        dbg("Data: %s" % dat)
        dbg("Firmware " + sdat + " Device ID: " + D)

        return sdat, D

    def get_key_state(self):
        pass

    def update_firmware(self):
        pass

    def update_firmware_legacy(self):
        pass

    def set_bank(self, bank):
        pass

    def flash_rom(self, address, data):
        pass

    def get_rom(self, address):
        pass
