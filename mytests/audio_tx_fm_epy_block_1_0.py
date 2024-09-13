"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt
import os
import numpy as np
from gtts import gTTS
from pydub import AudioSegment

class text_to_wav_block(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self, sample_rate=48000):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='text_to_wav_block',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )
        self.sample_rate=sample_rate
        self.text="no input"
        self.filename = "output.wav"
        self.message_port_register_in(pmt.intern("MSG_IN"))
        self.set_msg_handler(pmt.intern("MSG_IN"), self.set_text)


        
    def set_text(self, msg):
            """
            Sets the text to be converted to WAV.
            """
            # data = pmt.to_python(pmt.cdr(msg))
            self.text = str(msg)
            print(msg)
            self.convert_to_wav()
    def convert_to_wav(self):
        """
        Converts the stored text to a WAV file and loads the WAV data for output.
        """
        if self.text and len(self.text):
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
        """example: multiply with constant"""
        output_items[0][:] = input_items[0] * self.example_param
        return len(output_items[0])
