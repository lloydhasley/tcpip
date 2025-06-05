##################################
#
# architectural model
#
# pingable TCP/IP Handler
#
##################################
#
# note: byte reversible fields must be 8n in length
#    fragment offset may violate this
#
##################################

import sys
import argparse
from dataclasses import dataclass
import copy
from struct import *
import socket
import select

import ascii

FILEIN = "../gather/frame.dat"

LAST_BIT = 1 << (64 + 8)
KEEP_BITS = 0xff << 64
BRDCST = (1 << 48) - 1

BUFSIZE = 512

LAST_BIT_BYTE = 0x100

MAXFRAME = 128  # throw away frfames larger than this.
MAXFRAME = 150  # throw away frfames larger than this.


verbosity = 0
VERBOSITY_FRAME = 1
VERBOSITY_ARP = 2
VERBOSITY_PING = 4


# note mac ints are normal byte order
# ((mac strs have LSB first)), we switch the bytes so LSB is in the low order bytes of the integer
def mac_str2int(mac_str):
    mac_addr = 0

    tokens = mac_str.split(':')
#    tokens.reverse()
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


@dataclass
class FIELD:
    __slots__ = ("value", "offset", "width", "reverse")
    value: int
    offset: int
    width: int
    reverse: int


class MAC:
    def __init__(self, offset):
        print("mac offset=", offset, offset >> 3)

        self.da =           FIELD(0, offset + 0, 48, False)
        self.sa =           FIELD(0, offset + 48, 48, False)
        self.type =         FIELD(0, offset + 96, 16, False)

        self.length_bytes = 112 >> 3
        self.nextAddr = offset + 96 + 16


class ARP:
    def __init__(self, offset):
        print("arp offset=", offset, offset >> 3)

        self.hard_type =        FIELD(0, offset + 0, 16, False)
        self.prot_type =        FIELD(0, offset + 16, 16, False)
        self.hard_size =        FIELD(0, offset + 32, 8, False)
        self.prot_size =        FIELD(0, offset + 40, 8, False)

        self.op =               FIELD(0, offset + 48, 16, False)
        self.mac_addr_sender =  FIELD(0, offset + 64, 48, False)
        self.ip_addr_sender =   FIELD(0, offset + 112, 32, False)
        self.mac_addr_target =  FIELD(0, offset + 144, 48, False)  # used in response
        self.ip_addr_target =   FIELD(0, offset + 192, 32, False)

        self.length_bytes = 224 >> 3
        self.nextAddr = offset + 192 + 32


class IP:
    def __init__(self, offset):
        print("ip offset=", offset, offset>>3)

        self.header_length =    FIELD(0, offset + 0, 4, False)
        self.version =          FIELD(0, offset + 4, 4, False)
        self.tos =              FIELD(0, offset + 8, 8, False)
        self.length =           FIELD(0, offset + 16, 16, False)
        self.id =               FIELD(0, offset + 32, 16, False)
        self.flags =            FIELD(0, offset + 48, 3, False)
        self.fragment_offset =  FIELD(0, offset + 51, 13, False) # hope false is correct, we only reverse bytes
        self.ttl =              FIELD(0, offset + 64, 8, False)
        self.protocol =         FIELD(0, offset + 72, 8, False)
        self.header_checksum =  FIELD(0, offset + 80, 16, False)
        self.src_ip =           FIELD(0, offset + 96, 32, False)
        self.dest_ip =          FIELD(0, offset + 128, 32, False)

        self.length_bytes = 164 >> 3
        self.nextAddr = offset + 128 + 32

class ICMP:
    def __init__(self, offset):
        print("icmp offset=", offset, offset>>3)

        self.type =     FIELD(0, offset + 0, 8, False)
        self.code =     FIELD(0, offset + 8, 8, False)
        self.checksum = FIELD(0, offset + 16, 16, False)

        self.length_bytes = 32 >> 3
        self.nextAddr = offset + 16 + 16


class FRAME:
    def __init__(self, our_mac_addr, our_ip_addr):
        self.verbosity =  0

        # save parameters
        self.our_mac_addr = our_mac_addr
        self.our_ip_addr = our_ip_addr

        # constructors
        self.mac = MAC(0)

        self.arp = ARP(self.mac.nextAddr)
        self.ip = IP(self.mac.nextAddr)
        self.icmp = ICMP(self.ip.nextAddr)


        self.buffer = []
        self.frame_count = 0

    def print_frame(self, data_frame):
        self.print_frame_buffer(data_frame)
        print()
        self.print_frame_fields()

    def print_frame_buffer(self, data_frame, amt=64, bytesperline=8):
        ll = len(data_frame)
        if ll < amt:
            amt = ll

        outstr = ''
        for i in range(amt):
            if (i % bytesperline) == 0:
                outstr = "%03d" % i
            c = data_frame[i]
            outstr += ' %02x' % c
            if (i % bytesperline) == (bytesperline - 1):
                print(outstr)

    def print_frame_fields(self):
        reg_name_format = '\t%15s'

        mod = "MAC"
        print("%s" % mod, reg_name_format % "da" + ": %-012x" % self.mac.da.value)
        print("%s" % mod, reg_name_format % "sa" + ": %-012x" % self.mac.sa.value)
        print("%s" % mod, reg_name_format % "type" + ": %-04x" % self.mac.type.value)

        mod = "ARP"
        print("%s" % mod, reg_name_format % "hard_type" + ": %-04x" % self.arp.hard_type.value)
        print("%s" % mod, reg_name_format % "prot_type" + ": %-04x" % self.arp.prot_type.value)
        print("%s" % mod, reg_name_format % "hard_size" + ": %-04x" % self.arp.hard_size.value)
        print("%s" % mod, reg_name_format % "prot_size" + ": %-04x" % self.arp.prot_size.value)
        print("%s" % mod, reg_name_format % "os" + ": %-02x" % self.arp.op.value)
        print("%s" % mod, reg_name_format % "mac_addr_sender" + ": 0x%-12x" % self.arp.mac_addr_sender.value)
        print("%s" % mod, reg_name_format % "ip_addr_sender" + ":", ip_int2str(self.arp.ip_addr_sender.value))
        print("%s" % mod, reg_name_format % "mac_addr_target" + ": 0x%-12x" % self.arp.mac_addr_target.value)
        print("%s" % mod, reg_name_format % "ip_addr_target" + ":", ip_int2str(self.arp.ip_addr_target.value))

        mod = "IP "
        print("%s" % mod, reg_name_format % "header_length" + ": %-08x" % self.ip.header_length.value)
        print("%s" % mod, reg_name_format % "version" + ": %-08x" % self.ip.version.value)
        print("%s" % mod, reg_name_format % "tos" + ": %-02x" % self.ip.tos.value)
        print("%s" % mod, reg_name_format % "length" + ": %-04x" % self.ip.length.value)
        print("%s" % mod, reg_name_format % "id" + ": %-04x" % self.ip.id.value)
        print("%s" % mod, reg_name_format % "fragment_offset" + ": %-04x" % self.ip.fragment_offset.value)
        print("%s" % mod, reg_name_format % "flags" + ": %-04x" % self.ip.flags.value)
        print("%s" % mod, reg_name_format % "ttl" + ": %-02x" % self.ip.ttl.value)
        print("%s" % mod, reg_name_format % "protocol" + ": %-04x" % self.ip.protocol.value)
        print("%s" % mod, reg_name_format % "header_checksum" + ": %-04x" % self.ip.header_checksum.value)
#        print("%s" % mod, reg_name_format % "src_ip" + ": %-08x" % self.ip.src_ip.value)
#        print("%s" % mod, reg_name_format % "dest_ip" + ": %-08x" % self.ip.dest_ip.value)
        print("%s" % mod, reg_name_format % "src_ip" + ": ", ip_int2str(self.ip.src_ip.value))
        print("%s" % mod, reg_name_format % "dest_ip" + ": ", ip_int2str(self.ip.dest_ip.value))

        mod = "ICMP"
        print("%s" % mod, reg_name_format % "type" + ": %-02x" % self.icmp.type.value)
        print("%s" % mod, reg_name_format % "code" + ": %-02x" % self.icmp.code.value)
        print("%s" % mod, reg_name_format % "checksum" + ": %-08x" % self.icmp.checksum.value)

    def set_field_shadows(self, data_frame):
        self.data_frame = data_frame

        for handler in [self.mac, self.arp, self.ip, self.icmp]:
            for key, var in handler.__dict__.items():
                if not isinstance(var, FIELD):
                    continue

                offset = var.offset
                width = var.width
                reverse = var.reverse

                first_byte = offset >> 3
                last_byte = (offset + width + 7) >> 3
                field_bytes = data_frame[first_byte:last_byte]
                if reverse:
                    field_bytes.reverse()
                value = 0
                for byte in field_bytes:
                    value <<= 8
                    value |= byte
                value >>= (offset % 8)
                value &= (1 << width ) - 1
                var.value = value

    def clear_buffer(self):
        for i in range(BUFSIZE):
            self.buffer[i] = 0

    def read(self, field):
        return field.value

    def write(self, frame, field, data):
        #
        # note: this is way more complicated than it should be.
        #
        # limit data width
        offset_bits = field.offset % 8          # offset % 8, bits
        offset_bytes = field.offset >> 3        # floor offset/8
        num_bytes = (field.width + 7) >> 3      # roof width/8

        data &= (1 << field.width) - 1
        field.value = data

        if field.reverse:
            # only support len=8n
            data_reversed = 0
            for i in range(num_bytes):
                byte = data & 0xff
                data_reversed <<= 8
                data_reversed |= byte
            data = data_reversed

        # get existing data as integer
        value = 0
        for i in range(num_bytes):
            value_byte = frame[num_bytes - i - 1]
            value <<= 8
            value |= value_byte

        data_mask = ((1 << field.width) - 1) << offset_bits
        value <<= offset_bits
        value &= ~data_mask
        value |= data & data_mask

        # place new integer back into buffer
        for i in range(num_bytes):
            byte = value & 0xff
            frame[offset_bytes + num_bytes - i - 1] = byte
            value >>= 8

    def frame_filter(self, frame, our_mac_addr):
        # returns True if criteria met
        # returns False if frame is to be ignored
        if len(frame) > MAXFRAME:
            return False

        da = self.mac.da.value
        if da == BRDCST:
            return True
        if da == our_mac_addr:
            return True
        return False

    def do_L3_ARP(self, frame, our_ip_addr):
        # returns false if not ARP, true if ARP
        # note: frame has passed L2 address filtering!!
        # validate that fields are ARP

        self.verbosity |= VERBOSITY_ARP

        if self.verbosity & VERBOSITY_ARP:
            print("do_L3_ARP= %04x" % self.mac.type.value)

        if self.mac.type.value != 0x0806:
            return False

        if self.verbosity & VERBOSITY_ARP:
            print("=== have ARP Mac frame")

        if self.arp.hard_type.value != 1:
            print("not arp due to hard_type")
            return False
        if self.arp.prot_type.value != 0x0800:
            print("not arp due to prot_type")
            return False
        if self.arp.hard_size.value != 6:
            print("not arp due to hard_size")
            return False
        if self.arp.prot_size.value != 4:
            print("not arp due to prot_size")
            return False
        if self.arp.op.value != 1:
            print("not arp due to op")
            return False

        # have a valid ARP frame,
        # may or may not be our IP address
        if self.arp.ip_addr_target.value != self.our_ip_addr:
            print("arp, ip addr does not match")
            return False

        # have an ARP frame addressed to us, need to respond
        if self.verbosity & VERBOSITY_ARP:
            print("Have a valid ARP frame, addressed to this endpoint")

        # switch mac layer DA,SA
        addr_tmp = self.mac.sa.value
        self.write(frame, self.mac.da, addr_tmp)             # DA on the wire (orig SA)
        self.write(frame, self.mac.sa, self.our_mac_addr)    # SA on the wire (our sa)

        # switch ARP layer DA,SA
        self.write(frame, self.arp.mac_addr_sender, self.our_mac_addr)
        self.write(frame, self.arp.mac_addr_target, addr_tmp)

        # switch ARP layer IP
        ip_tmp = self.arp.ip_addr_sender.value        # 4 bytes
        self.write(frame, self.arp.ip_addr_sender, self.our_ip_addr)
        self.write(frame, self.arp.ip_addr_target, ip_tmp)

        # set op to ARP response
        self.write(frame, self.arp.op, 2)      # ARP reply, 2 byte

        # add our mac to the ARP response
        self.write(frame, self.arp.mac_addr_target, self.our_mac_addr)    # SA on the wire (our sa)

        print("ARP response frame ready for transmit")

        if self.verbosity & VERBOSITY_ARP:
            print("Processing ARP frame complete")

        return True

    def do_L3_IP(self, our_ip_addr):
        # verify we have a IP frame

        if self.ip.version.value != 4:
            return False

        if self.ip.dest_ip.value != our_ip_addr:
            return False

        header_length = self.ip.header_length.value
        if header_length < 5:
            return False

        if self.mac.type.value != 0x0800:
            return False

        total_length = self.ip.length.value  # 32 bit words

        header_offset_bytes = self.ip.header_length.offset >> 3
        print("header_offset_bytes =", header_offset_bytes)
#        if not self.do_IP_checksum(header_offset_bytes):
        if not self.do_IP_checksum(self.ip.header_checksum,
                header_offset_bytes, self.ip.header_length.value << 2):
            print("rejecting frame due to IP checksum error")
            return False

        print("Have a valid IP Frame, addressed to us with good checksum")
        # have a valid IP frame addressed to us
        return True

    def do_IP_checksum(self, checksum, start, length):
        """ returns true if checksum is valid """
        # checksum -- checksum in pkt, if 0 then no check needed
        # start, length are in bytes

        data_frame = self.data_frame

        # received chksum==0 -> do not check checksum
        if checksum.value == 0:
            return True

        print("length=", length)

        sum = 0
        for i in range(0, length, 2):
            word = data_frame[start + i] << 8
            word |= data_frame[start + i + 1]
            sum += word
        sum += sum >> 16
        sum &= 0xffff
        retval = sum == 0xffff

        print("sum=", sum)

        return retval

    def do_ICMP(self):
        # have valid IP-ICMP frame
        type = self.icmp.type.value
        code = self.icmp.code.value
        # note checksum cover entire packet from ICMP header onward

        checksum = self.icmp.checksum

        checksum_start = self.icmp.type.offset >> 3     # bytes
        pkt_length = self.ip.length.value               # bytes
        icmp_size = pkt_length - self.ip.length_bytes

        retval = self.do_IP_checksum(checksum, checksum_start, icmp_size)

        if retval or checksum == 0:
            return type, code
        else:
            return None, None

    def do_PING(self):
        self.verbosity |= VERBOSITY_PING

        if self.verbosity & VERBOSITY_PING:
            print("do_L3_PING= %04x" % self.mac.type.value)

        if self.verbosity & VERBOSITY_PING:
            print("=== have PING frame")

        frame = self.data_frame

        # switch mac layer DA,SA
        addr_tmp = self.mac.sa.value
        self.write(frame, self.mac.da, addr_tmp)             # DA on the wire (orig SA)
        self.write(frame, self.mac.sa, self.our_mac_addr)    # SA on the wire (our sa)

        # change ping request to ping replay
        self.write(frame, self.icmp.type, 0)             # DA on the wire (orig SA)

        # switch IP layet, source & destination IP addresses
        addr_tmp = self.ip.dest_ip.value
        self.write(frame, self.ip.dest_ip, self.ip.src_ip.value)
        self.write(frame, self.ip.src_ip, addr_tmp)

        print("PING response frame ready for transmit")

        if self.verbosity & VERBOSITY_PING:
            print("Processing PING frame complete")

        return True

    def process_frame(self, data_frame):
        print("\n**************************")
        print("* Processing frame # ", self.frame_count)
        print("**************************")
        self.frame_count += 1

        self.print_frame_buffer(data_frame)

        self.data_frame_orig = copy.copy(data_frame)
        self.set_field_shadows(data_frame)  # parse the buffer into fields

        print("    da= %012x" % self.mac.da.value)
        print("    sa= %012x" % self.mac.sa.value)
        print("our sa= %012x" % self.our_mac_addr)
        print("our ip= ", ip_int2str(self.our_ip_addr), "/0x%08x" % self.our_ip_addr)
        print("tgt ip= ", ip_int2str(self.arp.ip_addr_target.value),
                "/0x%08x" % self.arp.ip_addr_target.value)
        print("snd ip= ", ip_int2str(self.arp.ip_addr_sender.value),
                "/0x%08x" % self.arp.ip_addr_sender.value)

        self.print_frame(data_frame)

        # filter out frames too long and address not our own
        print("Warning.. Mac address filter disabled")
        if False:
            if not self.frame_filter(data_frame, self.our_mac_addr):
                return False

        # here IFF addressed to us and frame is short (ie ARP or PING)
        if verbosity & VERBOSITY_FRAME:
            self.print_frame(data_frame)
            print("da=%x" % self.mac.da.value)
            print("len=", len(data_frame))

        # is frame an ARP frame?
        if self.do_L3_ARP(data_frame, self.our_ip_addr):
            print("L3 ARP:")
            self.printBeforeAndAfter()
            return True

        self.print_frame_buffer(data_frame)

        if self.do_L3_IP(self.our_ip_addr):
            print("valid IP, addressed to us")
            # have valid IP frame
            type, code = self.do_ICMP()
            if type == 8 and code == 0:
                # have valid IP-ICMP frmae addressed to us
                if self.do_PING():
                    print("L3 PING:")
                    self.printBeforeAndAfter()
                    return True

        return False

    def printBeforeAndAfter(self):
        print("original frame:")
        self.print_frame_buffer(self.data_frame_orig, bytesperline=16)
        print("our frame response:")
        self.print_frame_buffer(self.data_frame, bytesperline=16)

class LAB:
    def __init__(self, args):
        self.args = args
        self.our_mac_addr = mac_str2int(args.mac_addr)
        self.our_ip_addr = ip_str2int(args.ip_addr)
        self.frame = FRAME(self.our_mac_addr, self.our_ip_addr) # constructor

        self.iname = "eno1"
        self.pkt_type = 8003
        self.response_timeout = 0.3     # needed?
        self.max_pkt_size = 8192

        self.kbhit_h = ascii.Ascii(self.quit)

        # open socket and register for test packets
        # note: we want both ARP and PING packets
        self.s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.pkt_type))
        self.s.bind((self.iname, 0))
        self.s.setblocking(0)
        # change keybaord to non-blocking, so we can get a quit.

    def quit(self, c):
        # c= character
        self.kbhit_h.close()
        self.s.close()
        print("normal exit")

        sys.exit(1)


    def recv_frame(self):
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

    def xmit_frame(self, frame):
        msg = bytearray(frame)
        retcode = self.s.send(msg)
        return retcode

    def doit(self):
        processed_frame_counter = 0
        while True:
            data_frame = self.recv_frame()
            if len(data_frame) == 0:
                continue

            # have a receive frame, need to process
            if self.frame.process_frame(data_frame):
                # have valid ARP or PING frame
                # need to send response
                # xmit frame len, matches receive frame
                self.xmit_frame()

                processed_frame_counter += 1
                print("processed_frame_counter=", processed_frame_counter)

        print("\nrecognized_frame_counter=", processed_frame_counter)



class TEST:
    def __init__(self, args):
        self.args = args
        self.our_mac_addr = mac_str2int(args.mac_addr)
        self.our_ip_addr = ip_str2int(args.ip_addr)

        self.frame = FRAME(self.our_mac_addr, self.our_ip_addr) # constructor

        # self.data_frames = self.readfile(args.datafile)
        if args.capture_scapy:
            self.data_frames = self.readfile_Capture(args.datafile)     # all capture frames from netrok
        elif args.capture_wireshark:
            self.data_frames = self.readfile_Wireshark(args.datafile)
        else:
            print("Error: unknown capture vehicle")
            sys.exit(1)

        print("# of frames read: ", len(self.data_frames))

        processed_frame_counter = 0
        for framecounter in range(len(self.data_frames)):
            # get the frame from the datafile
            data_frame = self.data_frames[framecounter]  # place frame into buffer
            if self.frame.process_frame(data_frame):
                processed_frame_counter += 1
                print("processed_frame_counter=", processed_frame_counter)

        print("\nrecognized_frame_counter=", processed_frame_counter)

    def readfile_Wireshark(self, filename):
        # return self.readfile_Capture(filename, type='wireshark')
        return self.readfile_Capture_k12(filename)

    def readfile_Capture_k12(self, filename):
        fin = open(filename, 'r')

        frames = []
        for line in fin:
            line.strip()

            # format is assumed to be wirshark, k1-12 format
            if line[0] == '+':
                continue
            tokens = line.split()
            if len(tokens) != 2:
                continue
            if tokens[1] == "ETHER":
                continue

            # token2 is the packet
            frame = []
            tokens = tokens[1].split('|')
            tokens = tokens[1:]
            for token in tokens:
                if len(token) == 0:
                    continue
                try:
                    value = int(token,16)
                except ValueError:
                    print("not a hex string: ", token)
                frame.append(value)
            frames.append(frame)

        fin.close()
        return frames

    def readfile_Capture(self, filename, type='scapy'):
        fin = open(filename, "r")

        frames = []
        if type == 'wireshark':
            frames.append([])

        for line in fin:
            if '#' in line:
                ii = line.find('#')
                line = line[:ii]
            line.strip()
            tokens = line.split()
            if len(tokens) == 0:
                if type == 'wireshark':
                    frames.append([])
                continue

            # appear to have valid data line
            # identify frame header lines)
            if type == 'scapy' and ':' in tokens[1]:
                # have header line
                frames.append([])
                continue

            for token in tokens[1:]:
                if '.' in token:
                    # at the alphanumeric summary at EOL
                    break
                frames[-1].append(int(token, 16))

        # frames is now 2d list of frames, with integerized bytes
        print(" # of frames in read file: ", len(frames))

        fin.close()
        return frames

    def readfile_Axis(self, filename):
        # read the file, create frames (list w one frame per entry)
        try:
            fin = open(filename, "r")
        except IOError:
            print("Error: Cannot open " + filename)
            sys.exit(1)

        frames = []
        frame_bytes = []    # pycharm happy
        for line in fin:
            if '=' in line:
                continue
            line.strip()
            data = int(line, 16)

            last_bit = data & LAST_BIT
            keep_bits = (data & KEEP_BITS) >> 64

            for i in range(8):
                if keep_bits & (1 << i):
                    # have keep bits for this byte
                    data_byte = (data >> (i << 3)) & 0xff
                    frame_bytes.append(data_byte)

            if len(frame_bytes) == 0:
                print("empty frame records/line detected")
                sys.exit(1)

            if last_bit:
                frame_bytes[-1] |= LAST_BIT_BYTE
                frames.append(frame_bytes)
                frame_bytes = []

        # close input file
        fin.close()

        if frames == []:
            print("ERROR, no frames extracted")
            sys.exit(1)

        if len(frame_bytes):
            print("ERROR, last frame is incomplete, ignored")

        print("Note: ", len(frames), " frames were extracted from file: ", filename)

        return frames


def main():
    # ack testing
    mac_addr_s = "01:02:03:04:05:06"
    ip_addr_s = "192.168.1.1"
    datafile = "./data_arp.txt"

    # ping test
    mac_addr_s = "74:24:09:0f:09:0e"
    ip_addr_s = "74.06.231.20"
    ip_addr_s = "8.8.8.8"
    # datafile = "./data_ping.txt"
    datafile = "./testing1.txt"

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-m', action='store', dest='mac_addr', default=mac_addr_s)
    arg_parser.add_argument('-i', action='store', dest='ip_addr', default=ip_addr_s)
    arg_parser.add_argument('-f', action='store', dest='datafile', default=datafile)
    arg_parser.add_argument('-w', action='store_true', dest='capture_wireshark', default=False)
    arg_parser.add_argument('-s', action='store_true', dest='capture_scapy', default=False)
    arg_parser.add_argument('-l', action='store_true', dest='lab', default=False)

    args = arg_parser.parse_args()

    if args.lab:        # must run root, open socket to listen and transmit
        sim = LAB(args)
    else:
        sim = TEST(args)


# start the program
if __name__ == '__main__':
    main()
