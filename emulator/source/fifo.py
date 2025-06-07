#
# fifo supports a stream write interface
# and a local bus write/read or a stream read interface
#
# the streaming interfaces are emulated and move data as a list
#

class Fifo:
    SIZE = 256      # number of words
    WIDTH = 64      # streaming data width
    KEEP_WIDTH = WIDTH/8
    #
    POS_DATA = 0
    POS_KEEP = POS_DATA + WIDTH
    POS_LAST = POS_KEEP + KEEP_WIDTH
    #
    def __init__(self, verbose=0):
        self.verbost = verbose

        self.fifo_data = []

    def stream_in(self, frame):
        # frame is a byte wide list
        # need to convert to 64 bit Axis style stream
        length = len(frame)
        for i in range(7):
            frame.append(0)

        # get 8 byte integer
        for i in range(0, length, self.KEEP_WIDTH):
            # get 8 byte integer
            word_bits = 0
            for j in range(8):
                word_bits |= frame[i+j] << (j * 8)

            # last bit
            if (i + j) > length:
                last_bit = 1
                overflow = i + j - length
                keeps = self.KEEP_WIDTH - overflow
                keep_bits = (1 << keeps) - 1
            else:
                last_bit = 0

            # fifo word
            word_fifo = word_bits
            word_fifo |= keep_bits << Fifo.POS_KEEP
            word_fifo |= last_bit << Fifo.POS_LAST
            self.fifo_data.append(word_fifo)

