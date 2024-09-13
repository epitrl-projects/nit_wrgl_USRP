import numpy as np
from gnuradio import gr
from gnuradio.gr import pdu
import pmt

class message_to_pdu(gr.basic_block):
    """
    A block that takes input from an Edit Text box, converts it to a PDU, and outputs the PDU.
    """

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="message_to_pdu",
            in_sig=None,  # No regular input signature
            out_sig=None  # No regular output signature
        )
        self.message_port_register_out(pmt.intern("pdu_out"))
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        # Check if the message is a string
        if pmt.is_symbol(msg):
            # Convert the string to bytes
            message_string = pmt.symbol_to_string(msg)
            message_bytes = np.frombuffer(message_string.encode('utf-8'), dtype=np.uint8)
            
            # Create a PDU (Protocol Data Unit)
            pdu_meta = pmt.PMT_NIL  # No metadata
            pdu_data = pmt.init_u8vector(len(message_bytes), message_bytes)
            pdu_message = pmt.cons(pdu_meta, pdu_data)
            
            # Output the PDU
            self.message_port_pub(pmt.intern("pdu_out"), pdu_message)
        else:
            print("Input is not a string")

