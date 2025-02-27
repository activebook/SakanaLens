import tkinter as tk
from tkinter import scrolledtext
from AppKit import NSApplication, NSWorkspace
from Cocoa import NSEvent, NSKeyDownMask
from PyObjCTools import AppHelper
from PIL import Image
import Quartz
import time
import threading
import asyncio
import Foundation
import queue
import objc
import subprocess
import os
import tempfile
import pygetwindow as gw
import pyautogui
import translate
import config


# this doesn't work on python3.13
'''
# Function to capture the active window screenshot
def capture_window():
    try:
        # Get the active window (assuming it's the game)
        active_window = gw.getActiveWindow()
        if not active_window:
            return None
        
        # Get window coordinates
        left, top, width, height = active_window.left, active_window.top, active_window.width, active_window.height
        
        # Capture screenshot of the window
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        return screenshot
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None
'''

# PyObjC approach: Python script to capture the active window screenshot
def capture_window(api_config):
    try:
        
        # Get front window info
        front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        front_app_name = front_app.localizedName()
        
        # Get windows from front app
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID)
            
        windows = [window for window in window_list if window['kCGWindowOwnerName'] == front_app_name]
        
        if not windows:
            return None
            
        # Get the topmost window
        window = windows[-1]
        bounds = window['kCGWindowBounds']
        # Convert coordinates to integers
        x = int(bounds['X'])
        y = int(bounds['Y'])
        width = int(bounds['Width'])
        height = int(bounds['Height'])
        
        # used for debugging
        # using macOS's built-in screenshot highlighting capability. 
        # We can use the screencapture command-line tool with its interactive mode to highlight the window temporarily
        '''
        # Use CoreGraphics to draw a temporary red border
        cg_context = Quartz.CGDisplayCreateImageForRect(
            Quartz.CGMainDisplayID(),
            Quartz.CGRectMake(x, y, width, height)
        )
        
        # Create a temporary file for the overlay
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "window_overlay.png")
        
        # Take a screenshot with the built-in highlight feature
        # This will briefly highlight the window
        subprocess.run([
            "screencapture",
            "-w",  # Window capture moed
            "-o",  # Don't include shadow
            temp_file
        ])
        
        print(f"Debug: Screenshot saved to {temp_file}")
        
        # Slight delay after highlight
        time.sleep(0.5)
        '''

        screenshot = pyautogui.screenshot(region=(x, y, width, height))   
        temp_file = api_config["DEBUG"]["SCREENSHOT"]
        if temp_file != "":
            # Print information for debugging
            print(f"Front app: {front_app_name}")
            print(f"Window detected: {front_app_name}")
            print(f"Position: X={x}, Y={y}, Width={width}, Height={height}")
            screenshot.save(temp_file)
        return screenshot
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None

# Simulated AI API function (replace with real API later)
def simulate_ai_api(image, api_config, stream_call=None):
    # Placeholder: Pretend this processes the image and returns Japanese + English text
    english_text = translate.call_real_api(image, api_config, stream_call)
    return english_text

# Function to process screenshot and update UI
def process_capture_window_text(api_config, stream_call=None):
    screenshot = capture_window(api_config)
    if screenshot:
        # Call Gemini API
        formatted_text = simulate_ai_api(screenshot, api_config, stream_call)
        return formatted_text
    else:
        return "Nothing to translate"


class KeyListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.monitor = None
        self.running = True
        
    def handle_event(self, event):
        # Get the key information
        key_char = event.characters()
        key_code = event.keyCode()
        modifiers = event.modifierFlags()
        
        # Check for Ctrl+T
        control_key_mask = (1 << 18)  # NSControlKeyMask
        if key_code == 17 and (modifiers & control_key_mask):            
            print("Ctrl+T was pressed!")
            self.event_queue.put("TaskEvent")
        else:
            #self.event_queue.put(f"Key: {key_char}, Code: {key_code}, Modifiers: {modifiers}")
            pass
    
    def start(self):
        # Set up a global monitor for key events
        mask = NSKeyDownMask
        self.monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            mask, self.handle_event
        )
    
    def stop(self):
        # Remove the monitor
        if self.monitor:
            NSEvent.removeMonitor_(self.monitor)
            self.monitor = None


class CocoaAppThread(threading.Thread):
    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.listener = listener
        self.daemon = True
        
    def run(self):
        # Create an autorelease pool
        pool = Foundation.NSAutoreleasePool.alloc().init()
        
        # Create and run the Cocoa application
        NSApplication.sharedApplication()
        self.listener.start()
        AppHelper.runEventLoop()
        
        # Release the pool
        del pool

APP_TITLE = "Sakana Lens 日本語の自動翻訳"
APP_TIPS = """Press [Ctrl+T] on any Text Window to trigger the automatic translation task"""

class TkinterApp:
    def __init__(self, root):
        # Read api.json
        self.api_config = config.read_config('api.json5')

        self.root = root
        root.title(APP_TITLE)

        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Set window size and position
        window_width = int(self.api_config['WIN']['WIDTH'])
        window_height = int(self.api_config['WIN']['HEIGHT'])
        window_pos = self.api_config['WIN']['POSITION']
        if window_pos == "left":
            y = (screen_height - window_height) // 2
            root.geometry(f"{window_width}x{window_height}+{0}+{y}")
        elif window_pos == "right":
            y = (screen_height - window_height) // 2
            root.geometry(f"{window_width}x{window_height}+{screen_width-window_width+2}+{y}")
        else:
            # Center the window
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create a text widget to display key events
        text_font = self.api_config['WIN']['TEXT_FONT']
        self.text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=30, 
                                                  font=tuple(text_font),  # Font family and size
                                                  padx=5,               # Horizontal padding inside the text area
                                                pady=5,                # Vertical padding inside the text area)
                                                highlightthickness=0, bd=0 # Remove border and no highlight
                                                
        ) 

        # Access the vertical scrollbar
        self.text_box.vbar.config(width=2)  # Sets scrollbar width (thickness) in pixels
        self.text_box.pack(padx=5, pady=(5,0), fill=tk.BOTH, expand=True)
        
        # Add a button to stop monitoring
        #self.stop_button = tk.Button(root, text="Stop", command=self.stop_monitoring)
        #self.stop_button.pack(pady=10)

        # Customized label
        self.tips_var = tk.StringVar(value=APP_TIPS)
        self.tips = tk.Label(
            root,
            textvariable=self.tips_var,
            font=("Arial", 14),  # Font family, size, and style
            fg="lightyellow",                  # Text color (foreground)
            wraplength=360,  # Wrap text after 250 pixels
            justify="left",   # Align text (left, center, or right)
            padx=0, pady=0
        )
        self.tips.pack(pady=(0,5))  # Add some vertical padding
        
        # Create a queue for thread communication
        self.event_queue = queue.Queue()
        self.result_queue = queue.Queue()  # Queue for results from the worker thread
        self.worker_thread = None
        
        # Create a key listener
        self.listener = KeyListener(self.event_queue)
        
        # Start the Cocoa app in a separate thread
        self.app_thread = CocoaAppThread(self.listener)
        self.app_thread.start()
        
        # Schedule the queue checking function
        self.poll_queues()
        '''
        self.listen_thread = threading.Thread(target=self.poll_queues)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        '''
        
    
    # Function to check the queues
    # Two queues: event_queue and result_queue
    # event_queue: for key events
    # result_queue: for results from the worker thread
    async def poll_queues(self):
        # Process event queue
        try:
            while True:
                message = self.event_queue.get_nowait()
                if message == "TaskEvent":
                    self.tips_var.set("Processing OCR and Translation ...")
                    if self.worker_thread and self.worker_thread.is_alive():
                        self.text_box.insert(tk.END, "Processing in progress. Please wait.\n")
                        self.text_box.see(tk.END)
                        continue
                    # Create and start the worker thread
                    self.worker_thread = threading.Thread(target=self.run_process_and_get_response)
                    self.worker_thread.daemon = True
                    self.worker_thread.start()
        except queue.Empty:
            pass

        # Process result queue
        try:
            while True:
                formatted_text = self.result_queue.get_nowait()
                if formatted_text:                    
                    self.text_box.insert(tk.END, formatted_text)
                    self.text_box.see(tk.END)
                    
        except queue.Empty:
            pass

        # Schedule the next poll
        self.root.after(200, self.poll_queues)
    
    def stop_monitoring(self):
        # Stop the listener
        if hasattr(self, 'listener'):
            self.listener.stop()
            AppHelper.stopEventLoop()
            #self.stop_button.config(text="Monitoring Stopped", state=tk.DISABLED)
            self.text_box.insert(tk.END, "App stopped.\n")
            self.text_box.see(tk.END)
    
    def run_process_and_get_response(self):
        # This runs in the worker thread
        stream = self.api_config['API']['STREAM']
        stream = stream.lower()
        stream_result = True if stream == "true" or stream == "yes" else False
        # If not stream mode, put the result into the result queue
        if not stream_result:
            # time-consuming function, no streaming
            formatted_text = process_capture_window_text(self.api_config)  
            # Clear the text box
            self.text_box.delete(1.0, tk.END)
            # Directly put the result into the result queue
            self.result_queue.put(formatted_text)  
            # Reset tips
            self.tips_var.set(APP_TIPS)
        else:
            # time-consuming function, with streaming
            process_capture_window_text(self.api_config, self.stream_response_call)
    
    # Stream response callback
    def stream_response_call(self, text, end=False):
        # Check if it’s the first call; if so, initialize the counter and clear the text box.  
        if not hasattr(self, '_stream_response_call_count'):
            # Initialize counter if it doesn't exist
            self._stream_response_call_count = 0
            self.text_box.delete(1.0, tk.END)
            
        if not end:
            # If it’s not the end state, place the text into the result queue and increment the counter
            self.result_queue.put(text)
            self._stream_response_call_count += 1
        else:
            # If it’s the end state, insert the text into the text box, update the prompt message, and delete the counter.
            self.text_box.insert(tk.END, text + "\n")
            self.text_box.see(tk.END)
            self.tips_var.set(APP_TIPS)
            # Remove the counter attribute when done
            del self._stream_response_call_count



if __name__ == "__main__":
    root = tk.Tk()
    app = TkinterApp(root)
    
    # Handle window close
    def on_closing():
        app.stop_monitoring()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()