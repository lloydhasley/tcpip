#
# execute an instruction
#

from rom import Rom


class Execute:
    def __init__(self, instr, bus, rom, verbose=0):
        self.instr = instr
        self.instr_defs = instr.instrs
        self.decodes = instr.decodes
        self.get_instr_fcn(self.instr_defs)     # get module functions handlers
        self.bus = bus      # system bus:  16 bits wide
        self.rom = rom      # pointer to rom class (rom.rom for the data)
        self.verbosity = verbose

        self.max_instruction_width = 20

        # we ASSUME all instructions have same format!!! (for now)
        #   <opcode><operand>
        position = self.instr_defs[0]['pos']
        self.operand_mask = (1 << position) - 1
        self.opcode_mask = ((1 << self.max_instruction_width) - 1) - self.operand_mask

        self.PC = 0         # program counter
        self.AR = 0         # accumulator

    def execute(self):
        instr_num = self.rom(self.PC)
        opcode_shifted = instr_num & self.opcode_mask
        operand = instr_num & self.operand_mask

        fcn = self.decodes[opcode_shifted]['fcn']
        fcn(operand)

    def get_instr_fcn(self, instr_def):
        print("entering get_instr_fcn aaa", instr_def)
        print("instr_def", instr_def)
        for instr in instr_def:
            try:
                fcn_name = instr['handler']
                fcn = getattr(self, fcn_name)
                instr['fcn'] = fcn
            except:
                print("Error: Cannot locate handler for: ", instr['name'])

    def addW(self, operand):
        if self.verbose & 1:
            print("ADD,W %02x" % operand)

        bus_value = self.bus.read(operand)
        self.AR += bus_value

    def addIW(self, operand):
        if self.verbose & 1:
            print("ADD,I,W %02x" % operand)

        self.AR += operand

    def addWI(self, operand):   # w/ indirect
        if self.verbose & 1:
            print("ADD,W,I %02x" % operand)

        # add with one layer of indirectness
        address = self.bus.read(operand)
        bus_value = self.bus.read(address)
        self.AR += bus_value

    def jmp(self, operand):
        if self.verbose & 1:
            print("JMP %02x" % operand)

        self.PC = operand

    def jnz(self, operand):
        if self.verbose & 1:
            print("JNZ %02x" % operand)

        if self.AR:
            self.PC = operand

    def jz(self, operand):
        if self.verbose & 1:
            print("JZ %02x" % operand)

        if not self.AR:
            self.PC = operand

    def jneg(self, operand):
        if self.verbose & 1:
            print("JNEG %02x" % operand)

        if self.AR & 0x8000:
            self.PC = operand

    def jmpI(self, operand):
        if self.verbose & 1:
            print("JMP,I %02x" % operand)

        # jump indirect
        address = self.bus.read(operand)
        self.PC = address

    def ldaB(self, operand):
        if self.verbose & 1:
            print("LDA,B %02x" % operand)

        bus_value = self.bus.read(operand, byte=True)
        bus_value &= 0xff
        self.AR = bus_value

    def ldaW(self, operand):
        if self.verbose & 1:
            print("LDA,W %02x" % operand)

        bus_value = self.bus.read(operand)
        bus_value &= 0xffff
        self.AR = bus_value

    def ldiB(self, operand):
        if self.verbose & 1:
            print("LDI,B %02x" % operand)

        self.AR = operand & 0xff

    def ldiW(self, operand):
        if self.verbose & 1:
            print("LDI,W %02x" % operand)

        self.AR = operand & 0xffff

    def nop(self, operand):
        if self.verbose & 1:
            print("NOP %02x" % operand)
        pass

    def staB(self, operand):
        if self.verbose & 1:
            print("STA,B %02x" % operand)

        self.bus.write(operand, self.AR, byte=True)
        self.AR = operand & 0xff

    def staW(self, operand):
        if self.verbose & 1:
            print("STA,W %02x" % operand)

        self.bus.write(operand, self.AR)
        self.AR = operand & 0xff

    def subiB(self, operand):
        if self.verbose & 1:
            print("SUBI,B %02x" % operand)

        self.AR += (~operand) + 1
        self.AR &= 0xffff

    def rotrIW(self, operand):
        if self.verbose & 1:
            print("ROTR,IW %02x" % operand)

        self.AR >>= operand

    def rotlIW(self, operand):
        if self.verbose & 1:
            print("ROTL,IW %02x" % operand)

        self.AR <<= operand

    def xorIB(self, operand):
        if self.verbose & 1:
            print("XOR,IB %02x" % operand)

        self.AR ^= operand
        self.AR &= 0xff

    def xorW(self,operand):
        if self.verbose & 1:
            print("XOR,W %02x" % operand)

        data = self.bus.read(operand)
        self.AR ^= data
