import json5
import sys
import os
    
def get_resource_path(relative_path, external=False):
    """
    Get absolute path to resources, works for dev and for py2app bundles
    
    Args:
        relative_path: Path relative to either the bundle resources or the external directory
        external: If True, look for the file outside the app bundle at the same level as the .app
                 If False, look inside the bundle resources (default behavior)
    """
    if getattr(sys, 'frozen', False):  # Running as compiled app
        if external:
            # Get directory containing the .app bundle
            # sys.executable points to YourApp.app/Contents/MacOS/YourApp
            app_bundle = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            base_dir = os.path.dirname(app_bundle)  # Parent directory of the .app
            return os.path.join(base_dir, relative_path)
        else:
            # For resources inside the bundle
            if hasattr(sys, '_MEIPASS'):  # PyInstaller
                base_dir = sys._MEIPASS
            else:  # py2app
                base_dir = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Resources')
            return os.path.join(base_dir, relative_path)
    else:  # Running in development
        # Assume the resource is relative to the script directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, relative_path)

def read_config(filename):
    try:
        # Look for api.json5 in the same directory as the .app
        config_path = get_resource_path(filename, external=True)

        # for debug only
        #print(f"Looking for file at: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json5.load(f)            
            return config
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found in the script's directory.")
        return None
    except Exception as e:
        print(f"Error: {e} in '{filename}'.")
        return None


if __name__ == "__main__":
    cfg = read_config('api.json5')
    print(cfg["API"]["PROMPT"])  # Prints the entire JSON object
