#
# interface to TCPIP network
#
#
import socket
import select
import os

class Net:
    def __init__(self, args):
        self.args = args

        self.our_mac_addr = self.mac_str2int(args.mac_addr)
        self.our_ip_addr = self.ip_str2int(args.ip_addr)

        self.iname = os.basename(args.interface)
        self.pkt_type = 8003
        self.response_timeout = 0.3     # needed?
        self.max_pkt_size = 8192

        # open socket and register for test packets
        # note: we want both ARP and PING packets
        self.s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.pkt_type))
        self.s.bind((self.iname, 0))
        self.s.setblocking(0)
        # change keybaord to non-blocking, so we can get a quit.

    def send_frame_axis64(self, frame):
        # frame is list of 64 bit words
        byte_array = []
        for word in frame:
            data = word & ((1 << 64) -1)
            keep = (word >> 64) & 0xff
            last = (word >> (64 + 8)) & 0x1
            while keep:
                if keep & 1:
                    byte_array.append(data & 0xff)
                data >>= 8
                keep >>= 1
            if last:
                break
        return self.send_bytes(byte_array)

    def send_bytes(self, byte_array):
        msg = bytearray(byte_array)
        retcode = self.s.send(msg)
        return retcode

    def recv_bytes(self):
        ready = select.select([self.s], [], [], self.response_timeout)
        if not ready[0]:
            # nothing received
            return []

        # frame ready, retrieve it
        r_pkt = self.s.recvfrom(self.max_pkt_size)
        r_msg = r_pkt[0]
        r_length = len(r_msg) + 3
        #        r_format = ('!' + str(r_length) | + 'B')
        #        frame = unpack(r_format, r_msg)
        frame = list(r_msg)
        return frame


    # note mac ints are normal byte order
    # ((mac strs have LSB first)), we switch the bytes so LSB is in the low order bytes of the integer
    def mac_str2int(mac_str):
        mac_addr = 0

        tokens = mac_str.split(':')
        for token in tokens:
            byte = int(token, 16)
            mac_addr <<= 8
            mac_addr |= byte
        print(" mac str2int: %012x" % mac_addr)
        return mac_addr

    def mac_int2str(mac_addr):
        mac_str = ''
        for i in range(6):
            if mac_str != '':
                mac_str = mac_str + ':'
            mac_str = mac_str + "%d" % (mac_addr & 0xff)
            mac_addr >>= 8
        return mac_str

    def ip_int2str(ip_num):
        ip_str = ''
        for i in range(4):
            if ip_str != '':
                ip_str = '.' + ip_str
            ip_str = "%d" % (ip_num & 0xff) + ip_str
            ip_num >>= 8
        return ip_str

    # convert ip str of the form 192.168.1.4
    # to integer
    def ip_str2int(ip_str):
        tokens = ip_str.split('.')
        ip_int = 0
        for i in range(len(tokens)):
            ip_int <<= 8
            ip_int |= int(tokens[i], 10)
        return ip_int


