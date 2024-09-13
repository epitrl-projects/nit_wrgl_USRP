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
        self.count = 0
        self.bytecount=0
        self.stategotheartbeat=False

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
        
    def sendheartbeatandparam(self):
            for i in range(0,100):
                self.mavlink_connection.mav.param_request_list_send(self.mavlink_connection.target_system,self.mavlink_connection.target_component)
        
    def mavlink_handler(self, msg):
        data = pmt.to_python(pmt.cdr(msg))
        binarrymavlink = bytearray(data)
        mavmessage = self.mavlink_connection.mav.decode(binarrymavlink)
        print("from gcs",mavmessage)
        self.stategotheartbeat=True
        if((mavmessage.get_type() == 'HEARTBEAT' or mavmessage.get_type() == 'PARAM_REQUEST_READ') and self.count>=100):
            # self.mavlink_connection.mav.heartbeat_send(
            #                 type=mavutil.mavlink.MAV_TYPE_GCS,
            #                 autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            #                 base_mode=0,
            #                 custom_mode=0,
            #                 system_status=mavutil.mavlink.MAV_STATE_ACTIVE
            #             )
                        # Request all parameters
            self.mavlink_connection.mav.param_request_list_send(
                    self.mavlink_connection.target_system,
                    self.mavlink_connection.target_component
                )
            self.count = 0
        self.count +1
        #       sendthread = threading.Thread(target=self.sendheartbeatandparam)
         #       sendthread.start()
         #       self.count=1
                
        self.mavlink_connection.write(binarrymavlink)

    def check_for_message(self):
        while self.running:
           
            self.message = self.mavlink_connection.recv_match(blocking=False, timeout=10)
            self.count+=1
            #self.sendbuffer = self.message
            if self.message is not None:
                if self.message.get_type() == 'BAD_DATA':
                    continue
                
                buf = self.message.get_msgbuf()
                bufnp = numpy.frombuffer(buf, dtype=numpy.uint8)
                if(self.stategotheartbeat):
                    self.bytecount+=1
                    
                    byte_data = str(self.bytecount).encode('utf-8')  # or use another encoding if needed

                    # Create a NumPy array from the byte data
                    buffer_array = numpy.frombuffer(byte_data, dtype=numpy.uint8)
                    self.message_port_pub(pmt.intern("MAVLink_OUT"), pmt.cons(pmt.PMT_NIL, pmt.to_pmt(buffer_array)))
                    # self.stategotheartbeat=False
                self.message_port_pub(pmt.intern("MAVLink_OUT"), pmt.cons(pmt.PMT_NIL, pmt.to_pmt(bufnp)))

    def __del__(self):
        self.running = False
        self.mavlink_connection.close()
        if self.thread.is_alive():
            self.thread.join()

    def work(self, input_items, output_items):
        # Not used in this block, but required for the basic_block
        return len(input_items[0])
