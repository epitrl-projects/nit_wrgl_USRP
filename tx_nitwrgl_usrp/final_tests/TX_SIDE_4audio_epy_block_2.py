


import os
import numpy as np
from gnuradio import gr
import pmt
import time

class message_file_sink_source(gr.basic_block):
    def __init__(self, file_path="/home/pi/Desktop/project/mytests/demo.txt", check_interval=1):
        # Define the block with no input streaming, only message input
        # Output signal is a byte stream (np.uint8)
        gr.basic_block.__init__(self,
            name="message_file_sink_source",
            in_sig=None,  # No streaming input
            out_sig=[np.uint8])  # Output byte stream

        # Register the message input port
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_message)

        # File path and check interval
        self.file_path = file_path
        self.check_interval = check_interval

        # Initialize file handling variables
        self.file_position = 0  # Track where we are in the file
        self.bytes_written = False
        self.source_file = None
        self.loop_file = False  # Initially, we do not loop
        
        
        self.stream_data = None

    def handle_message(self, msg):
        # Handle incoming messages from the message strobe
        if pmt.is_symbol(msg):
            # If message is a string (symbol), encode it as bytes
            data = pmt.symbol_to_string(msg).encode('utf-8')
        elif pmt.is_u8vector(msg):
            # If message is a u8vector (byte array), convert to a numpy array
            data = np.array(pmt.u8vector_elements(msg), dtype=np.uint8).tobytes()
        else:
            print("Unsupported message type.")
            return

            
        # Write the incoming message to the file
        try:
            with open(self.file_path, 'wb') as sink_file:
                # Write the new data to the file
                sink_file.write(data * 550)  # Repeat data 15 times for testing
                sink_file.flush()

            # Mark that new data is available for reading
            self.bytes_written = True
            self.file_position = 0  # Reset position to start reading from the beginning
            #print("New data written to file.")
        except Exception as e:
            print(f"Error writing to file: {e}")

    def general_work(self, input_items, output_items):
        # If no data has been written yet, output nothing
        if not self.bytes_written:
            time.sleep(self.check_interval)  # Pause for a while if no new data
            return 0

        # Read bytes from the file in chunks and send them to the output
        output_len = len(output_items[0])

        # Open the file if not already opened
        if self.source_file is None:
            try:
                self.source_file = open(self.file_path, 'rb')
            except Exception as e:
                print(f"Error opening file for reading: {e}")
                return 0

        try:
            # Seek to the current file position
            self.source_file.seek(self.file_position)

            # Try to read `output_len` bytes from the source file
            data = self.source_file.read(output_len)
            #print(data)
            print("true" if data else "false")
            
            if(data):
                self.stream_data = data

            if not data:
                # If EOF is reached, close the file and stop reading until new data is written
                self.source_file.close()
                self.source_file = None
                self.bytes_written = False
                #print("End of file reached, waiting for new data.")
                #return 0  # No items produced
           
                
            if(self.stream_data!=None):
                print(self.stream_data)

                # Convert data to numpy uint8 format for output
                output_items[0][:len(self.stream_data)] = np.frombuffer(self.stream_data, dtype=np.uint8)

                # Update file position
                self.file_position += len(self.stream_data)

                # Produce the number of output items generated
                self.consume_each(0)  # We are not consuming from any input
                return len(self.stream_data)
            else:
                return 0
                
        except Exception as e:
            print(f"Error reading file: {e}")
            return 0

    def stop(self):
        # Close the source file when the flowgraph stops
        if self.source_file:
            self.source_file.close()
        return True
