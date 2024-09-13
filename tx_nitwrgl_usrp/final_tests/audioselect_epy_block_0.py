import numpy as np
from gnuradio import gr
import pmt

class message_to_int8(gr.sync_block):
    """
    A GNU Radio block that converts messages to int8 format and outputs them.
    """

    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="message_to_int8",  # Block name
            in_sig=None,             # No direct input
            out_sig=[np.int8]        # Output signal type
        )

        # Register a message port
        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg)

        # Buffer to store the int8 data
        self.output_data = np.array([], dtype=np.int8)

    def handle_msg(self, msg):
        # Convert the input PMT message to a string
        str_data = pmt.symbol_to_string(msg)
        
        # Convert string to int8 numpy array
        int8_data = np.frombuffer(str_data.encode('utf-8'), dtype=np.int8)
        
        # Append the int8 data to the buffer
        self.output_data = np.append(self.output_data, int8_data)
        

    def work(self, input_items, output_items):
        # Determine how much data we can output
        n_output_items = min(len(self.output_data), len(output_items[0]))
        #print("sender",n_output_items)
        
        if n_output_items > 0:
            # Copy the data to the output
            output_items[0][:n_output_items] = self.output_data[:n_output_items]
            
            # Remove the outputted data from the buffer
            self.output_data = self.output_data[n_output_items:]
        
        # Return the number of items produced
        return n_output_items
