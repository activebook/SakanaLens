# coding=utf-8
#
# Installation instructions for pyaudio:
# APPLE Mac OS X
#   brew install portaudio 
#   pip install pyaudio
# Debian/Ubuntu
#   sudo apt-get install python-pyaudio python3-pyaudio
#   or
#   pip install pyaudio
# CentOS
#   sudo yum install -y portaudio portaudio-devel && pip install pyaudio
# Microsoft Windows
#   python -m pip install pyaudio

import dashscope
import pyaudio
import language
from dashscope.api_entities.dashscope_response import SpeechSynthesisResponse
from dashscope.audio.tts import ResultCallback, SpeechSynthesizer, SpeechSynthesisResult


"""
Handles the playback of synthesized speech using the PyAudio library.

This class extends the ResultCallback to manage audio playback events
triggered by the speech synthesizer. It initializes audio playback on
opening, writes audio frames to the stream during events, and cleans up
resources on closure. Error handling is also provided for synthesis
failures.

Attributes:
    _player: An instance of PyAudio for managing audio playback.
    _stream: A PyAudio stream for outputting audio data.

Methods:
    on_open(): Initializes the audio player and stream for playback.
    on_complete(): Placeholder for actions upon synthesis completion.
    on_error(response): Handles errors during speech synthesis.
    on_close(): Stops and closes the audio stream and player.
    on_event(result): Writes audio frames to the stream during synthesis events.
"""
class playback(ResultCallback):
    _player = None
    _stream = None

    def on_open(self):
        #print('Speech synthesizer is opened.')
        self._player = pyaudio.PyAudio()
        self._stream = self._player.open(
            format=pyaudio.paInt16,
            channels=1,     
            rate=48000,
            output=True)

    def on_complete(self):
        #print('Speech synthesizer is completed.')
        pass

    def on_error(self, response: SpeechSynthesisResponse):
        #print('Speech synthesizer failed, response is %s' % (str(response)))
        pass

    def on_close(self):
        #print('Speech synthesizer is closed.')
        self._stream.stop_stream()
        self._stream.close()
        self._player.terminate()

    def on_event(self, result: SpeechSynthesisResult):
        if result.get_audio_frame() is not None:
            #print('audio result length:', sys.getsizeof(result.get_audio_frame()))
            self._stream.write(result.get_audio_frame())

        '''
        if result.get_timestamp() is not None:
            print('timestamp result:', str(result.get_timestamp()))
        '''

"""
Calls the Sambert client to synthesize speech from text using the specified API configuration.

This function sets the API key for Dashscope, retrieves the speech model and key from the
provided configuration, and initiates the speech synthesis process. The synthesized speech
is streamed using a specified sample rate and format, with playback managed by a callback.

Args:
    text (str): The text to be converted into speech.
    api_config (dict): Configuration dictionary containing the speech model and API key.

Returns:
    SpeechSynthesisResult: The result of the speech synthesis process.
"""
def call_sambert_client(text, api_config):

    model = api_config["SPEECH"]["MODEL"]
    key = api_config["SPEECH"]["KEY"]
    lang = api_config["SPEECH"]["LANG"]
    rate = float(api_config["SPEECH"]["RATE"])

    # Filtering the text based on the specified language
    if text is None or len(text) == 0:
        return
    text = language.filter_target_lang(text, lang)

    # Streaming the synthesized speech
    dashscope.api_key = key
    result = SpeechSynthesizer.call(model=model,
                       text=text,
                       rate=rate,
                       sample_rate=48000,
                       format='pcm',
                       callback=playback()
                       )