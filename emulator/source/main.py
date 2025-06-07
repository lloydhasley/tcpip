
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

from emul import Emul


interfaces = {
    'home': { 'mac_addr':'02:fe:dc:ba:98:72', 'ip':'192.168.1.254', 'interf':'/sys/class/net/eno1'},        # lah's lhc2
    'smu': {'mac_addr': '02:fe:dc:ba:98:72', 'ip': '192.168.0.254', 'interf':'/sys/class/net/enp98s0f0'}    # lab's larc
}


def validate_environment():
    rootcheck = False

    if rootcheck:
        # check that we are running as root (neccessary for socket operations
        uid = os.getuid()
        if uid != 0:
            print("You must run this script as root")
            sys.exit(1)

    # determine operational site (home, smu labnet)
    for location, interface in interfaces.items():
        interf = interface['interf']
        if os.path.exists(interf):

            break
    if location is None:
        print("location determined: ", location)
    else:
        print("Cannot determine network location")
        sys.exit(1)

    return location


def main():
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
    args = arg_parser.parse_args()

    emul = Emul(args)
#    tcpip = TcpIp(args)
#    tcpip.do_execute()
#    tcpip.do_execute()


# start the program
if __name__ == '__main__':
    main()

