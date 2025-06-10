
#
# top level tcpip emulator
#
# main handles command line arguments
#
# note: currently traditional cmd line arguments are presently hardcoded
#
import os
import sys
import argparse
import time

from emul import Emul


interfaces = {
    'Mac': {'mac_addr': '02:fe:dc:ba:98:72', 'ip': '192.168.1.254', 'interf': None},  # Mac Air
    'LloydAir': {'mac_addr': '02:fe:dc:ba:98:72', 'ip': '192.168.1.254', 'interf': None},  # Mac Air
    'home': {'mac_addr': '02:fe:dc:ba:98:72', 'ip': '192.168.1.254', 'interf': 'eno1'},  # lah's lhc2
    'larc': {'mac_addr': '02:fe:dc:ba:98:72', 'ip': '192.168.0.254', 'interf': 'enp98s0f0'}  # lab's larc
}


def validate_environment():
    rootcheck = False

    if rootcheck:
        # check that we are running as root (neccessary for socket operations
        uid = os.getuid()
        if uid != 0:
            os.setuid(0)
            print("You must run this script as root")
            sys.exit(1)

    # determine operational site (home, smu labnet)
    hostname = os.uname().nodename
    ii = hostname.find('.')
    if ii >= 0:
        hostname = hostname[:ii]

    print("hostname={}".format(hostname))

    if hostname not in interfaces:
        print("Hostname not found in database: {}".format(hostname))
        sys.exit(1)

    return hostname


def main():
    print("ab")
    time.sleep(1)
    location = validate_environment()
    default_mac_addr = interfaces[location]['mac_addr']
    default_ip = interfaces[location]['ip']
    default_interf = interfaces[location]['interf']

    response_timeout = 0.3
    path_to_main = os.path.abspath(os.path.dirname(sys.argv[0]))
    prgm_dir = path_to_main + '/../../as'       # change to '.' for production use

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', action='store', dest='prgm_dir', default=prgm_dir)
    arg_parser.add_argument('-n', action='store', dest='prgm_name', default='prgm')
    arg_parser.add_argument('-m', action='store', dest='mac_addr', default=default_mac_addr)
    arg_parser.add_argument('-i', action='store', dest='ip_addr', default=default_ip)
    arg_parser.add_argument('-I', action='store', dest='interface', default=default_interf)
    arg_parser.add_argument('-f', action='store', dest='data_file', default='axis.txt')
    args = arg_parser.parse_args()

    print("constructing emulation")
    emul = Emul(args)
#    tcpip = TcpIp(args)
#    tcpip.do_execute()
#    tcpip.do_execute()


# start the program
if __name__ == '__main__':
    main()

