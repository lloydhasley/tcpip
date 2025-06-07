#
# reads output(s) from assembler to get
# instruction definitions
#
# note: instr bit assignments are read from assembler
# but the actual instructions must be previously known
# by the emulator
#

class Instr:
    def __init__(self, file_source, file_hex):
        self.instrs = self.instr_defs(file_source)      # read instr definitions
        self.decodes = self.instr_decodes(self.instrs)  # determine instr opcodes
        self.prgm = self.read_prgm(file_hex)            # read user program (hex)

    def instr_defs(self, file_source):
        lastcomment = ''
        fields = []
        instrs = []
        with open(file_source, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()     # leading/trailing space
                if len(line) <= 0:
                    continue
                ii = line.find(';')    # line comments
                if ii != -1:
                    lastcomment = line
                    line = line[:ii]
                tokens = line.split()
                if len(tokens) <= 0:
                    continue

                if tokens[0] == 'inst':
                    # capture field header
                    if fields == []:
                        fields = lastcomment.split()

                    instr = {}
                    for i in range(1, len(tokens)):
                        field_name = fields[i]
                        if i > 1:
                            tokens[i] = int(tokens[i])
                        instr[field_name] = tokens[i]
                    if instr['cycles']:
                        instrs.append(instr)
        return instrs

    def instr_decodes(self, instrs):
        decodes = {}
        for instr in instrs:
            if instr['length']:
                pos = instr['pos']
                value = instr['value']
                opcode = value << pos
                decodes[opcode] = instr
        return decodes

    def read_prgm(self, file_hex):
        prgm = []
        with open(file_hex, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()  # leading/trailing space
                if len(line) <= 0:
                    continue

                instr_hex = int(line, 16)
                prgm.append(instr_hex)
        return prgm

