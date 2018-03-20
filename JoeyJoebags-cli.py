import string

import usb.core
import usb.util
# import sys
# import itertools
import time
import binascii
from optparse import OptionParser

ROMsize = 0
RAMsize = 0
BankSize = 0
ROMbuffer = ""
RAMbuffer = ""
USBbuffer = ""
FlashBlockSize = 0

for usbfill in range(64):
    USBbuffer = USBbuffer + "\x00"

Command_Get_Version = [0x00]
Command_Get_ROM = [0x10]
Command_Set_Bank = [0x08]
Command_Flash_ROM = [0x20]

CMD_Autoselect_0001 = [0x0A, 0x01, 0x04,
                       0x55, 0x55, 0xAA,
                       0x2A, 0xAA, 0x55,
                       0x55, 0x55, 0x90,
                       0x00, 0x00, 0x01]
CMD_Autoselect_01a4 = [0x0A, 0x01, 0x04,
                       0x55, 0x55, 0xAA,
                       0x2A, 0xAA, 0x55,
                       0x55, 0x55, 0xa0,
                       0x00, 0x01, 0xa4]
CMD_ChipErase = [0x0A, 0x01, 0x06, # byte mode ... 6 cycles
                 0x55, 0x55, 0xAA,  # cycle 1 (0x5555 <- 0xAA)
                 0x2A, 0xAA, 0x55,  # cycle 2 (0x2AAA <- 0x55)
                 0x55, 0x55, 0x80,  # cycle 3 (0x5555 <- 0x80)
                 0x55, 0x55, 0xAA,  # cycle 4 (0x5555 <- 0xAA)
                 0x2A, 0xAA, 0x55,  # cycle 5 (0x2AAA <- 0x55)
                 0x55, 0x55, 0x10]  # cycle 6 (0x5555 <- 0x10) Chip Erase command
CMD_Autoselect_DevID = [0x0A, 0x01, 0x04, # 4 cycles
                        0x0A, 0xAA, 0xAA, # cycle 1 (0x0AAA <- 0xAA)
                        0x05, 0x55, 0x55, # cycle 2 (0x2AAA <- 0x55)
                        0x0A, 0xAA, 0x90, ## 
                        0x00, 0x01, 0x00] ## actually read this address ...
CMD_BV5_Erase = [0x0A, 0x01, 0x06, # 6 cycles, byte mode?
                 0x0A, 0xAA, 0xA9, 
                 0x05, 0x55, 0x56, 
                 0x0A, 0xAA, 0x80, 
                 0x0A, 0xAA, 0xA9, 
                 0x05, 0x55, 0x56, 
                 0x0A, 0xAA, 0x10]
# 886_DRV erase code
# 2100 <- 34
# 4000 <- F0  //reset
# 0555 <- A9  //
# 02AA <- 56
# 0555 <- 80
# 0555 <- A9
# 02AA <- 56
# 4000 <- 30  // erase sector 4000 ??
# while read 4000 != FF
# 4000 <- F0


class messagebox(object):
    @staticmethod
    def showinfo(text, waitforenter=True):
        print("%s" % text)
        if waitforenter:
            result = input("Press <enter> to continue. ")
            print("\n")
            return result
        print()


# ----------------

def hexdump( src, length=16, sep='.' ):
    '''
    @brief Return {src} in hex dump.
    @param[in] length   {Int} Nb Bytes by row.
    @param[in] sep      {Char} For the text part, {sep} will be used for non ASCII char.
    @return {Str} The hexdump
    @note Full support for python2 and python3 !
    '''
    result = [];

    # Python3 support
    try:
        xrange(0,1);
    except NameError:
        xrange = range;

    for i in xrange(0, len(src), length):
        subSrc = src[i:i+length];
        hexa = '';
        isMiddle = False;
        for h in xrange(0,len(subSrc)):
            if h == length/2:
                hexa += ' ';
            h = subSrc[h];
            if not isinstance(h, int):
                h = ord(h);
            h = hex(h).replace('0x','');
            if len(h) == 1:
                h = '0'+h;
            hexa += h+' ';
        hexa = hexa.strip(' ');
        text = '';
        for c in subSrc:
            if not isinstance(c, int):
                c = ord(c);
            if 0x20 <= c < 0x7F:
                text += chr(c);
            else:
                text += sep;
        result.append(('%08X:  %-'+str(length*(2+1)+1)+'s  |%s|') % (i, hexa, text));

    return '\n'.join(result);

def dispose_USB(dev):
    usb.util.dispose_resources(dev)


def main_Header():
    global ROMsize
    global RAMsize
    Header = ""
    dev.write(0x01, [0x10, 0x00, 0x00, 0x01, 0x00])  # start of logo
    dat = dev.read(0x81, 64)
    Header = dat
    msg = [0x10, 0x00, 0x00, 0x01, 0x40]  #
    dev.write(0x01, msg)
    dat = dev.read(0x81, 64)
    Header += dat
    msg = [0x10, 0x00, 0x00, 0x01, 0x80]  #
    dev.write(0x01, msg)
    dat = dev.read(0x81, 64)
    Header += dat  # Header contains 0xC0 bytes of header data
    print("ROM Title: " + str(Header[0x34:0x43]))


def main_readCartHeader():
    main_BV_SetBank(0, 0)
    main_ROMBankSwitch(1)
    RAMtypes = [0, 2048, 8192, 32768, (32768 * 4), (32768 * 2)]
    global ROMsize
    global RAMsize
    Header = ""
    dev.write(0x01, [0x10, 0x00, 0x00, 0x01, 0x00])  # start of logo
    dat = dev.read(0x81, 64)
    Header = dat
    msg = [0x10, 0x00, 0x00, 0x01, 0x40]  #
    dev.write(0x01, msg)
    dat = dev.read(0x81, 64)
    Header += dat
    msg = [0x10, 0x00, 0x00, 0x01, 0x80]  #
    dev.write(0x01, msg)
    dat = dev.read(0x81, 64)
    Header += dat  # Header contains 0xC0 bytes of header data
    try:
        ROMsize = (32768 * (2 ** (Header[0x48])))
    except Exception as e:
        ROMsize = 0
    try:
        RAMsize = RAMtypes[Header[0x49]]
    except Exception as e:
        RAMsize = 0

    print("ROM Title: ", str(Header[0x34:0x43], 'utf-8', "ignore"))
    print("ROM Size: %d [%s]" % (ROMsize, hex(Header[0x48])))
    print("RAM Size: %d [%s]" % (RAMsize, hex(Header[0x48])))
    print("+[DBG] Header: len: %d 0x%x"%(len(Header),len(Header)))
    print(hexdump(Header))


def main_CheckVersion():
    dev.write(0x01, Command_Get_Version)
    dat = dev.read(0x81, 64)
    sdat = ""
    for x in range(5):
        sdat = sdat + chr(dat[x])
    D = (SDID_Read())
    print("Firmware " + sdat + " Device ID: " + D)


def SDID_Read():
    dev.write(0x01, [0x80])
    USBbuffer = dev.read(0x81, 64)
    A = (USBbuffer[0]) + (USBbuffer[1] << 8) + (USBbuffer[2] << 16) + (USBbuffer[3] << 24)
    B = (USBbuffer[4]) + (USBbuffer[5] << 8) + (USBbuffer[6] << 16) + (USBbuffer[7] << 24)
    C = (USBbuffer[8]) + (USBbuffer[9] << 8) + (USBbuffer[10] << 16) + (USBbuffer[11] << 24)
    D = str(hex(A)) + "," + str(hex(B)) + "," + str(hex(C))
    return (D)


def main_BV_lockBank(bnum):
    # Lock cart before writing
    bnum = bnum + 0x90
    print('Flash locked to ', hex(bnum))
    dev.write(0x01, [0x0A, 0x00, 0x03, 0x70, 0x00, 0x00, 0x70, 0x01, 0x00, 0x70, 0x02, bnum])  # Lock flash block
    USBbuffer = dev.read(0x81, 64)


def main_BV_SetBank(blk, sublk):  # 1-4:1-4
    # Lock cart before writing
    sublk = sublk * 64
    print("+[DBG] BV setBank:", hex(blk), hex(sublk))
    dev.write(0x01, [0x0A, 0x00, 0x03, 0x70, 0x00, sublk, 0x70, 0x01, 0xE0, 0x70, 0x02, blk])  # Lock flash block
    USBbuffer = dev.read(0x81, 64)


def main_BV_Flash_ROM(block, options):
    FFtest = ""
    FFtest = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
    # ZZtest=b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    if main_LoadROM(options) == 1:
        FlashBlockSize = 131072
        messagebox.showinfo('Please remove and insert Flash cart, then click OK')
        main_BV_lockBank(block)
        print('from flashrom() ', ROMsize, FlashBlockSize)
        NumOfBlks = int(ROMsize / FlashBlockSize)
        if NumOfBlks == 0:
            NumOfBlks = 1
        print('erasing %d Blocks' % NumOfBlks)
        print('Erasing ROM Area required for flash')
        for blknum in range(0, NumOfBlks):
            main_BV_EraseFlashBlock(blknum, quiet=True)

        print('Writing ROM Data')
        ROMpos = 0
        waitcount = 0
        for BankNumber in range(0, int((ROMsize / 16384))):
            main_ROMBankSwitch(BankNumber)  # Set the bank
            print(BankNumber * 16384, ' of ', ROMsize)
            for ROMAddress in range(0x4000, 0x8000, 32):
                if BankNumber == 0:
                    ROMAddress = ROMAddress - 0x4000
                AddHi = ROMAddress >> 8
                AddLo = ROMAddress & 0xFF
                Data32Bytes = ROMbuffer[ROMpos:ROMpos + 32]
                if Data32Bytes == FFtest:
                    pass
                # elif Data32Bytes == ZZtest:
                #	pass
                else:
                    AddHi = AddHi.to_bytes(1, 'little')
                    AddLo = AddLo.to_bytes(1, 'little')
                    FlashWriteCommand = b'\x20\x00\x04\x2A\x0A\xAA\xA9\x05\x55\x56' + AddHi + AddLo + b'\x26' + AddHi + AddLo + b'\x1F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                    USBoutputPacket = FlashWriteCommand + Data32Bytes
                    dev.write(0x01, USBoutputPacket)
                    while main_IsFlashBusy() == 1:
                        pass
                        waitcount += 1
                        if waitcount == 10:
                            print('Error: ', USBoutputPacket, BankNumber, AddHi, AddLo, ROMpos)
                    waitcount = 0
                ROMpos += 32
        print("Done:", str(ROMsize) + ' Bytes Written')
        messagebox.showinfo('Writing Complete. Please remove and insert Flash cart, then click OK')


# MBC Generic Specific Code Goes here:
def main_MBC_Dump_ROM(size=None):
    global BankSize
    BankSize = 16384  # bytes per bank
    if size is None:
        main_readCartHeader()
    else:
        global ROMsize
        ROMsize = size
    main_dumpROM()


# BV64 Specific Code Goes here:
def main_BV64_Dump_ROM(ROMBlk):
    global BankSize
    global ROMsize
    BankSize = 16384  # bytes per bank
    ROMsize = int(64 * 1024 * 1024 / 8)
    main_BV_SetBank(ROMBlk, 0)
    main_dumpROM()


# Universal routines
def main_dumpROM():
    global ROMbuffer
    global USBbuffer
    # ROMfileName = asksaveasfilename(defaultextension=".GB", filetypes=(
    #    ("GB ROM File", "*.GB"), ("GBC ROM File", "*.GBC"), ("GBA ROM File", "*.GBA"), ("All Files", "*.*")))
    ROMfileName = options.romfile
    if ROMfileName:
        ROMfile = open(ROMfileName, 'wb')
        for bankNumber in range(0, (int(ROMsize / BankSize))):
            print('Dumping ROM:', int(bankNumber * BankSize), ' of ', ROMsize)
            if bankNumber == 0:
                ROMaddress = 0  # get bank 0 from address 0, not setbank(0) and get from high bank...
            else:
                ROMaddress = BankSize
            main_ROMBankSwitch(bankNumber)  # switch to new bank.
            for packetNumber in range(0, (int(BankSize / 64))):
                AddHi = ROMaddress >> 8
                AddLo = ROMaddress & 0xFF
                dev.write(0x01, [0x10, 0x00, 0x00, AddHi, AddLo])
                ROMbuffer = dev.read(0x81, 64)
                ROMfile.write(ROMbuffer)
                ROMaddress += 64
        ROMfile.close()
        print('Done!')


def main_IsFlashBusy():
    dev.write(0x01, [0x0B, 0x00])  # IsFlashBusy?
    temp = dev.read(0x81, 64)
    if temp[0] == 0x01:
        return (1)
    if temp[0] == 0x00:
        return (0)


def main_BV_EraseFlashBlock(BlockNum, quiet=False):  # 1 block = 128kbytes of ROM (BV cart)
    main_ROMBankSwitch(BlockNum * 8)
    if not quiet:
        print('Erasing Block ' + str(BlockNum))
    dev.write(0x01,
              [0x0A, 0x00, 0x06, 0x0A, 0xAA, 0xA9, 0x05, 0x55, 0x56, 0x0A, 0xAA, 0x80, 0x0A, 0xAA, 0xA9, 0x05, 0x55,
               0x56, 0x40, 0x00, 0x30])
    USBbuffer = dev.read(0x81, 64)
    waitcount = 0
    while main_IsFlashBusy() == 1:
        waitcount += 1
        if waitcount == 100000:
            print('Error: ', BlockNum)
            exit()
    if not quiet:
        print('Done')
    return True


def main_ROMBankSwitch(bankNumber):
    # Convert 16bit bank number to 2 x 8bit numbers
    # Write to address defined under MBC settings to swap banks. This will change depending on certain cart types...
    bhi = bankNumber >> 8
    blo = bankNumber & 0xFF
    if bhi > 0:
        dev.write(0x01, [0x0A, 0x00, 0x01, 0x30, 0x00, bhi])
        USBbuffer = dev.read(0x81, 64)
    dev.write(0x01, [0x0A, 0x00, 0x01, 0x21, 0x00, blo])
    USBbuffer = dev.read(0x81, 64)


def main_RAMBankSwitch(bankNumber):
    print("Bank:" + str(bankNumber))
    # Convert 16bit bank number to 2 x 8bit numbers
    # Write to address defined under MBC settings to swap banks. This will change depending on certain cart types...
    blo = bankNumber & 0xFF
    dev.write(0x01, [0x0A, 0x00, 0x01, 0x40, 0x00, blo])
    USBbuffer = dev.read(0x81, 64)


def main_BV5_Erase():
    print("Erasing...")
    dev.write(0x01,
              [0x0A, 0x01, 0x06, 0x0A, 0xAA, 0xA9, 0x05, 0x55, 0x56, 0x0A, 0xAA, 0x80, 0x0A, 0xAA, 0xA9, 0x05, 0x55,
               0x56, 0x0A, 0xAA, 0x10])
    RAMbuffer = dev.read(0x81, 64)
    while main_ELCheapo_Read(0)[0] != 0xFF:
        time.sleep(0.1)
        print(main_ELCheapo_Read(0))
        pass
    print("Erased")


def main_BV5_Write(options):
    if main_LoadROM(options) == 1:
        print('Writing ROM Data')
        main_BV5_Erase()
        ROMpos = 0
        waitcount = 0
        for BankNumber in range(0, int((ROMsize / 16384))):
            main_ROMBankSwitch(BankNumber)  # Set the bank
            print(BankNumber * 16384, ' of ', ROMsize)
            for ROMAddress in range(0x4000, 0x8000, 32):
                #            if BankNumber==0:
                #                ROMAddress=ROMAddress-0x4000
                AddHi = ROMAddress >> 8
                AddLo = ROMAddress & 0xFF
                Data32Bytes = ROMbuffer[ROMpos:ROMpos + 32]

                # byte by byte write, its slow....

                AddHi = AddHi.to_bytes(1, 'little')
                AddLo = AddLo.to_bytes(1, 'little')

                FlashWriteCommand = b'\x27\x00' + AddHi + AddLo
                USBoutputPacket = FlashWriteCommand + Data32Bytes
                dev.write(0x01, USBoutputPacket)
                USBbuffer = dev.read(0x81, 64)

                ROMpos += 32
        app.lowerLeftLabel.set(str(ROMsize) + ' Bytes Written')
        messagebox.showinfo('Writing Complete.')
        # return to read mode - datasheet says write 0xFF to any address
        main_ROMBankSwitch(0)

def main_ELCheapoSD_Erase():
    print("Erasing...")

    dev.write(0x01, [0x0A, 0x00, 0x01, 0x00, 0x00, 0x05])  # Enable WE and SPI
    USBbuffer = dev.read(0x81, 64)

    dev.write(0x01,
              [0x0A, 0x00, 0x06, 0x0A, 0xAA, 0xAA, 0x05, 0x55, 0x55, 0x0A, 0xAA, 0x80, 0x0A, 0xAA, 0xAA, 0x05, 0x55,
               0x55, 0x0A, 0xAA, 0x10])
    RAMbuffer = dev.read(0x81, 64)
    while main_ELCheapo_Read(0)[0] != 0xFF:
        time.sleep(0.2)
        print(main_ELCheapo_Read(0))
        pass
    print("Erased")

def main_ELCheapo_Read(Address):
    AddHi = Address >> 8
    AddLo = Address & 0xFF
    dev.write(0x01, [0x10, 0x00, 0x00, AddHi, AddLo])
    ROMbuffer = dev.read(0x81, 64)
    return (ROMbuffer)


def main_ELCheapo_Erase():
    print("Erasing...")
    dev.write(0x01, CMD_ChipErase)
    RAMbuffer = dev.read(0x81, 64)
    while main_ELCheapo_Read(0)[0] != 0xFF:
        time.sleep(0.2)
        print(".")
        pass
    print("Erased")


def main_ELCheapo_Write():
    main_LoadROM()
    print('Writing ROM Data')
    main_ELCheapo_Erase()
    ROMpos = 0
    waitcount = 0
    for BankNumber in range(0, int((ROMsize / 16384))):
        main_ROMBankSwitch(BankNumber)  # Set the bank
        print(BankNumber * 16384, ' of ', ROMsize)
        for ROMAddress in range(0x4000, 0x8000, 32):
            if BankNumber == 0:
                ROMAddress = ROMAddress - 0x4000
            AddHi = ROMAddress >> 8
            AddLo = ROMAddress & 0xFF
            Data32Bytes = ROMbuffer[ROMpos:ROMpos + 32]

            # byte by byte write, its slow....

            AddHi = AddHi.to_bytes(1, 'little')
            AddLo = AddLo.to_bytes(1, 'little')

            FlashWriteCommand = b'\x24\x00' + AddHi + AddLo
            USBoutputPacket = FlashWriteCommand + Data32Bytes
            dev.write(0x01, USBoutputPacket)
            USBbuffer = dev.read(0x81, 64)

            ROMpos += 32
    app.lowerLeftLabel.set(str(ROMsize) + ' Bytes Written')
    messagebox.showinfo('Writing Complete.')
    # return to read mode - datasheet says write 0xFF to any address
    main_ROMBankSwitch(0)


def main_Catskull_write():
    if main_LoadROM() == 1:
        main_ELCheapo_Erase()
        print('Writing ROM Data')
        ROMpos = 0
        for ROMAddress in range(0x0000, 0x8000, 1):
            AddHi = ROMAddress >> 8
            AddLo = ROMAddress & 0xFF
            Data1Byte = ROMbuffer[ROMpos:ROMpos + 1]
            dev.write(0x01, [0x0A, 0x01, 0x04,
                             0x55, 0x55, 0xAA,
                             0x2A, 0xAA, 0x55,
                             0x55, 0x55, 0xA0,
                             AddHi, AddLo, Data1Byte[0]])
            ROMpos += 1
        messagebox.showinfo('Writing Complete.')
    return

def main_Catskull_erase():
    print("Erasing...")
    dev.write(0x01,
              [0x0A, 0x01, 0x06,
               0x55, 0x55, 0xAA,  # cycle 1 (0x5555 <- 0xAA)
               0x2A, 0xAA, 0x55,  # cycle 2 (0x2AAA <- 0x55)
               0x55, 0x55, 0x80,  # cycle 3 (0x5555 <- 0x80)
               0x55, 0x55, 0xAA,  # cycle 4 (0x5555 <- 0xAA)
               0x2A, 0xAA, 0x55,  # cycle 5 (0x2AAA <- 0x55)
               0x55, 0x55, 0x10])  #cycle 6 (0x5555 <- 0x10) Chip Erase command
    RAMbuffer = dev.read(0x81, 64)
    while main_ELCheapo_Read(0)[0] != 0xFF:
        pass
    print("Erased")

def br_dev_id():
    data = [0x0A, 0x01, 0x03, # 4 cycles
            0x0A, 0xAA, 0xAA, # cycle 1 (0x0AAA <- 0xAA)
            0x05, 0x55, 0x55, # cycle 2 (0x2AAA <- 0x55)
            0x0A, 0xAA, 0x90] # cycle 3
            #0x00, 0x01, 0x00] ## actually read this address ...
    data = [0x10, 0x00, 0x04, # 4 cycles
            0x0A, 0xAA, 0xAA, # cycle 1 (0x0AAA <- 0xAA)
            0x05, 0x55, 0x55, # cycle 2 (0x2AAA <- 0x55)
            0x0A, 0xAA, 0x90, # cycle 3
            0x00, 0x01, 0x00] ## actually read this address ...
    data = [0x0a, 0x01, 0x03, # 4 cycles AMD
            0x55, 0x55, 0xAA, # cycle 1 (0x0AAA <- 0xAA)
            0x2A, 0xAA, 0x55, # cycle 2 (0x2AAA <- 0x55)
            0x55, 0x55, 0x90]#, # cycle 3
            #0x00, 0x01, 0x00] ## actually read this address ...
    print("entering Automatic select Mode...")
    ret = dev.write(0x01, data)
    print("write: ret: %s"%(ret))
    print(hexdump(data))
    ret = dev.read(0x81, 64)
    #print("Read:")
    #print(hexdump(ret))
    for foo in range(0,2):
        print("Read[%d]"%foo)
        ret = main_ELCheapo_Read(foo)
        print(hexdump(ret[:16]))

    dev.write(0x01, [0x0A, 0x00, 0x01, # reset
                     0x00, 0x00, 0xF0])
    dev.read(0x81, 64)

def read_sector_lock(sector_address):
    data = [0x0a, 0x01, 0x03, # 4 cycles AMD
        0x55, 0x55, 0xAA, # cycle 1 (0x0AAA <- 0xAA)
        0x2A, 0xAA, 0x55, # cycle 2 (0x2AAA <- 0x55)
        0x55, 0x55, 0x90]#, # cycle 3
        #0x00, 0x01, 0x00] ## actually read this address ...
    print("entering Automselect Mode...")
    ret = dev.write(0x01, data)
    print("write: ret: %s"%(ret))
    print(hexdump(data))
    ret = dev.read(0x81, 64)
    print("Read:")
    print(hexdump(ret))
    addr=((sector_address & 0xff)<<8)|(0x02)
    ret = main_ELCheapo_Read(addr)
    print("Read: SA=0x%02x addr=0x%04x DQ0=%d" % (sector_address, addr,ret[0]&0x01))
    print(hexdump(ret[:8]))



def main_LoadROM(options):
    global ROMsize
    global ROMbuffer
    # ROMfileName=askopenfilename(filetypes=(("GB ROM File","*.GB"),("GBC ROM File","*.GBC"),("GBA ROM File","*.GBA"),("All Files","*.*")))
    ROMfileName = options.romfile
    if ROMfileName:
        ROMfile = open(ROMfileName, 'rb')
        ROMbuffer = ROMfile.read()
        ROMsize = len(ROMbuffer)
        ROMfile.close()
        return (1)
    return (0)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--info", dest="readinfo",
                      help="Read Card INFO",
                      action="store_true")

    parser.add_option("-f", "--rom", dest="romfile",
                      help="ROM filename")
    parser.add_option("-s", "--sav", dest="savfile",
                      help="SAV filename")

    parser.add_option("-b", "--block", dest="romblock",
                      help="ROM block number (BV256 -> 0,1,2,3)", default=0)

    parser.add_option("-F", "--flash", dest="do_flash",
                      help="Write ROMfile to Flash", action="store_true")

    parser.add_option("-R", "--read-rom", dest="do_read_rom",
                      help="Read Rom to ROMfile", action="store_true")
 
    parser.add_option("-E", "--erase-bv5", dest="do_erase_bv5",
                      help="Erase BV5 Cart", action="store_true")

    parser.add_option("-X", "--chip-id", dest="do_chipid",
                      help="send MX29LV320E DevID command", action="store_true")

    (options, args) = parser.parse_args()

    dev = usb.core.find(idVendor=0x046d, idProduct=0x1234)
    if dev is None:
        messagebox.showinfo("Note", "I Cant find your hardware! Check the device is plugged in and the USB driver is installed")
        exit()
    if dev is not None:
        dev.set_configuration()
        messagebox.showinfo("Gen3 is a work in progress, please report any bugs or requests to Bennvenn@hotmail.com",
                            waitforenter=False)
        main_CheckVersion()

        if options.readinfo:
            cnt = 0
            while True:
                print("Round %d"%cnt)
                main_readCartHeader()
                time.sleep(0.2)
                cnt+=1

        if options.do_flash:
            romblock = int(options.romblock)
            print("Writing to ROM block %d" % romblock)
            main_BV_Flash_ROM(romblock, options)
        elif options.do_read_rom:
            romblock = int(options.romblock)
            # print("Reading from ROM block %d to file %s" % (romblock, options.romfile))
            # main_BV64_Dump_ROM(romblock)
            if not options.readinfo:
                read_size=524288
            else:
                read_size=None
            print("reading %s bytes from cart"%read_size)
            main_MBC_Dump_ROM(read_size)
        elif options.do_erase_bv5:
            print("about to erase the cart... ctrl+c to cancel")
            result = input("about to erase the cart... ctrl+c to cancel. Press <enter> to continue. ")
            #main_BV5_Erase()
            #main_ELCheapoSD_Erase()
            main_Catskull_erase()
        elif options.do_chipid:
            #main_readCartHeader()
            #br_dev_id()
            #br_dev_id()
            read_sector_lock(0)
            read_sector_lock(1)

        dispose_USB(dev)
