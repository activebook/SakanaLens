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
#
# For kokoro offline:
#   pip install -U kokoro-onnx sounddevice
# Download the model files:
#   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
#   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
#
#

import config
import language

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
    import dashscope
    import pyaudio
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


"""
Sends a request to the Kokoro online service to synthesize speech from text.

This function uses the provided API configuration to set up the request
parameters, including the speech model, API key, endpoint, language, and
rate. It filters the input text based on the specified language and sends
a POST request to the service. The synthesized audio is then played back
automatically.

Args:
    text (str): The text to be synthesized into speech.
    api_config (dict): Configuration dictionary containing API details such
                       as model, key, endpoint, language, and rate.

Returns:
    None
"""
def call_kokoro_online(text, api_config):
    import io
    import requests
    from pydub import AudioSegment
    from pydub.playback import play    

    model = api_config["SPEECH"]["MODEL"]
    key = api_config["SPEECH"]["KEY"]
    endpoint = api_config["SPEECH"]["ENDPOINT"]
    lang = api_config["SPEECH"]["LANG"]
    rate = float(api_config["SPEECH"]["RATE"]) - 1 # Increament range(-1.0 to 1.0)

    # Filtering the text based on the specified language
    if text is None or len(text) == 0:
        return
    text = language.filter_target_lang(text, lang)

    response = requests.post(
        endpoint,
        headers = {
            'Authorization' : f"Bearer {key}"
        },
        json = {
            'Text': text, # max 1000 chars
            'VoiceId': model,
            'Bitrate': '48k', # 320k, 256k, 192k, ...
            'Speed': rate, # -1.0 to 1.0
            'Pitch': '1', # 0.5 to 1.5
            'Codec': 'libmp3lame', # libmp3lame or pcm_mulaw
        }
    )

    try:
        # Load audio directly into memory
        audio_data = io.BytesIO(response.content)
        audio_data.seek(0)  # Reset the file pointer to the beginning

        # Create AudioSegment object from memory - use from_mp3 instead of from_file
        audio = AudioSegment.from_mp3(audio_data)

        # Auto-play the audio
        play(audio)
    except Exception as e:
        return

'''
kokoro-offline:
Features:
Supports multiple languages
Fast performance near real-time on macOS M1
Offer multiple voices
Lightweight: ~300MB (quantized: ~80MB)
'''
def call_kokoro_offline(text, api_config):
    import sounddevice as sd
    from kokoro_onnx import Kokoro

    model = api_config["SPEECH"]["MODEL"]
    lang = api_config["SPEECH"]["LANG"]
    rate = float(api_config["SPEECH"]["RATE"]) # Increament range(0.5 to 2.0)

    # Filtering the text based on the specified language
    if text is None or len(text) == 0:
        return
    text = language.filter_target_lang(text, lang)
    print(text)

    try:
        model_path = config.get_resource_path("kokoro/kokoro-v1.0.int8.onnx")
        voice_path = config.get_resource_path("kokoro/voices-v1.0.bin")
        kokoro = Kokoro(model_path, voice_path)
        samples, sample_rate = kokoro.create(
            text=text, voice=model, speed=rate, lang=lang
        )
        sd.play(samples, sample_rate)
        sd.wait()
    except Exception as e:
        print(e)
        return

# Testing
if __name__ == "__main__":
    # Call the Sambert client with the specified text and API configuration
    
    _all_cfg = config.read_config('api.json5')
    speech_type = _all_cfg["SPEECH"]["TYPE"]
    text = """
        IGs are the watchdogs of the federal government, providing fair, objective and independent oversight inside federal agencies. 
    """
    if speech_type == "kokoro-online":
        call_kokoro_online(
            text,
            _all_cfg
        )    
    elif speech_type == "sambert":
        call_sambert_client(
            text,
            _all_cfg
        )
    else:
        call_kokoro_offline(
            text,
            _all_cfg
        )
    
    