import hid
import time
import sys
import os
import struct
import logging


__version__ = '0.1.0'


class FT260_I2C():

    """
    Key to symbols
    ==============

    S     (1 bit) : Start bit
    P     (1 bit) : Stop bit
    Rd/Wr (1 bit) : Read/Write bit. Rd equals 1, Wr equals 0.
    A, NA (1 bit) : Accept and reverse accept bit.
    Addr  (7 bits): I2C 7 bit address. Note that this can be expanded as usual to
                    get a 10 bit I2C address.
    Comm  (8 bits): Command byte, a data byte which often selects a register on
                    the device.
    Data  (8 bits): A plain data byte. Sometimes, I write DataLow, DataHigh
                    for 16 bit data.
    Count (8 bits): A data byte containing the length of a block operation.

    [..]: Data sent by I2C device, as opposed to data sent by the host adapter.

    More detail documentation is at https://www.kernel.org/doc/Documentation/i2c/smbus-protocol

    This is a pure Python implementation of the I2C protocol for FTDI FT260.
    It is traying to by compatible with the smbus2 library as much as possible.
    
    This library was developed as part of MLAB project. Visit https://mlab.cz for more information.
    """

    def __init__(self, hid_device=None, vid=None, pid=None, *args, **kwargs):
        if hid_device is not None:
            self.dev = hid_device

        ## TODO: S timhle si nejsem stoprocentne jisty, jak to nejlepe udelat. 
        elif vid is not None and pid is not None:
            self.dev = hid.device()
            self.dev.open(vid, pid)
        else:
            raise ValueError("Either hid_device or vid and pid must be provided.")

        self.initialize_ftdi()
        self.driver_type = 'ft260_hid'
        self.dev = hid_device
        self.initialize_ftdi()

        return True


    def initialize_ftdi(self):

        self.reset_i2c()
        #self.set_i2c_speed(100000) # 100 Khz
        self.get_i2c_status()

    
    def reset_i2c(self):
        self.device.send_feature_report([0xA1, 0x20])
        
    def set_i2c_speed(self, speed = 100000):
        speed = int(speed/1000)
        LSB = (speed & 0xff)
        MSB = (speed>>8 & 0xff)
        print(f"Set i2c rate to {speed} Hz: ", hex(LSB), hex(MSB))
        self.device.send_feature_report([0xA1, 0x22, LSB, MSB])


    def write_byte(self, address, value):
        """
        SMBus Send Byte:  i2c_smbus_write_byte()
        ========================================

        This operation is the reverse of Receive Byte: it sends a single byte
        to a device.  See Receive Byte for more information.

        S Addr Wr [A] Data [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_BYTE
        """

        payload = [0xD0, address, 0x06, 1, value]
        self.device.write(payload)


    def read_byte(self, address):
        """
        SMBus Send Byte:  i2c_smbus_write_byte()
        ========================================

        This operation is the reverse of Receive Byte: it sends a single byte
        to a device.  See Receive Byte for more information.

        S Addr Wr [A] Data [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_BYTE
        """
        raise NotImplementedError

    def write_byte_data(self, address, register, value):
        """
        SMBus Read Byte:  i2c_smbus_read_byte_data()
        ============================================

        This reads a single byte from a device, from a designated register.
        The register is specified through the Comm byte.

        S Addr Wr [A] Comm [A] S Addr Rd [A] [Data] NA P

        Functionality flag: I2C_FUNC_SMBUS_READ_BYTE_DATA
        """

        return self.device.write([0xD0, address, 0x06, 2, register, value])


    def read_byte_data(self, address, register):
        """
        SMBus Read Byte:  i2c_smbus_read_byte_data()
        ============================================

        This reads a single byte from a device, from a designated register.
        The register is specified through the Comm byte.

        S Addr Wr [A] Comm [A] S Addr Rd [A] [Data] NA P

        Functionality flag: I2C_FUNC_SMBUS_READ_BYTE_DATA
        """


        payload = [0xD0, address, 0x06, 0b01, register]
        self.device.write(payload)
        length = (1).to_bytes(2, byteorder='little')
        self.device.write([0xC2, address, 0x06, length[0], length[1]])
        d = self.device.read(0xde)

        # TODO: Osetrit chyby v chybnem vycteni registru
        return d[2]


    def write_word_data(self, address, register, value):
        """
        SMBus Write Word:  i2c_smbus_write_word_data()
        ==============================================

        This is the opposite of the Read Word operation. 16 bits
        of data is written to a device, to the designated register that is
        specified through the Comm byte.

        S Addr Wr [A] Comm [A] DataLow [A] DataHigh [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_WORD_DATA

        Note the convenience function i2c_smbus_write_word_swapped is
        available for writes where the two data bytes are the other way
        around (not SMBus compliant, but very popular.)
        """
        return self.device.write([0xD0, address, 0x06, 3, register, (value)&0xff, (value>>8)&0xff ])

    def read_word_data(self, address, register):
        """
        SMBus Read Word:  i2c_smbus_read_word_data()
        ============================================

        This operation is very like Read Byte; again, data is read from a
        device, from a designated register that is specified through the Comm
        byte. But this time, the data is a complete word (16 bits).

        S Addr Wr [A] Comm [A] S Addr Rd [A] [DataLow] A [DataHigh] NA P

        Functionality flag: I2C_FUNC_SMBUS_READ_WORD_DATA

        Note the convenience function i2c_smbus_read_word_swapped is
        available for reads where the two data bytes are the other way
        around (not SMBus compliant, but very popular.)
        """

        payload = [0xD0, address, 0x06, 0b01, register]
        self.device.write(payload)
        length = (2).to_bytes(2, byteorder='little')
        self.device.write([0xC2, address, 0x06, length[0], length[1]])
        d = self.device.read(0xde)

        # TODO: Osetrit chyby v chybnem vycteni registru
        return d[2]<<8 | d[3]

    def write_block_data(self, address, register, value):
        """
        SMBus Block Write:  i2c_smbus_write_block_data()
        ================================================

        The opposite of the Block Read command, this writes up to 32 bytes to
        a device, to a designated register that is specified through the
        Comm byte. The amount of data is specified in the Count byte.

        S Addr Wr [A] Comm [A] Count [A] Data [A] Data [A] ... [A] Data [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_BLOCK_DATA
        """
        raise NotImplementedError

    def read_block_data(self, address, register):
        """
        SMBus Block Read:  i2c_smbus_read_block_data()
        ==============================================

        This command reads a block of up to 32 bytes from a device, from a
        designated register that is specified through the Comm byte. The amount
        of data is specified by the device in the Count byte.

        S Addr Wr [A] Comm [A]
                   S Addr Rd [A] [Count] A [Data] A [Data] A ... A [Data] NA P

        Functionality flag: I2C_FUNC_SMBUS_READ_BLOCK_DATA
        """
        raise NotImplementedError

    def block_process_call(self, address, register, value):
        """
        SMBus Block Write - Block Read Process Call
        ===========================================

        SMBus Block Write - Block Read Process Call was introduced in
        Revision 2.0 of the specification.

        This command selects a device register (through the Comm byte), sends
        1 to 31 bytes of data to it, and reads 1 to 31 bytes of data in return.

        S Addr Wr [A] Comm [A] Count [A] Data [A] ...
                                     S Addr Rd [A] [Count] A [Data] ... A P

        Functionality flag: I2C_FUNC_SMBUS_BLOCK_PROC_CALL
        """
        raise NotImplementedError

    ### I2C transactions not compatible with pure SMBus driver
    def write_i2c_block(self, address, value):
        """
        Simple send transaction
        ======================

        This corresponds to i2c_master_send.

          S Addr Wr [A] Data [A] Data [A] ... [A] Data [A] P

        More detail documentation is at: https://www.kernel.org/doc/Documentation/i2c/i2c-protocol
        """
        raise NotImplementedError

    def read_i2c_block(self, address, length):
        """
        Simple receive transaction
        ===========================

        This corresponds to i2c_master_recv

          S Addr Rd [A] [Data] A [Data] A ... A [Data] NA P

        More detail documentation is at: https://www.kernel.org/doc/Documentation/i2c/i2c-protocol
        """

        payload = [0xc2, address, 0x06, length, 0]
        self.device.write(payload)
        data = self.device.read(0xde)

        return data[2:data[1]+2]

    def write_i2c_block_data(self, address, register, value):
        """
        I2C block transactions do not limit the number of bytes transferred
        but the SMBus layer places a limit of 32 bytes.

        I2C Block Write:  i2c_smbus_write_i2c_block_data()
        ==================================================

        The opposite of the Block Read command, this writes bytes to
        a device, to a designated register that is specified through the
        Comm byte. Note that command lengths of 0, 2, or more bytes are
        supported as they are indistinguishable from data.

        S Addr Wr [A] Comm [A] Data [A] Data [A] ... [A] Data [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_I2C_BLOCK
        """
        
        payload = [0xD0, address, 0x06, len(value) + 1, register] + value
        self.device.write(payload)


    def read_i2c_block_data(self, address, register, length):
        data = []
        for i in range(length):
            self.write_byte_data(address, register, i)
            byte = self.read_byte(address)
            data.append(byte)
        return data
        
    def read_i2c_block_data(self, address, register, length):
        """
        I2C Block Read: i2c_smbus_read_i2c_block_data()
        =================================================

        Reads a block of bytes from a specific register in a device. It's the direct
        opposite of the Block Write command, primarily used for retrieving a series
        of bytes from a given register.

        S Addr Wr [A] Comm [A] S Addr Rd [A] Data [A] Data [A] ... [A] Data [A] P

        The method respects SMBus limitations of 32 bytes for block transactions.
        """

        timeout = 500

        register = (register).to_bytes(2, byteorder='little')
        payload = [0xD4, address, 0x02, 2, register[0], register[1]]
        self.device.write(payload)
        length = (length).to_bytes(2, byteorder='little')
        self.device.write([0xC2, address, 0x07, length[0], length[1]])
        d = self.device.read(0xde, timeout)

        print(d)

        return d[2:d[1]]

    def write_i2c_block_data(self, address, register, data):
        """
        I2C Block Write: i2c_smbus_write_i2c_block_data()
        =================================================

        Writes a block of bytes to a specific register in a device. This command
        is designed for direct I2C communication, allowing for command lengths of 0,
        2, or more bytes, which are indistinguishable from data.

        S Addr Wr [A] Comm [A] Data [A] Data [A] ... [A] Data [A] P

        Functionality flag: I2C_FUNC_SMBUS_WRITE_I2C_BLOCK
        """

        register = (register).to_bytes(2, byteorder='little')
        payload = [0xD4, address, 0x06, 0, register[0], register[1]] + data
        payload[3] = len(payload) - 4
        self.device.write(payload)

        return True
    

class FT260():
    def __init__(self, VID=0, PID=0, *args, **kwargs):
        self.VID = VID
        self.PID = PID
        self.device = hid.device()
        self.open_hid()

    def __str__(self) -> str:
        return f"FT260 device with VID: {self.VID}, PID: {self.PID}, SN: {self.device.get_serial_number_string()}"

    def print_device_info(self):
        print(f'Device manufacturer: {self.device.get_manufacturer_string()}')
        print(f'Product: {self.device.get_product_string()}')
        print(f'Serial Number: {self.device.get_serial_number_string()}')


    def open_hid(self):
        self.device.open(self.VID, self.PID)
        self.device.set_nonblocking(0)


    def get_i2c_status(self):
        d = self.device.get_feature_report(0xC0, 100)

        status = ['busy_chip', 'error', 'no_ack', 'arbitration_lost', 'idle', 'busy_bus']
        bits = [(d[1] & (1 << i)) >> i for i in range(8)]
        status = dict(zip(status, bits))

        baudrate = (d[2] | d[3]<<8)*1000
        status['baudrate'] = baudrate

        return status

    def FT260_I2C(self):
        return I2C(self.device)

    def FT260_UART(self):
        raise NotImplementedError("UART interface not implemented yet")
    
    def FT260_GPIO(self):
        raise NotImplementedError("GPIO interface not implemented yet")
    


    


