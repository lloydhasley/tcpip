
#
# top level tcpip emulator
#
# main handles command line arguments
#
# note: currently traditional cmd line arguments are presently hardcoded
#
import threading
import sys
import time

from tcpip import TcpIp
from network import Net


class Emul:
    def __init__(self, args):
        self.args = args
        self.shut_down = False

        print("Starting emulation")

        # constructors
        self.tcpip = TcpIp(self.args)

        print("Starting threads")
        if self.args.data_file == '':
            self.network = Net(self.args)
            t1 = threading.Thread(self.NetworkReceive)
        else:
            t1 = threading.Thread(self.FileIn)
        t2 = threading.Thread(self.Processor)
        t3 = threading.Thread(self.MonitorQuit)
        t4 = threading.Thread(self.Helpers)
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        print("Note: All emulator threads started")
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        print("Note: All emulator threads stopped")

    def FileIn(self, datafile):
        fifo = self.tcpip.fifo.fifo_data

        try:
            with open(datafile) as f:
                for line in f:
                    line = line.strip()
                    word = int(line,16)
                    print("writing fifo: %019x" % word)
                    fifo.append(word)
        except IOError:
            print("Error opening file", datafile)
            sys.exit(1)

    def NetworkReceive(self):
        # check if any frames received
        while not self.shut_down:
            frame = self.network.recv_bytes()
            if frame != []:
                # copy frame into buffer
                fifo = self.tcpip.fifo.fifo_data
                for word in frame:
                    fifo.append(word)

    def Processor(self):
        # run the processor
        while not self.shut_down:
            self.tcpip.do_execute()

    def Helpers(self):
        while not self.shut_down:
            self.tcpip.fifostatus = self.tcpip.fifo.status()
            time.sleep(0.001)       # yield to other threads

    def MonitorQuit(self):
        # thread gathers lines and quits if line starts with 'q'
        user_input = input("Enter 'q' to quit")
        if user_input[0] == 'q':
            print("Beginning shutdown")
            self.shut_down = True
