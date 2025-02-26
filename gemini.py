from google import genai
from google.genai import types
import io
import base64
import requests
import json


# Function to encode image to base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Function to call Gemini API using HTTP requests
def call_gemini_api_http(image, api_config):
    # Convert image to base64
    try:
        # Convert image to base64
        image_base64 = image_to_base64(image)
    except Exception as e:
        formatted_text = (f"Error preparing image: {e}")
        return formatted_text

    # Prompt for Gemini: OCR + Translation + Formatting
    model = api_config["API"]["MODEL"]
    key = api_config["API"]["KEY"]
    endpoint = api_config["API"]["ENDPOINT"]
    prompt = api_config["API"]["PROMPT"]

    # API request payload (adjust based on actual Gemini API spec)
    # Request headers
    headers = {
        "Content-Type": "application/json",
    }

    # Request body (example prompt)
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            },
            {
                "inline_data": {
                    "mime_type": "image/jpeg",  # Or "image/png", etc.
                    "data": image_base64
                }
            }
            ]
        }]
    }

    # Add API key to the request parameters
    params = {"key": key}

    try:
        response = requests.post(endpoint, headers=headers, params=params, json=data)
        response.raise_for_status()
        
        # Parse the JSON response
        json_response = response.json()
        #print(json.dumps(json_response, indent=2)) # Pretty print the JSON

        formatted_text = ""
        # Extract and print the generated text (if availabl)e
        if 'candidates' in json_response and json_response['candidates']:
            formatted_text = json_response['candidates'][0]['content']['parts'][0]['text']
            #print("\nGenerated Text:")
            #print(formatted_text)
            
        return formatted_text
    except requests.exceptions.HTTPError as e:
        formatted_text = (f"HTTP Error: {e}")
        formatted_text += (f"Response content: {e.response.text}") # Print error details from the API
        return formatted_text
    except requests.exceptions.RequestException as e:
        formatted_text = (f"Request Error: {e}")
        return formatted_text
    except json.JSONDecodeError:
        formatted_text = ("JSON Decode Error: Could not parse the JSON response from the API.")
        formatted_text += (f"Response text: {response.text}") # Print raw response if JSON parsing fails
        return formatted_text


# Function to call Gemini API using the Google API Client
def call_gemini_api_client(image, api_config):
    model = api_config["API"]["MODEL"]
    key = api_config["API"]["KEY"]
    endpoint = api_config["API"]["ENDPOINT"]
    prompt = api_config["API"]["PROMPT"]

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model, 
            contents=[prompt, image]
        )
        formatted_text = response.text
        return formatted_text
    except Exception as e:
        formatted_text = (f"Request Error: {e}")
        return formatted_text



# callback function (used for streaming)
# callback(chunk, over)
def call_gemini_api_stream(image, api_config, callback):
    model = api_config["API"]["MODEL"]
    key = api_config["API"]["KEY"]
    endpoint = api_config["API"]["ENDPOINT"]
    prompt = api_config["API"]["PROMPT"]

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content_stream(
            model=model, 
            contents=[prompt, image]
        )
        for chunk in response:
            callback(chunk.text, end=False)
        callback("", end=True)
        return ""
    except Exception as e:
        callback(f"Request Error: {e}", end=True)
        return ""
    