
import argparse
from datetime import datetime, timedelta
import sys
import time
import threading
import logging
import numpy as np
import uhd


class LogFormatter(logging.Formatter):
    """Log formatter which prints the timestamp with fractional seconds"""
    @staticmethod
    def pp_now():
        """Returns a formatted string containing the time of day"""
        now = datetime.now()
        return "{:%H:%M}:{:05.2f}".format(now, now.second + now.microsecond / 1e6)
        # return "{:%H:%M:%S}".format(now)

    def formatTime(self, record, datefmt=None):
        converter = self.converter(record.created)
        if datefmt:
            formatted_date = converter.strftime(datefmt)
        else:
            formatted_date = LogFormatter.pp_now()
        return formatted_date


 # Setup a usrp device


CLOCK_TIMEOUT = 1000  # 1000mS timeout for external clock locking
INIT_DELAY = 0.05  # 50mS initial delay before transmit

global logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
logger.addHandler(console)
formatter = LogFormatter(fmt='[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s')
console.setFormatter(formatter)

usrp = uhd.usrp.MultiUSRP()
if usrp.get_mboard_name() == "USRP1":
    logger.warning(
        "Benchmark results will be inaccurate on USRP1 due to insufficient features.")

logger.info("Using Device: %s", usrp.get_pp_string())

def benchmark_rx_rate(usrp, rx_streamer, timer_elapsed_event, rx_statistics):
    """Benchmark the receive chain with text data"""
    logger.info("Testing receive rate %.3f Msps on %d channels",
                 usrp.get_rx_rate() / 1e6, rx_streamer.get_num_channels())

    num_channels = rx_streamer.get_num_channels()
    max_samps_per_packet = rx_streamer.get_max_num_samps()
    recv_buffer = np.empty((num_channels, max_samps_per_packet), dtype=np.complex64)
    metadata = uhd.types.RXMetadata()

    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = (num_channels == 1)
    stream_cmd.time_spec = uhd.types.TimeSpec(usrp.get_time_now().get_real_secs() + INIT_DELAY)
    rx_streamer.issue_stream_cmd(stream_cmd)

    received_bytes = bytearray()
    num_rx_samps = 0

    while not timer_elapsed_event.is_set():
        try:
            num_rx_samps_now = rx_streamer.recv(recv_buffer, metadata) * num_channels
            num_rx_samps += num_rx_samps_now

            # Convert received buffer to bytes
            received_bytes.extend(recv_buffer.view(np.uint8).tobytes())

        except RuntimeError as ex:
            logger.error("Runtime error in receive: %s", ex)
            return

    # Decode the bytes to text
    received_text = received_bytes.decode(errors='ignore')
    logger.info("Received data: %s", received_text)

    rx_statistics["num_rx_samps"] = num_rx_samps
    rx_streamer.issue_stream_cmd(uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont))

def benchmark_tx_rate(usrp, tx_streamer, text_data, timer_elapsed_event, tx_statistics):
    """Benchmark the transmit chain with continuous text data transmission"""
    logger.info("Testing transmit rate %.3f Msps on %d channels",
                 usrp.get_tx_rate() / 1e6, tx_streamer.get_num_channels())

    # Convert text data to bytes
    text_bytes = text_data.encode()
    num_channels = tx_streamer.get_num_channels()
    max_samps_per_packet = tx_streamer.get_max_num_samps()

    # Create a buffer for transmitting data
    transmit_buffer = np.zeros((num_channels, max_samps_per_packet), dtype=np.complex64)
    metadata = uhd.types.TXMetadata()
    metadata.time_spec = uhd.types.TimeSpec(usrp.get_time_now().get_real_secs() + INIT_DELAY)
    metadata.has_time_spec = bool(num_channels)

    num_tx_samps = 0
    num_samples = len(text_bytes)
    idx = 0

    while not timer_elapsed_event.is_set():
        # Check if we've reached the end of the text data and loop back if needed
        if idx >= num_samples:
            idx = 0

        # Prepare the chunk to send
        start_idx = idx
        end_idx = min(start_idx + max_samps_per_packet, num_samples)
        chunk = text_bytes[start_idx:end_idx]

        # Convert the chunk to np.complex64
        chunk_length = len(chunk)
        chunk_padded = chunk.ljust(max_samps_per_packet, b'\0')  # Pad to the buffer size
        chunk_array = np.frombuffer(chunk_padded, dtype=np.uint8)

        # Handle the conversion from uint8 to complex64
        if chunk_length % 8 == 0:  # Ensure the length is a multiple of 8 for complex64
            chunk_array = chunk_array.view(np.complex64).reshape((num_channels, -1))
        else:
            num_complex_samples = chunk_length // 8
            chunk_array = chunk_array[:num_complex_samples * 8].view(np.complex64).reshape((num_channels, -1))

        # Ensure the buffer is filled correctly
        transmit_buffer[:, :chunk_array.shape[1]] = chunk_array

        try:
            num_tx_samps_now = tx_streamer.send(transmit_buffer, metadata) * num_channels
            num_tx_samps += num_tx_samps_now
            # Move the index forward for the next chunk
            idx = end_idx
        except RuntimeError as ex:
            logger.error("Runtime error in transmit: %s", ex)
            return

    # Send a mini EOB packet after stopping
    metadata.end_of_burst = True
    tx_streamer.send(np.zeros((num_channels, 0), dtype=np.complex64), metadata)
    tx_statistics["num_tx_samps"] = num_tx_samps


def benchmark_tx_rate_async_helper(tx_streamer, timer_elapsed_event, tx_async_statistics):
    """Receive and process the asynchronous TX messages"""
    async_metadata = uhd.types.TXAsyncMetadata()

    # Setup the statistic counters
    num_tx_seqerr = 0
    num_tx_underrun = 0
    num_tx_timeouts = 0  # TODO: Not populated yet
    try:
        while not timer_elapsed_event.is_set():
            # Receive the async metadata
            if not tx_streamer.recv_async_msg(async_metadata, 0.1):
                continue

            # Handle the error codes
            if async_metadata.event_code == uhd.types.TXMetadataEventCode.burst_ack:
                return
            if async_metadata.event_code in (
                    uhd.types.TXMetadataEventCode.underflow,
                    uhd.types.TXMetadataEventCode.underflow_in_packet):
                num_tx_underrun += 1
            elif async_metadata.event_code in (
                    uhd.types.TXMetadataEventCode.seq_error,
                    uhd.types.TXMetadataEventCode.seq_error_in_packet):
                num_tx_seqerr += 1
            else:
                logger.warning("Unexpected event on async recv (%s), continuing.",
                               async_metadata.event_code)
    finally:
        # Write the statistics back
        tx_async_statistics["num_tx_seqerr"] = num_tx_seqerr
        tx_async_statistics["num_tx_underrun"] = num_tx_underrun
        tx_async_statistics["num_tx_timeouts"] = num_tx_timeouts



threads = []
# Make a signal for the threads to stop running
quit_event = threading.Event()
# Create a dictionary for the RX statistics
# Note: we're going to use this without locks, so don't access it from the main thread until
#       the worker has joined
rx_statistics = {}
tx_statistics = {}
tx_async_statistics = {}
# Spawn the receive test thread

usrp.set_rx_rate(2.4e6)
usrp.set_tx_rate(2.4e6)
usrp.set_rx_gain(20,0)
usrp.set_tx_gain(20,0)

usrp.set_rx_freq(50e6,0)
usrp.set_tx_freq(45e6,0)

st_args = uhd.usrp.StreamArgs("fc32", "sc16")

st_args.channels = [0]
st_args.args = uhd.types.DeviceAddr("")
rx_streamer = usrp.get_rx_stream(st_args)
tx_streamer = usrp.get_tx_stream(st_args)

rx_thread = threading.Thread(target=benchmark_rx_rate,
                                args=(usrp, rx_streamer, quit_event,
                                    rx_statistics))

tx_thread = threading.Thread(target=benchmark_tx_rate,
                                args=(usrp, tx_streamer, "USRP1", quit_event,
                                    tx_statistics))

tx_async_thread = threading.Thread(target=benchmark_tx_rate_async_helper,
                                    args=(tx_streamer, quit_event, tx_async_statistics))


threads.append(rx_thread)
rx_thread.start()
rx_thread.name = "bmark_rx_stream"


threads.append(tx_thread)
tx_thread.start()
tx_thread.name = "bmark_tx_stream"

threads.append(tx_async_thread)
tx_async_thread.start()
tx_async_thread.name = "bmark_tx_helper"