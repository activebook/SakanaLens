import io
from openai import OpenAI
import base64

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def call_openai_api_client(image, api_config):
    # Convert image to base64
    try:
        # Convert image to base64
        image_base64 = image_to_base64(image)
        image_url = "data:image/png;base64," + image_base64
    except Exception as e:
        formatted_text = (f"Error preparing image: {e}")
        return formatted_text

    # Prompt for: OCR + Translation + Formatting
    model = api_config["API"]["MODEL"]
    key = api_config["API"]["KEY"]
    endpoint = api_config["API"]["ENDPOINT"]
    prompt = api_config["API"]["PROMPT"]

    # Invoke the OpenAI compatible API
    try:
        client = OpenAI(base_url=endpoint, api_key=key)
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        )

        formatted_text = (response.choices[0].message.content)
        return formatted_text
    except Exception as e:
        formatted_text = (f"Request Error: {e}")
        return formatted_text


def call_openai_api_stream(image, api_config, callback):
    # Convert image to base64
    try:
        image_base64 = image_to_base64(image)
        image_url = "data:image/png;base64," + image_base64
    except Exception as e:
        callback(f"Error preparing image: {e}", end=True)
        return ""

    # Extract configuration
    model = api_config["API"]["MODEL"]
    key = api_config["API"]["KEY"]
    endpoint = api_config["API"]["ENDPOINT"]
    prompt = api_config["API"]["PROMPT"]

    try:
        # Initialize the client
        client = OpenAI(base_url=endpoint, api_key=key)

        # Call the API in streaming mode by adding stream=True
        response_stream = client.chat.completions.create(
            model=model,
            temperature=0,
            stream=True,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        )

        # Accumulate the streamed output
        for chunk in response_stream:
            # Check if the chunk contains content in the delta field
            delta = chunk.choices[0].delta
            chunk_text = delta.content
            callback(chunk_text, end=False)
        callback("", end=True)
        return ""
    
    except Exception as e:
        callback(f"Request Error: {e}", end=True)
        return ""
