import numpy as np
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio import uhd

class TextTransmitter(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        # Parameters
        samp_rate = 1e6
        freq = 2.4e9

        # Create a block to convert string to byte stream
        text = "Hello World"
        text_bytes = text.encode('utf-8')  # Convert text to bytes
        byte_source = blocks.vector_source_b(list(text_bytes), True)

        # BPSK Modulation
        bpsk_constellation = digital.constellation_bpsk().base()
        modulator = digital.chunks_to_symbols_bc(bpsk_constellation.points())

        # Create a USRP sink block
        usrp_sink = uhd.usrp_sink(
            "", 
            uhd.stream_args(cpu_format="fc32", channels=[0])
        )
        usrp_sink.set_samp_rate(samp_rate)
        usrp_sink.set_center_freq(freq)
        usrp_sink.set_gain(0)

        # Connect blocks
        self.connect(byte_source, modulator, usrp_sink)

if __name__ == '__main__':
    tb = TextTransmitter()
    tb.start()
    tb.wait()
