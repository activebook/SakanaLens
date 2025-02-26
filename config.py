import json5
import os

def read_config(filename):
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Change the working directory to the script's directory
        os.chdir(script_dir)

        with open(filename, 'r', encoding='utf-8') as f:
            config = json5.load(f)            
            return config
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found in the script's directory.")
        return None
    except json5.JSONDecodeError:
        print(f"Error: Invalid JSON in '{filename}'.")
        return None

    

if __name__ == "__main__":
    cfg = read_config('api.json5')
    print(cfg["API"]["PROMPT"])  # Prints the entire JSON object
