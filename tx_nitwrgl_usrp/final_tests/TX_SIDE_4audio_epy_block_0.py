






import numpy as np
from gnuradio import gr
import pmt

class message_to_int8(gr.sync_block):
    """
    A GNU Radio block that converts messages to int8 format and outputs them.
    Optimized for faster live streaming with both blob and string handling.
    """

    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="message_to_int8_optimized",  # Block name
            in_sig=None,                       # No direct input
            out_sig=[np.int8]                  # Output signal type
        )

        # Register a message port
        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg)

        # Buffer to store the int8 data
        self.output_data = np.array([], dtype=np.int8)
        self.data_ready = False  # Flag to track if new data is ready

    def handle_msg(self, msg):
        # Check if the message is a blob (binary data)
        if pmt.is_blob(msg):
            # Extract blob data directly as int8
            blob = pmt.blob_data(msg)
            int8_data = np.frombuffer(blob, dtype=np.int8)
            print("Received blob data:", int8_data)

        # Handle the case where the message is a string
        elif pmt.is_symbol(msg):
            # Convert the string to int8 numpy array
            str_data = pmt.symbol_to_string(msg)
            int8_data = np.frombuffer(str_data.encode('utf-8'), dtype=np.int8)
            print("Received string data:", int8_data)

        else:
            print("Unsupported PMT message type:", msg)
            return

        # Update the buffer with the new data
        self.output_data = np.append(self.output_data, int8_data)
        self.data_ready = True

    def work(self, input_items, output_items):
        if not self.data_ready:
            return 0  # No new data to output

        # Determine how much data we can output
        n_output_items = min(len(self.output_data), len(output_items[0]))

        if n_output_items > 0:
            # Directly copy data to the output buffer
            output_items[0][:n_output_items] = self.output_data[:n_output_items]

            # Remove the outputted data from the buffer
            self.output_data = self.output_data[n_output_items:]

            # If we've exhausted the buffer, reset the data_ready flag
            if len(self.output_data) == 0:
                self.data_ready = False

        # Return the number of items produced
        return n_output_items
