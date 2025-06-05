###################
#
# captures network traffice and puts into a Verilog ROM file
#
#
# stepping stone on way to Verilog of a data handler
#
###############################

import socket
import select
import struct
import time
import sys
import os


NUMFRAMES = 10000

# broadcast -- ARP/RARP
# MAC addressed

class IO:
    def __init__(self, timeout=0.3):
        self.iname = "eno1"
        self.timeout = timeout
        self.maxframesize = 8192
        self.datawidth = 64
        self.databytes = self.datawidth >> 3

        self.pad = bytes(self.databytes)

        self.s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x003))
        self.s.bind((self.iname, 0))
        host = socket.gethostbyname(socket.gethostname())

        # as a capture program we leave it in blocking mode
        #        self.s.setblocking(0)

    def close(self):
        self.s.close()

    def get_frames(self, frame_count):
        frames_multiple = []
        for i in range(frame_count):
            print("pktcnt=", i)
            frame_single = self.get_frame()
            frames_multiple += frame_single

        return frames_multiple

    def get_frame(self):
        # polling to get a frame, any frame

        if False:
            # is a frame available
            ready, _, _ = select.select([self.s], [], [], self.timeout)
            if self.s  not in ready:
                # nothing received
                print("no frame")
                return []

            print("frame ready")

        (msg, addr) = self.s.recvfrom(self.maxframesize)
        msg_len = len(msg)
        print("msg_len=", msg_len)
        r = len(msg) % 8  # 0-7

        # pad out to 64 bits
        pad_l = (8 - r) % 8
        if pad_l:
            msg += self.pad[:pad_l]

        frame_64 = []
        for int64 in struct.iter_unpack('<Q', msg):
            data = int64[0] | (0xff << 64)
            frame_64.append(data)

        frame_64[-1] &= (1 << 64) - 1          # remove intermediate keep
        frame_64[-1] |= ((1 << r) - 1) << 64   # apply final word keep
        frame_64[-1] |= (1 << 64) << 8         # apply last bit

        return frame_64

    def printAxis(self, frame):
        for word in frame:
            print("%019X" % word)

def main():
    io = IO()
    frames = io.get_frames(NUMFRAMES)
    io.printAxis(frames)
    io.close()

main()


