# import uhd
# import numpy as np
# import time

# # Configuration
# class Config:
#     sample_rate = 1e6  # Sample rate in Hz
#     gain = 30  # Gain value in dB
#     duration = 0.2  # Duration of each transmission burst in seconds
#     frequency = 2.4e9  # Transmission frequency in Hz

# config = Config()

# # Create a USRP object
# b210 = uhd.usrp.MultiUSRP("type=b200")

# # Set sample rate, frequency, and gain
# b210.set_tx_rate(config.sample_rate)
# b210.set_tx_freq(uhd.libpyuhd.types.tune_request(config.frequency))
# b210.set_tx_gain(config.gain)

# # Configure stream arguments
# st_args = uhd.usrp.StreamArgs("fc32", "sc16")
# st_args.channels = [0]

# # Get TX streamer
# tx_streamer = b210.get_tx_stream(st_args)
# tx_metadata = uhd.types.TXMetadata()

# # Prepare the data buffer with incrementing numbers
# sample_count = int(config.sample_rate * config.duration)
# incrementing_numbers = np.arange(sample_count, dtype=np.float32)
# tx_buffer = incrementing_numbers + 1j * 0  # Complex signal

# # Continuously send data
# print("Starting to transmit data...")
# try:
#     while True:
#         tx_metadata.start_of_burst = True
#         tx_metadata.end_of_burst = False
#         tx_streamer.send(tx_buffer, tx_metadata)
#         tx_metadata.start_of_burst = False
#         print("Transmitted data:", incrementing_numbers)
#         time.sleep(config.duration)
# except KeyboardInterrupt:
#     print("Transmission interrupted by user.")

# # Send end of burst
# tx_metadata.end_of_burst = True
# tx_streamer.send(tx_buffer, tx_metadata)
# print("Transmission complete.")










import uhd
import numpy as np
import time

def send_text_message(usrp, message, rate):
    # Prepare transmit buffer
    tx_buffer = np.frombuffer(message.encode('utf-8'), dtype=np.uint8)
    num_channels = usrp.get_tx_num_channels()

    # Create TX metadata
    metadata = uhd.types.TXMetadata()

    # Setup TX stream
    stream_args = uhd.usrp.StreamArgs("sc16", "sc16")
    tx_streamer = usrp.get_tx_stream(stream_args)

    # Send message
    num_sent = tx_streamer.send(tx_buffer, metadata, timeout=1.0)
    print(f"Number of samples sent: {num_sent}")

def main():
    # Setup USRP
    usrp = uhd.usrp.MultiUSRP("")

    # Define message and rate
    message = "Hello, USRP! "
    rate = 1e6  # Define appropriate transmit rate

    usrp.set_tx_rate(rate)
    count=0
    while True:
        count=count+1
        send_text_message(usrp, message+str(count), rate)

if __name__ == "__main__":
    main()
