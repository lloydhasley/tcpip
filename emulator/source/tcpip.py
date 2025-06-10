#
# top level of emulator
# only main(which handles cmd-line arguments is above)
#
# the various class modules are put together here:
# rom, regfile, fifo.
#
# instr reads both the program and instructions from the
# assembler output files
#
#

from instr import Instr
from exec import Execute
from rom import Rom
from regfile import RegFile
from fifo import Fifo
from bus import Bus


class TcpIp:
    def __init__(self, args, verbose=0):
        prgm_dir = args.prgm_dir
        prgm_name = args.prgm_name

        file_source = prgm_dir + '/' + prgm_name + '.s'
        file_hex = prgm_dir + '/' + prgm_name + '.hex'

        # global variables (def and initialization)
        self.fifostatus = 0
        self.FRAME_DONE = 0
        self.enable = 0
        self.ADDR_SEND_FRAME = 0
        self.EatFrame = 0

        self.instr = Instr(file_source, file_hex)
        self.rom = Rom(self.instr.prgm)
        self.regfile = RegFile(self)
        self.fifo = Fifo()

        # connect peripherals
        self.bus = Bus()
        self.bus.attach(self.regfile, 0x00, 0x80)
        self.bus.attach(self.fifo, 0x80, 0x100)

        self.execute = Execute(self.instr, self.bus, self.rom, verbose)

    def do_execute(self):
        self.execute.execute()      # executes a single instruction
