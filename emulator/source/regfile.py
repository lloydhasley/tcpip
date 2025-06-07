


class RegFile:
    def __init__(self, tcpip,  verbose=0):
        self.tcpip = tcpip

        self.regs = [0] * 128
        self.external = {
            0x04:self.tcpip.fifostatus,
            0x08:self.tcpip.FRAME_DONE,
            0x28:0xffff,
            0x2a:0x0806,
            0x2c:0x0800,
            0x2e:0x0800
        }
        pass

    def update_outputs(self, addr):
        # Control Register
        self.tcpip.enable = self.regs[0] & 1

        # pulse send frame
        if addr==0x08:
            # put handler call here
            self.tcpip.ADDR_SEND_FRAME = 0

        # pulse eat frame
        if addr==0x0c:
            # put handler call here
            self.tcpip.EatFrame = 0

    def write(self, addr, data):
        addr &= 0x7f
        self.regs[addr] = data & 0xffff
        self.update_outputs(addr)

    def read(self, addr):
        addr &= 0x7f
        if addr in self.external:
            data = self.external[addr]
        else:
            data = self.regs[addr]
