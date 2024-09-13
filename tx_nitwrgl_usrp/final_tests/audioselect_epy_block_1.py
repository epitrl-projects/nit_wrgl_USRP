import numpy as np
from gnuradio import gr
import pmt

class int8_to_message(gr.sync_block):
    """
    A GNU Radio block that converts int8 input to a string and sends it as a message to update a QT GUI Chooser.
    """

    def __init__(self,chooser_block=None):
        gr.sync_block.__init__(
            self,
            name="int8_to_message",  # Block name
            in_sig=[np.int8],        # Input signal type
            out_sig=None             # No direct output
        )
        
        # Register an output message port
        self.message_port_register_out(pmt.intern("msg_out"))
        self.chooser_block = chooser_block

    def work(self, input_items, output_items):
        # Convert int8 input to a byte array
        byte_array = input_items[0].tobytes()
        
        # Convert byte array to string
        converted_string = byte_array.decode('utf-8')
        converted_string = converted_string[-1]
        print("data received",converted_string)
        self.chooser_block=int(converted_string)
        
        # Convert string to a PMT symbol
        msg = pmt.intern(converted_string)
        
        # Send the message out
        self.message_port_pub(pmt.intern("msg_out"), msg)
        
        return len(input_items[0])

