##################################
#
# architectural model
#
# pingable TCP/IP Handler
#
##################################
import sys
import argparse

import queue
import threading
from time import sleep
import signal


FILEIN = "../gather/frame.dat"

LAST_BIT = 1 << (64 + 8)
KEEP_BITS = 0xff << 64
BRDCST = (1 << 48) - 1


def get_field(self, addr, num_bytes, reverse=False):
    base = addr >> 3
    offset = addr % 8

    word_low = self.sim.fifo.read(base)
    word_high = self.sim.fifo.read(base + 1)
    data = (word_high << 64) + word_low
    data >>= offset << 3

    mask = (1 << (num_bytes << 3)) - 1
    data &= mask

    # reverse bytes, optionally
    if reverse:
        data = self.reverse(data, num_bytes)

    return data

def reverse(self, data, num_bytes):
    # reverse bytes, optionally
    new_data = 0
    for i in range(num_bytes):
        new_data <<= 8
        new_data |= data & 0xff
        data >>= 8

    return new_data

class LayerMac:
    def __init_(self, our_mac_addr):
        self.our_mac_addr = our_mac_addr

    def addr_filter(self, buffer):
        self.parse(buffer)

        if self.broadcast or self.ours:
            return True
        return False

    def parse(self, buffer):
        ##########################################
        # MAC fields
        ##########################################
        # either broadcast, individual address
        self.da = get_field(0,6)
        self.broadcast = self.da == BRDCST
        self.ours = self.da == self.our_mac_addr

        self.sa = get_field(6, 6)
        self.packet_type = get_field(12, 2, reverse=True)
        self.length = 14

class Test:
    def __init__(self):
        self.buffer = []

        # buffer contains test frame
        mac = LayerMac(self.buffer)



class IpMac:
    def __init__(self, buffer, offset_start):
        ##########################################
        # MAC fields
        ##########################################
        # either broadcast, individual address
        self.da = self.ip.get_field(0,6)
        self.broadcast = self.da == BRDCST
        self.ours = self.da == self.our_mac_addr

        self.sa = self.ip.get_field(6, 6)
        self.packet_type = self.ip.get_field(12, 2, reverse=True)


class IpARP:
    def __init__(self):
        pass

class Ip:
    def __init__(self):
        pass









# convert ip str of the form 192.168.1.4
# to integer
def ip_s2i(ip_str):
    tokens = ip_str.split('.')
    ip_int = 0
    for i in range(len(tokens)):
        ip_int <<= 8
        ip_int |= int(tokens[i], 0)
    return ip_int


def mac_s2i(mac_str):
    mac_addr = 0

    tokens = mac_str.split(':')
    tokens.reverse()
    for token in tokens:
        byte = int(token, 16)
        mac_addr <<= 8
        mac_addr |= byte
    return mac_addr


# reads data file produced by gather
# note: in separate class since data formats
# may change
class DATA:
    def __init__(self, datafile):
        self.count = 0
        self.datablock = []
        self.open(datafile)

    def open(self, datafile):
        try:
            fin = open(datafile, "r")
        except IOError:
            print("Cannot open " + datafile)
            sys.exit(1)

        for line in fin:
            if '=' in line:
                continue
            data = int(line, 16)
            self.datablock.append(data)

        print("linecount", len(self.datablock))

        framecount = 0
        brdcstcount = 0
        first = True
        for data in self.datablock:
            if data & LAST_BIT:
                framecount += 1
            if first:
                if (data & BRDCST) == BRDCST:
                    brdcstcount += 1

        print("read framecount=", framecount)
        print("brdcstcount=", brdcstcount)

    def get_data(self):
        if self.done():
            return None

        data = self.datablock[self.count]
        self.count += 1
        return data

    def done(self):
        if self.count >= len(self.datablock):
            return True
        else:
            return False


# mimic hardware packet fifo
class FIFO:
    def __init__(self, size=8192*2):
        self.size = size
        self.Ram = [0] * size
        self.reset()

    def incr_pointer(self, pointer):
        pointer += 1
        pointer = self.pointer_range_fix(pointer)
        return pointer

    def pointer_range_fix(self, pointer):
        if pointer >= self.size:
            pointer = 0
        return pointer

    def reset(self):
        # leaves data in the Ram, but the pointers are reset
        self.writeP = 0
        self.lagP = 0
        self.readP = 0

    # full: do not write
    def full(self):
        if self.readP == self.incr_pointer(self.writeP):
            # fifo is full
            return True
        return False

    # empty: do not read
    def empty(self):
        if self.readP == self.lagP:
            return True
        return False

    def push(self, data):
        if self.full():
            return None

        self.Ram[self.writeP] = data
        self.writeP = self.incr_pointer(self.writeP)
        return True

    def pop(self):
        if self.empty():
            return None

        data = self.Ram[self.readP]
        self.readP = self.incr_pointer(self.readP)
        return data

    def accept(self):
        # make data available to the read process
        self.lagP = self.writeP

    def reject(self):
        # remove/delete bad packet
        self.writeP = self.lagP

    def read(self, word_address):
        if self.empty():
            return None

        real_addr = word_address + self.readP
        real_addr = self.pointer_range_fix(real_addr)
        data = self.Ram[real_addr]
        return data

    def write_byte(self, byte_address, write_data):
        # based on READ pointer
        # full check not needed since replacing data in fifo
#        if self.full():
#            return None

        byte = byte_address % 8  # which byte
        word_address = byte_address >> 3
        real_addr = word_address + self.readP
        real_addr = self.pointer_range_fix(real_addr)

        data = self.Ram[real_addr]
        data &= ~(0xff << (byte << 3))
        data |= write_data << (byte << 3)

        self.Ram[real_addr] = data

    # flush fifo until next LAST
    def frame_purge(self):
        while True:
            data = self.pop()
            # was there data
            if data is None:
                return

            if data & LAST_BIT:
                # have last, next word in fifo is first word next frame
                return


class FRAME:
    def __init__(self, iphandler, our_mac_addr, our_ip_addr):
        self.ip = iphandler
        self.sim = self.ip.sim
        self.fifo = self.ip.sim.fifo  # has random access read routine to extract frame with

        self.our_mac_addr = our_mac_addr
        self.our_ip_addr = our_ip_addr

        self.broadcast = False
        self.ours = False
        self.da = mac_s2i("0:0:0:0:0:0")

    def print(self):
        for i in range(20):        # limit to 160 bytes.
            data = self.fifo.read(i)
            lastbit = (data >> (64 + 8)) & 1
            outstr = "%03d:" % (i << 3)
            keeps = (data >> 64) & 0xff

            for j in range(8):
                if keeps & 1:
                    outstr += " %02x" % (data & 0xff)
                keeps >>= 1
                data >>= 8
            print(outstr)

            if lastbit:
                break

    def parse(self):
        ##########################################
        # MAC fields
        ##########################################
        # either broadcast, individual address
        self.da = self.ip.get_field(0,6)
        self.broadcast = self.da == BRDCST
        self.ours = self.da == self.our_mac_addr

        self.sa = self.ip.get_field(6, 6)
        self.packet_type = self.ip.get_field(12, 2, reverse=True)

        ##########################################
        # ARP fields
        ##########################################
        self.hard_type = self.ip.get_field(14, 2, reverse=True)
        self.prot_type = self.ip.get_field(16, 2, reverse=True)
        self.hard_size = self.ip.get_field(18, 1)
        self.prot_size = self.ip.get_field(19, 1)

        self.op = self.ip.get_field(20, 2, reverse=True)
        self.mac_addr_sender = self.ip.get_field(22, 6)
        self.ip_addr_sender = self.ip.get_field(28, 4, reverse=True)
        self.mac_addr_target = self.ip.get_field(32, 6) # used in response, not request
        self.ip_addr_target = self.ip.get_field(38, 4, reverse=True)

        ##########################################
        # IP FRAME fields
        ##########################################
        data = self.sim.ip.get_field(14, 1)
        self.version = (data >> 4) & 0xf
        self.header_length = data & 0xf
        self.tos = self.sim.ip.get_field(15, 1)
        self.length = self.sim.ip.get_field(16, 2, reverse=True)
        self.id = self.sim.ip.get_field(18, 2, reverse=True)
        self.flags = (self.sim.ip.get_field(19, 1) >> 5) & 0x7
        self.fragment_offset = self.sim.ip.get_field(19, 2, reverse=True) & 0x1fff
        self.ttl = self.sim.ip.get_field(20, 1)
        self.protocol = self.sim.ip.get_field(21, 1)
        self.header_checksum = self.sim.ip.get_field(22, 2, reverse=True)
        self.src_ip = self.sim.ip.get_field(24, 4, reverse=True)
        self.dest_ip = self.sim.ip.get_field(28, 4, reverse=True)

class IP:
    def __init__(self, sim, mac_addr, ip_addr):
        self.sim = sim
        self.frame_count = 0
        self.frame_count_ours = 0

        self.frame = FRAME(self, mac_addr, ip_addr)

    def do_frame(self):
        # following sequence process a frame
        # L2 frame processing
        #
        # fifo empty checked up one level
        #
        # is this our frame (@L2)
        retval = self.do_frame_L2(self.frame)
        if not retval:
            # not our frame
            self.sim.fifo.frame_purge()
            return

        # check if ARP
        retval = self.do_frame_L3_ARP(frame)
        if retval:
            # is an ARP frame addressed to us
            # do_frame_L3_ARP will have sent ARP reply
            self.sim.fifo.frame_purge()
            return

        retval = self.do_frame_L3(self.frame)
        if not retval:
            self.sim.fifo.frame_purge()
            return

        # have valid L3 frame
        # do we have a L3:ICMP Frame?
        if self.protocol != PROTOCOL_ICMP:
            # not an ICMP
            self.sim.fifo.frame_purge()
            return

        # have a valid ICMP packet
        # is it a PING packet


    def do_frame_L2(self, frame):
        # either broadcast, individual address

        takeit = frame.ours or frame.broadcast
        self.frame_count += 1
        if takeit:
            self.frame_count_ours += 1

        return takeit

    def do_frame_L3(self, frame):
        #
        # we have a L2 frame addressed to us
        #
        # do we have an ARP Frame
        retval = self.do_frame_L3_ARP(frame)
        if retval:
            # yes
            self.do_frame_L3_ARP(frame)
            pass

        # no, must be an IP4 frame
        self.do_frame_L3_IP(frame)
        self.sim.fifo.frame_purge()

    def do_frame_L3_ARP(self, frame):
        # note: frame has passed L2 address filtering!!

        # validate that fields are ARP
        if not frame.broadcast:
            return False
        print("pt= %04x" % frame.packet_type)
        if frame.packet_type != 0x0806:
            return False
        if frame.hard_type != 1:
            return False
        if frame.prot_type != 0x0800:
            return False
        if frame.hard_size != 6:
            return False
        if frame.prot_size != 4:
            return False
        if frame.op != 1:
            return False

        print("Have a valid ARP frame")
        #frame.print()

        self.sim.fifo.write_byte(21, 2)     # 2nd byte of 2 byte field

        our_mac = frame.our_mac_addr
        for i in range(6):
            byte = our_mac & 0xff
            self.sim.fifo.write_byte(32 + i, byte)
            our_mac >>= 8

        frame.print()

        print("Processing ARP frame complete")
        return True

    def do_frame_L3_IP(self, frame):
        # check if IP frame is addressed to us
        if frame.dest_ip != frame.our_mac_addr:
            return False

        # checksum in frame is zero, we do not check checksum
        if frame.header_checksum:
            # calculate checksum
            sum = 0
            for i in range(frame.header_length):
                ip_addr = 14 + i
                data16 = self.sim.ip.get_field(ip_addr, 2, reverse=True)
                sum += data16
            sum &= 0xffff

            if sum != 0xffff:
                print("ERROR: IP checksum")
                return False
        else:
            # if received checksum is 0, we do not check the checksum
            pass

        # have a valid IP addressed packet with good checksum


        pass

    def get_field(self, addr, num_bytes, reverse=False):
        base = addr >> 3
        offset = addr % 8

        word_low = self.sim.fifo.read(base)
        word_high = self.sim.fifo.read(base + 1)
        data = (word_high << 64) + word_low
        data >>= offset << 3

        mask= (1 << (num_bytes << 3)) - 1
        data &= mask

        # reverse bytes, optionally
        if reverse:
            data = self.reverse(data, num_bytes)

        return data

    def reverse(self, data, num_bytes):
        # reverse bytes, optionally
        new_data = 0
        for i in range(num_bytes):
            new_data <<= 8
            new_data |= data & 0xff
            data >>= 8

        return new_data

class SIM:
    def __init__(self, args):
        self.args = args

        mac_addr = mac_s2i(args.mac_addr)
        ip_addr = ip_s2i(args.ip_addr)

        self.frame_count = 0

        # design consists of
        # 1. Data stream generator fed by a file
        self.data = DATA(FILEIN)
        self.datastream = self.data.datablock
        # 2. Packet Fifo
        self.fifo = FIFO()
        self.fifo.reset()
        # 3. Receive Frame Processor
        self.ip = IP(self, mac_addr, ip_addr)

        self.thread_frames_enable = True
        self.frame_count = 0
        self.current_input_word = 0

        # capture ^C
        signal.signal(signal.SIGINT, self.sigC_handler)

        self.t1 = threading.Thread(target=self.thread_fill, daemon=True)
        self.t1.daemon = True
        self.t2 = threading.Thread(target=self.thread_frames, daemon=True)
        self.thread_frames_stop = False
        self.t2.daemon = True

        self.t1.start()
        self.t2.start()

        sleep(0.02)     # give time for threads to start

        while len(self.datastream) != self.current_input_word:
            sleep(0.02)

    def sigC_handler(self, sig, frame):
        self.quit()

    def quit(self):
        while True:
            if not self.t1.is_alive():
                break

            sleep(0.01)

        self.thread_frames_enable = False

        self.t1.join()
        self.t2.join()
        print("all done, goodbye")

    def thread_fill(self):
        # read data from data stream
        # if fifo fills, reject the frame and throw remaining word in trash

        self.frames_sent = 0
        self.current_input_word = 0
        while self.thread_frames_enable:
            if self.fifo.full():
                # no room to write
                sleep(0.02)    # 20ms
                continue
            else:
                # room for a packet
                try:
                    data = self.datastream[self.current_input_word]
                    self.current_input_word += 1
                    self.fifo.push(data)
                    EOF = data & LAST_BIT
                    if EOF:
                        self.fifo.accept()
                        self.frames_sent += 1
                except IndexError:
                    print("all done")
                    break

        print("frames_sent = ", self.frames_sent)

    def thread_frames(self):
        self.frame_count = 0
        while self.thread_frames_enable:
            if not self.fifo.empty():
                self.ip.frame.parse()
                self.ip.do_frame()
                self.frame_count += 1

def main():
    mac_addr_s = "01:02:03:04:05:06"
    ip_addr_s = "168.192.1.16"
    ip_addr = ip_s2i(ip_addr_s)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-m', action='store', dest='mac_addr', default=mac_addr_s)
    arg_parser.add_argument('-i', action='store', dest='ip_addr', default=ip_addr_s)
    args = arg_parser.parse_args()

    sim = SIM(args)

    print("fc = ", sim.frame_count)


main()


