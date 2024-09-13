import numpy as np
from gnuradio import gr
import pmt
import os
from gtts import gTTS
from pydub import AudioSegment

class text_to_wav_block(gr.sync_block):  
    """Embedded Python Block example - converts text to WAV and outputs float32 data"""

    def __init__(self, sample_rate=48000):  
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='text_to_wav_block',   # will show up in GRC
            in_sig=[],
            out_sig=[np.float32]  # Output signal as float32
        )
        self.sample_rate = sample_rate
        self.text = "no input"
        self.filename = "output.wav"
        self.wav_data = np.array([], dtype=np.float32)  # Initialize an empty array for WAV data
        self.message_port_register_in(pmt.intern("MSG_IN"))
        self.set_msg_handler(pmt.intern("MSG_IN"), self.set_text)

    def set_text(self, msg):
        """
        Sets the text to be converted to WAV.
        """
        self.text = str(msg)
        print(msg)
        self.convert_to_wav()

    def convert_to_wav(self):
        """
        Converts the stored text to a WAV file and loads the WAV data for output.
        """
        if self.text:
            tts = gTTS(text=self.text, lang='en')
            tts.save("temp.mp3")  # Save as mp3 temporarily

            # Convert mp3 to wav
            sound = AudioSegment.from_mp3("temp.mp3")
            sound = sound.set_frame_rate(self.sample_rate)  # Ensure correct sample rate
            sound.export(self.filename, format="wav")
            print(f"Audio saved as {self.filename}")
            
            # Load the WAV data into memory as a numpy array
            self.wav_data = np.array(sound.get_array_of_samples(), dtype=np.float32)
            
            # Normalize the data to the range [-1, 1]
            self.wav_data /= np.iinfo(np.int16).max
            
            # Clean up the temporary mp3 file
            os.remove("temp.mp3")
        else:
            print("No text provided for conversion.")

    def work(self, input_items, output_items):
        """Output the float32 WAV data"""
        output_length = len(output_items[0])
        data_length = len(self.wav_data)
        
        # Ensure we don't exceed the length of the WAV data
        if data_length > 0:
            output_items[0][:min(output_length, data_length)] = self.wav_data[:min(output_length, data_length)]
            self.wav_data = self.wav_data[min(output_length, data_length):]  # Update remaining data
        else:
            output_items[0][:] = 0  # No data to output

        return len(output_items[0])
