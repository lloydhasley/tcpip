#
#
# emulates kbit,
# but within a class so opening/closing can be separated
#
# returns char if one present
# returns None if no chars present
#

import select
import sys
import termios
import tty
import os


class Ascii():
    def __init__(self, callback=None):
        self.callback = callback
        self.open()

    def open(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
#        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())

    def close(self):
        # restore original terminal settings
        print("Restoring terminal settings")
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

        # above statement does not seem work on MAC
        os.system("stty sane")

    def kbhit(self):
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            c = sys.stdin.read(1)
            if c == 3:      # control-c
                print("^C detected")
                if self.callback:
                    self.callback()

            print(c, end='')
            return c
        else:
            return False

