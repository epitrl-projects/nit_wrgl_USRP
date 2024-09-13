
import numpy as np
from gnuradio import gr
import os
from pydub import AudioSegment

class myblock(gr.sync_block):
    """
    Custom block to stream an MP3 file from a folder based on a selection value (weight).
    """
    def __init__(self, folder_path="/home/pi/Desktop/project/assets"):
        # Initialize the block with no inputs and one output
        gr.sync_block.__init__(self,
            name="myblock",
            in_sig=None,
            out_sig=[np.float32])

        self.folder_path = folder_path
        self.weight = -1
        self.previous_weight = -1  # Store the previous weight to detect changes
        self.audio_position = 0
        self.selected_audio = None
        self.previouscheckweight = 0
        
        # Load and validate MP3 files in the directory
        self.mp3_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.mp3')])
        if not self.mp3_files:
            raise ValueError("No MP3 files found in the specified folder.")
        if(self.weight!=-1):
            # Load the initial MP3 file based on the weight index
            self.load_mp3_by_weight()
        # Register an input message port
        self.message_port_register_in(gr.pmt.intern("weight_msg"))
        self.set_msg_handler(gr.pmt.intern("weight_msg"), self.handle_msg)

    def load_mp3_by_weight(self):
        """ Load the MP3 file corresponding to the current weight index """
        if self.weight >= 0 and self.weight < len(self.mp3_files):
            filename = self.mp3_files[self.weight]
            self.load_mp3(filename)
        else:
            raise ValueError("Invalid weight index: out of range for available MP3 files.")

    def handle_msg(self, msg):
            """ Handle incoming messages to update the weight """
            # Convert the message to an integer (assumes the message is a string or integer PMT)
            new_weight = int(gr.pmt.to_python(msg))
            print(f"Received new weight: {new_weight}")
            if(self.previouscheckweight!=new_weight):
                self.weight = new_weight
                self.check_and_update_weight()
        
    def load_mp3(self, filename):
        """ Load the selected MP3 file as raw PCM audio data """
        audio_path = os.path.join(self.folder_path, filename)
        audio = AudioSegment.from_mp3(audio_path)
        
        # Convert to raw PCM 32-bit float data
        samples = np.array(audio.get_array_of_samples())
        
        # If the audio is stereo, flatten the samples
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)
        
        # Normalize to the range [-1, 1]
        self.selected_audio = samples.astype(np.float32) / np.iinfo(audio.array_type).max
        
        # Reset audio position
        self.audio_position = 0
        print(f"Loaded MP3 file: {filename}, Total samples: {len(self.selected_audio)}")

    def check_and_update_weight(self):
        """ Check if the weight has changed, and update the MP3 file if it has """
        if self.weight != self.previous_weight:
            print(f"Weight changed from {self.previous_weight} to {self.weight}")
            self.previous_weight = self.weight
            self.load_mp3_by_weight()
            self.reset_audio_stream()

    def reset_audio_stream(self):
        """ Clear the output buffer to start streaming the new audio immediately """
        self.audio_position = 0  # Reset position to the beginning of the new audio

    def work(self, input_items, output_items):
        # Check if the weight has changed and update if necessary
        self.check_and_update_weight()

        # Determine how many samples we need to output
        num_samples = len(output_items[0])

        if self.selected_audio is None:
            output_items[0][:] = np.zeros(num_samples)
            return num_samples

        # Output the selected portion of the audio file
        start = self.audio_position
        end = start + num_samples

        if end <= len(self.selected_audio):
            output_items[0][:] = self.selected_audio[start:end]
            self.audio_position = end
        else:
            # If we've reached the end of the audio, pad with zeros
            valid_samples = len(self.selected_audio) - start
            output_items[0][:valid_samples] = self.selected_audio[start:]
            output_items[0][valid_samples:] = 0
            self.audio_position = len(self.selected_audio)  # Stop streaming
            print("Reached the end of the audio stream")

        return num_samples

# Example usage:
# block = myblock(folder_path="/path/to/mp3/folder", weight=2)
# block.weight = 1  # Changing the weight during runtime
