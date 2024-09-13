from gnuradio import gr
from pymavlink import mavutil
import numpy
import pmt
import threading
import time

class pymavlink_source_sink_pp(gr.basic_block):
    def __init__(self, connection_string='udp:localhost:14550', baud_rate=57600):
        gr.basic_block.__init__(self,
            name="pymavlink_source_sink_pp",
            in_sig=[],
            out_sig=[])

        self.connection_string = connection_string
        self.baud_rate = baud_rate
        self.sendbuffer=None

        # Register message ports
        self.message_port_register_in(pmt.intern("MAVLink_IN"))
        self.message_port_register_out(pmt.intern("MAVLink_OUT"))
        self.set_msg_handler(pmt.intern("MAVLink_IN"), self.mavlink_handler)

        # Setup MAVLink connection
        self.mavlink_connection = mavutil.mavlink_connection(connection_string, baud=baud_rate)
        
        # Thread for checking for messages
        self.running = True
        self.thread = threading.Thread(target=self.check_for_message)
        self.thread.daemon = True
        self.thread.start()
       
    def mavlink_handler(self, msg):
        data = pmt.to_python(pmt.cdr(msg))
        binarrymavlink = bytearray(data)
        mavmessage = self.mavlink_connection.mav.decode(binarrymavlink)
        print("from gcs",mavmessage)
        self.mavlink_connection.write(binarrymavlink)

    def check_for_message(self):
        self.mavlink_connection.mav.param_request_list_send(
                self.mavlink_connection.target_system,
                self.mavlink_connection.target_component
            )
        while self.running:
            
            self.message = self.mavlink_connection.recv_match(blocking=True, timeout=10)
            self.sendbuffer = self.message
            if self.message is not None:
                if self.message.get_type() == 'BAD_DATA':
                    continue
                
                    
                buf = self.message.get_msgbuf()
                bufnp = numpy.frombuffer(buf, dtype=numpy.uint8)
                #print("to gcs",self.message)
                
                self.message_port_pub(pmt.intern("MAVLink_OUT"), pmt.cons(pmt.PMT_NIL, pmt.to_pmt(bufnp)))

    def __del__(self):
        self.running = False
        self.mavlink_connection.close()
        if self.thread.is_alive():
            self.thread.join()

    def work(self, input_items, output_items):
        # Not used in this block, but required for the basic_block
        return len(input_items[0])
