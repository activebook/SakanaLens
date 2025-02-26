import gemini
import openchat

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
    
# use for testing stream
def stream_call(text, end=False):
    print(text, end="") if not end else print(text+"\nOver", end="\r")

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
    cfg = config.read_config('api.json5')
    result = call_real_api(image, cfg, stream_call)
    print(result)
