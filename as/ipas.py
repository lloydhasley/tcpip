#! /usr/bin/python3

import argparse
import sys
import shlex
import math


class Assembler:
    def __init__(self, args):
        self.verbose = args.verbose
        self.infile = args.infile

        self.space = ' \t'
        self.instrs = {}
        self.labels = {}
        self.errcount = 0
        self.line_number = 0
        self.precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        self.instr_errcount = 0
        self.instr_seen = {}
        self.instr_unknown = {}

        self.pass_id = 1
        self.do_pass(args, self.pass_id)

        if args.verbose:
            self.print_instr()

        if args.verbose:
            self.print_symbol_table(sys.stdout)

        self.width = []
        self.depth = []

        if self.errcount > 0:
            self.early_end(1)

        try:
            self.fout = open(args.listing, 'w')
        except IOError:
            print("Error: Cannot open listing file:", args.listing)
            sys.exit(1)

        self.pass_id = 2
        self.do_pass(args, self.pass_id)
        self.check_instr_used()

        print("Assembly complete, ", self.errcount  + self.instr_errcount, " errors were encountered.")
        print("\t             Assembly errors: ", self.errcount)
        print("\t         Instruct def errors: ", self.instr_errcount)
        print("\t# instr defined but not used: ", self.instr_unused)

        self.print_symbol_table(self.fout)   # add to listing file
        self.fout.close()

        self.print_hex_out(args.hexfile)


    def error_detected(self):
        print("Error detected, line no: ", self.line_number)
        self.errcount += 1

    def early_end(self, code):
        print("Errors encountered: ", self.errcount)
        sys.exit(code)

    def do_pass(self, args, pass_id):
        # first pass, builds symbol/label dictionary
        # 2nd pass builds code
        instr_seen = {}
        instr_unknown = {}

        if args.verbose:
            print("**********************************")
            print("* PASS: ", pass_id)
            print("**********************************")
        pc = 0

        # open file
        try:
            fin = open(args.infile)
        except IOError:
            print("Error: Cannot open file '{}'".format(args.infile))
            sys.exit(1)

        # initial line processing
        self.line_number = 0
        for line in fin:
            self.line_number += 1
            line = line.rstrip()
            line_orig = line

            ii = line.find(';')     # line comments
            if ii != -1:
                line = line[:ii]

            # break line up into tokens
            tokens = shlex.split(line)      # maintain quoted strings
            if len(tokens) == 0:
                self.print_out_line(line_orig)
                continue                    # blank line

            # (jump) labels
            ii = tokens[0].find(':')
            if ii != -1:
                # have a label
                label = tokens[0][:ii]
                if pass_id == 1:
                    self.set_label(label, pc)
                tokens = tokens[1:]
                if len(tokens) == 0:        # label only line, so print
                    self.print_out_line(line_orig, addr=pc)
                    continue
                # proceed w reset of line

            l = len(tokens)
            if l > 2:       # have at least 3 tokens
                if tokens[1] == 'equ':
                    label = tokens[0]
                    value = self.exp(tokens[2:])
                    if pass_id == 1:
                       self.set_label(label, value)

                    self.print_out_line(line_orig, data=value)
                    continue

            if l >= 6:
                if tokens[0] == 'inst':
                    if pass_id == 1:
                        name = tokens[1]
                        value = int(tokens[2],0)
                        operand = int(tokens[3], 0)
                        pos = int(tokens[4], 0)
                        length = int(tokens[5], 0)

                        if name in self.instrs:
                            print("ERROR: Duplicate instruction '{}'".format(name))
                            print("duplicate ignored")
                            continue

                        self.instrs[name] = {'value': value, 'length': length, 'operand': operand, 'pos': pos}

                    self.print_out_line(line_orig)
                    continue

            instr_name = tokens[0]

            # statistics on instruction
            #   counts known and unknown
            if instr_name in instr_seen:
                self.instr_seen[instr_name] += 1
            else:
                self.instr_seen[instr_name] = 1
            if instr_name not in self.instrs:
                self.instr_unknown[instr_name] = 1

            # regular instruction -> opcode <operand>
            if instr_name not in self.instrs:
                print("Unknown instr_name '{}'".format(instr_name), 'at line no: ', self.line_number)
                self.error_detected()
                instr_name = "nop"

            instr = self.instrs[instr_name]
            instr_value = instr['value']        # instruction opcode (not shifted into position)
            instr_length = instr['length']      # number of words consumed by instruction
            instr_operand = instr['operand']    # number of operands
            instr_pos = instr['pos']

            value_limit = 1 << instr_pos

            if l >= instr_operand:
                # check for specials
                if instr_name == 'org':
                    pc = self.exp(tokens[1])

                    self.print_out_line(line_orig, addr=pc)
                    continue
                elif instr_name == 'rom':
                    tokens = tokens[1].split('x')
                    self.width = int(tokens[0], 0)
                    self.depth = int(tokens[1], 0)
                    self.rom = [0 for x in range(self.depth)]

                if l >= 2:
                    operand = tokens[1]
                else:
                    print('ERROR: Invalid syntax at line no: ', self.line_number)
                    self.error_detected()
                    sys.exit(1)

                # on first pass, we only want labels
                #   not all dependencies will be known during pass1, do not call self.exp
                if pass_id != 1:
                    operand_value = self.exp(operand)
                else:
                    operand_value = 0

                if operand_value >= value_limit:
                    print("ERROR: operand value is too large, at line no: ", self.line_number)
                    self.error_detected()

                value = (instr_value << instr_pos) | operand_value
                self.rom[pc] = value
                self.print_out_line(line_orig, addr=pc, data=value)

                pc += instr_length
                continue

            print("ERROR: unknown line, at line: ", self.line_number)
            self.error_detected()

        # close file
        fin.close()

    def check_instr_used(self):
        self.instr_unused = 0
        self.instr_values = []
        for key, value in self.instr_seen.items():
            if value == 0:
                print("WARNING, instruction defined but not used: ", key)
                self.instr_unused += 1
            instr_value = self.instrs[key]['value']
            if self.instrs[key]['length']:
                if instr_value in self.instr_values:
                    print("ERROR: duplicate instruction value: '{}'".format(instr_value))
                    self.error_detected()
                else:
                    self.instr_values.append(instr_value)

        if self.instr_unused:
            print("Note: All defined instructions are used")

    def print_instr(self):
        # print out instruction table
        sort_instr = {key: value for key, value in sorted(self.instr_seen.items())}
        self.instr_errcount = 0
        for key, value in sort_instr.items():
            if key in self.instr_unknown:
                status = False
                self.instr_errcount += 1
            else:
                status = True
            print(" instr: %8s" % key, " count=%2d" % value, " known=", status)
        num_instr = len(self.instr_seen)
        print("     instr_num=", num_instr)
        print("instr_errcount=", self.instr_errcount)

    def print_out_line(self, line, addr=None, data=None):
        # only print during pass2
        if self.pass_id == 1:
            return

        if addr is not None:
            addr_str = "%03x" % addr
        else:
            addr_str = "   "

        if data is not None:
            data_str = "%05x" % data
        else:
            data_str = "     "


        outstr = addr_str + " " + data_str + "  " + line

        print(outstr, file=self.fout)

    def print_symbol_table(self, fout):
        # add to listing file
        keys_sorted = {key: value for key, value in sorted(self.labels.items())}

        print("\n\nSymbol Table:", file=fout)
        for key in keys_sorted:
            print("%35s" % key, "\t", self.labels[key], file=fout)
        print("note: # of symbols defined: ", len(keys_sorted), file=fout)

    def print_hex_out(self, filename):
        width = self.width
        dig_width = math.floor((width + 3)/4)
        dif_format = '%0' + str(dig_width) + 'x'
        try:
            fout = open(filename, 'w')
        except IOError:
            print("Cannot open hex file: ", filename, " for writing")
            sys.exit(1)

        for addr in range(self.depth):
            value = self.rom[addr]
            print(dif_format % value, file=fout)

        fout.close()

    def set_label(self, label, value):
        if label in self.labels:
            print("Label '{}' already set".format(label), " at line: ", self.line_number)
            self.error_detected()
            return
        self.labels[label] = value

    def exp(self, expression):
        # evaluate an expression;  all terms must be previously known
        #print("expression=", expression)

        if isinstance(expression, str):
            l = []
            l.append(expression)
            expression = l

        stack = []
        exp_s = ' '.join(expression)
        # exp1 = exp_s.replace('.', '+')        # determine hierarchal address
        exp1 = exp_s
        for char in '+-*/()':
            exp1 = exp1.replace(char, ' ' + char + ' ')

        tokens = shlex.split(exp1)
        exp_list = []
        for token in tokens:
            try:
                value = int(token, 0)
            except:
                # cannot convert to integer
                # should be in labels.
                if token in self.labels:
                    value = self.labels[token]
                else:
                    value =  token
            exp_list.append(value)

        tokens = self.infix_to_postfix(exp_list)
        for token in tokens:
            if token in self.labels:
                token = self.labels[token]
            if isinstance(token, int):
                stack.append(token)
            elif token in self.precedence: # not an integer string, try an operator
                # operator
                if len(stack) < 2:
                    print("Fatal Error in expression: ", expression, " at line: ", self.line_number)
                    sys.exit(1)
                b = stack.pop()
                a = stack.pop()
                if token == "+":
                    c = a + b
                elif token == '-':
                    c = a - b
                elif token == '*':
                    c = a * b
                elif token == '/':
                    c = a / b
                stack.append(c)
            else:
                print("ERROR: unknown token: ", token, " at line: ", self.line_number)
                self.error_detected()
                self.early_end(1)        # not recoverable

        value = stack.pop()
        return value

    def infix_to_postfix(self, exp):
        output = []
        stack = []

        for term in exp:
            if term not in self.precedence:
                output.append(term)
            elif term == '(':
                stack.append(term)
            elif term == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            #elif term in self.precedence:
            else:
                while stack and stack[-1] != '(' and self.precedence[term] <= self.precedence[stack[-1]]:
                    output.append(stack.pop())
                stack.append(term)

        while stack:
            output.append(stack.pop())
        return output

    def get_value(self, value_s):
        if value_s in self.labels:
            value = self.labels[value_s]
        else:
            value = 0

        return value


def main():

    arg_parser = argparse.ArgumentParser()
#    arg_parser.add_argument('-i', action='append', dest='infile')
#    arg_parser.add_argument('-i', dest='infile')

#    arg_parser.add_argument('-l', dest='logfile', default=None)
    arg_parser.add_argument('-v', dest='verbose', action='store_true', default=False)
#    arg_parser.add_argument('-c', action='store', dest='configuration', default=configuration)
#    arg_parser.add_argument('-S', action='store_false', dest='signenable', default=True)
    # note: tapename is optional, can be specified in run script
#    arg_parser.add_argument('-t', action='store', dest='tapename', default=None, help="tape name")
    # signenable=1 vtrace files displays integers as signed, else 29bits unsigned
    arg_parser.add_argument('sourcefile', nargs='?', default=None)
    args = arg_parser.parse_args()

    if args.sourcefile is None:
        print("ERROR: no source file specified")
        sys.exit(1)

    # auto derive listing and object (Verilog Rom) file
    sfile = args.sourcefile
    ii = sfile.find('.')
    if ii == -1:
        args.infile = sfile + '.s'
    else:
        args.infile = sfile
        sfile = sfile[:ii]
    args.hexfile = sfile + '.hex'
    args.listing = sfile + '.lst'

    a = Assembler(args)
#    print("formats:", a.instr.formats)
#    a.instr.print_db()

# start the program
if __name__ == '__main__':
    main()

