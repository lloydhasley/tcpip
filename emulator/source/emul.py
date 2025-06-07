
#
# top level tcpip emulator
#
# main handles command line arguments
#
# note: currently traditional cmd line arguments are presently hardcoded
#
import threading

from tcpip import TcpIp
from network import Net


class Emul:
    def __init__(self, args):
        self.args = args
        self.shut_down = False

        # constructors
        self.tcpip = TcpIp(self.args)
        self.network = Net(self.tcpip)

        t1 = threading.Thread(self.NetworkReceive)
        t2 = threading.Thread(self.Processor)
        t3 = threading.Thread(self.MonitorQuit)
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

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

    def MonitorQuit(self):
        # thread gathers lines and quits if line starts with 'q'
        user_input = input("Enter 'q' to quit")
        if user_input[0] == 'q':
            self.shut_down = True
