# import time
# import uhd
# import numpy as np
# from pymavlink import mavutil

# # Initialize USRP
# usrp = uhd.usrp.MultiUSRP()

# # Create a MAVLink connection
# mavlink_connection = mavutil.mavlink_connection('udpout:localhost:14550')

# # Create a MAVLink message (e.g., HEARTBEAT)
# csmode=0
# while True:
#     if(csmode==0):
#         csmode=1
#     else:
#         csmode=0

#     heartbeat_msg = mavlink_connection.mav.heartbeat_encode(
#         type=mavutil.mavlink.MAV_TYPE_QUADROTOR,
#         autopilot=mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
#         base_mode=0,
#         custom_mode=csmode,
#         system_status=0
#     )

#     # Convert MAVLink message to bytes
#     mavlink_bytes = heartbeat_msg.pack(mavlink_connection.mav)

#     # Repeat the MAVLink message to match the number of samples
#     samples = np.tile(np.frombuffer(mavlink_bytes, dtype=np.uint8), 10000 // len(mavlink_bytes))

#     # Parameters
#     print(len(samples))
#     duration = 10  # seconds
#     center_freq = 100e6
#     sample_rate = 1e6
#     gain = 50  # [dB] start low then work your way up

#     # Send the MAVLink message as waveform
#     usrp.send_waveform(samples, duration, center_freq, sample_rate, [0], gain)
#     time.sleep(2)







import time
import numpy as np
from pymavlink import mavutil
import uhd
# Initialize MAVLink connection
master = mavutil.mavlink_connection('udpout:localhost:14550')

# Create USRP object
usrp = uhd.usrp.MultiUSRP()
count=0

def create_heartbeat_message():
    return master.mav.heartbeat_encode(
        mavutil.mavlink.MAV_TYPE_GENERIC,
        mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
        0, 0, 0, 3
    )

def send_mavlink_message(usrp, message, freq=2.4e9, rate=1e6, gain=10):
    # Convert MAVLink message to byte array
    message_bytes = message.pack(master.mav)
    print(f"Message bytes: {message_bytes}")

    # Convert byte array to numpy array
    message_array = np.frombuffer(message_bytes, dtype=np.uint8)
    print(f"Message array: {message_array}")

    if len(message_array) == 0:
        print("Error: Empty message array. Exiting transmission.")
        return

    # Convert uint8 array to complex samples
    samples = np.zeros((len(message_array),), dtype=np.complex64)
    samples.real = message_array.astype(np.float32)  # Real part as the byte values
    samples.imag = 0  # Imaginary part as 0 (assuming no modulation here)
    print(f"Samples: {samples}")

    # Calculate duration
    duration = len(samples) / rate
    print(f"Duration: {duration}, Rate: {rate}, Freq: {freq}, Gain: {gain}")

    # Transmit the samples
    usrp.send_waveform(samples, duration=duration, freq=freq, rate=rate, gain=gain)

def main():
    # Create a MAVLink message
    msg = create_heartbeat_message()
    print(f"MAVLink message: {msg}")

    send_mavlink_message(usrp, msg)
    print("MAVLink message sent.")


if __name__ == "__main__":
    while True:

        main()
        time.sleep(2)
