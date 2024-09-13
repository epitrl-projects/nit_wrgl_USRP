from gtts import gTTS
from pydub import AudioSegment

def text_to_wav(text, filename="output.wav"):
    # Convert the text to speech using gTTS
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")  # Save as mp3 temporarily

    # Convert mp3 to wav
    sound = AudioSegment.from_mp3("temp.mp3")
    sound.export(filename, format="wav")
    print(f"Audio saved as {filename}")

# Example usage
text_message = "Hello, this is a sample text message converted to a WAV audio file."
text_to_wav(text_message, "output.wav")
