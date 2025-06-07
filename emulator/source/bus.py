
#
# Emulates the 16-bit bus.
#
# supports both byte and word writes.
# peripherals attach to the bus by specifying address rand and pointer to defining class
#
#
class Bus:
    def __init__(self, verbose=0):
        self.devices = []

    def attach(self, peripheral, start, end):
        p = {'p':peripheral, 's':start, 'e':end}
        self.devices.append(p)

    def determine_devices(self, addr):
        for device in self.devices:
            if device['s'] <= addr and device['e'] > addr:
                # have a match
                return device

    def word2byte(self, addr, data, byte=False):
        # we are doing a byte operation
        # need to convert word data to duplicated byte data
        if byte:
            if addr & 1:
                # return odd (upper byte)
                data = (data >> 8) & 0xff
                data |= data << 8
            else:
                # return even (lower byte)
                data &= 0xff
                data |= data << 8
        return data

    def write(self, addr, data, byte=False):
        device = self.determine_devices(addr)
        device_addr = addr - device['s']
        data = self.word2byte(addr, data, byte)
        device.peripheral.write(device_addr, data)

    def read(self, addr, byte=False):
        device = self.determine_devices(addr)
        device_addr = addr - device['s']
        data = device.peripheral.read(device_addr)
        data = self.word2byte(addr, data, byte)
        if byte:
            data &= 0xff
        return data
