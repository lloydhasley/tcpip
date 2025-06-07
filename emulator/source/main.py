

import os
import sys


from tcpip import TcpIp


def main():
    path_to_main = os.path.abspath(os.path.dirname(sys.argv[0]))
    file_source = path_to_main + '/../../as/prgm.s'
    file_hex = path_to_main + '/../../as/prgm.hex'

    tcpip = TcpIp(file_source, file_hex)
    tcpip.execute()
    tcpip.execute()


# start the program
if __name__ == '__main__':
    main()

