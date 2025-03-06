import gemini
import openchat
import speech
import threading

class TextStreamMemory:
    def __init__(self):
        """Initialize with empty text storage."""
        self.text = ""
    
    def append(self, new_text):
        """Append new text to the stream."""
        self.text += new_text
        return self.text  # Returns current state for convenience
    
    def clear(self):
        """Clear all stored text."""
        self.text = ""
        
    def get_text(self):
        """Return the current complete text."""
        return self.text

streamed_text = TextStreamMemory()

# Function to call API for OCR and translation
def call_real_api(image, api_config, callback=None):
    # Check if the API is compatible with OpenAI
    openai_compatible = api_config["API"]["OPENAI_COMPATIBLE"]
    # No value then not compatible
    if not openai_compatible:
        # Gemini API
        return gemini.call_gemini_api_stream(image, api_config, callback) if callback else gemini.call_gemini_api_client(image, api_config)
    
    # Check if the API is compatible with OpenAI
    openai_compatible = openai_compatible.lower()
    compatible_result = True if openai_compatible == "true" or openai_compatible == "yes" else False
    if compatible_result:
        # OpenAI API
        return openchat.call_openai_api_stream(image, api_config, callback) if callback else openchat.call_openai_api_client(image, api_config)
    else:
        # Gemini API
        return gemini.call_gemini_api_stream(image, api_config, callback) if callback else gemini.call_gemini_api_client(image, api_config)


"""
Initiates a speech synthesis process in a separate thread if streaming is enabled.

This function checks the configuration to determine if speech streaming is enabled.
If enabled, it starts a daemon thread to handle the speech synthesis using the
provided text. The thread runs the `call_sambert_client` function from the `speech`
module. If streaming is not enabled, the function returns None.

Args:
    text (str): The text to be synthesized into speech.

Returns:
    threading.Thread or None: The thread handling the speech synthesis if streaming
    is enabled, otherwise None.
"""
def call_speech(text, api_config):
    # Set the global variable to the API configuration
    speech._app_config = api_config
    # Check whether streaming speech
    speech_stream = speech._app_config["SPEECH"]["STREAM"]
    if not speech_stream:
        return None
    
    speech_stream = speech_stream.lower()
    speech_result = True if speech_stream == "true" or speech_stream == "yes" else False
    if speech_result:
        speech_type = api_config["SPEECH"]["TYPE"]
        # daemon thread for speeching
        if speech_type == "kokoro-online":
            thread = threading.Thread(target=speech.call_kokoro_online, args=(text, api_config), daemon=True)
        elif speech_type == "sambert":
            thread = threading.Thread(target=speech.call_sambert_client, args=(text, api_config), daemon=True)
        elif speech_type == "kokoro-offline":
            thread = threading.Thread(target=speech.call_kokoro_offline, args=(text, api_config), daemon=True)
        else:
            return None
        thread.start()
        return thread
    
    return None
        

# use for testing
_all_text = ""
_all_cfg = None
# use for testing stream
def stream_call(text, end=False):
    global _all_text
    global _all_cfg

    _all_text += text
    if not end:
        print(text, end="")
    else:
        print(text+"\nOver", end="\r")
        thread = call_speech(_all_text, _all_cfg)
        if thread:
            thread.join()

# Use for testing
if __name__ == "__main__":
    
    # Replace with your actual image
    from PIL import Image
    import os
    import config
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Change the working directory to the script's directory
        os.chdir(script_dir)

        image = Image.open("screenshot.png")
        # Now you can work with the image object
        print(f"Image size: {image.size}")
        print(f"Image mode: {image.mode}")
    except FileNotFoundError:
        print("Image file not found")
    except Exception as e:
        print(f"An error occurred: {e}")

    # test
    _all_cfg = config.read_config('api.json5')
    result = call_real_api(image, _all_cfg, stream_call)
    print(result)
