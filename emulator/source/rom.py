#
# execute an instruction
#
class Rom:
    def __init__(self, hex_program):
        self.rom = hex_program          # rom has hex numbers from assembler

    def read(self, address):
        return self.rom[address]


