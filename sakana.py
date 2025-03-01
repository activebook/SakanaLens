import tkinter as tk
from tkinter import ttk
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
import tooltip
import translate
import config

APP_TITLE = "Sakana Lens 日本語の自動翻訳"
# Constants for keyboard shortcut events
APP_EVENT_CT = "app.shortcut.ctrl_t.task"  # Event for Ctrl+T
APP_EVENT_CMT = "app.shortcut.ctrl_cmd_t.special"  # Event for Ctrl+Cmd+T

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
def capture_window(api_config, message):

    temp_file = api_config["DEBUG"]["SCREENSHOT"]
    try:
        # print("Ctrl+T pressed")
        if message == APP_EVENT_CT:
            # Get front window info
            front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            front_app_name = front_app.localizedName()
            
            # Get windows from front app
            window_list = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID)
                
            windows = [window for window in window_list if window['kCGWindowOwnerName'] == front_app_name]            
            if not windows: return None
                
            # Get the topmost window (retrieve the last one which contains text)
            window = windows[-1]
            bounds = window['kCGWindowBounds']
            # Convert coordinates to integers
            x,y,width,height = int(bounds['X']),int(bounds['Y']),int(bounds['Width']),int(bounds['Height'])

            # Use CoreGraphics to draw a temporary red border
            '''
            cg_context = Quartz.CGDisplayCreateImageForRect(
                Quartz.CGMainDisplayID(),
                Quartz.CGRectMake(x, y, width, height)
            )
            '''
            
            screenshot = pyautogui.screenshot(region=(x, y, width, height))   
            if temp_file != "":
                # Print information for debugging
                print(f"Front app: {front_app_name}")
                print(f"Window detected: {front_app_name}")
                print(f"Position: X={x}, Y={y}, Width={width}, Height={height}")
                print(f"Screenshot saved to {temp_file}")
                screenshot.save(temp_file)
            return screenshot

        # print("Ctrl+Cmd+T pressed")
        elif message == APP_EVENT_CMT:
            # using macOS's built-in screenshot highlighting capability. 
            # We can use the screencapture command-line tool with its interactive mode to highlight the window temporarily
            # Create a temporary file for the overlay
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, temp_file)

            try:
                # Check if file exists before deleting
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                pass
            
            # Take a screenshot with the built-in highlight feature
            # This will briefly highlight the window
            result = subprocess.run([
                "screencapture",
                "-i",  # Capture screen interactively, by selection or window
                #"-w",  # Window capture mode
                #"-s", # only window mode
                "-o",  # Don't include shadow
                "-x",  # Don't play sounds
                temp_file
            ])

            # Check return code (0 typically means success)
            if result.returncode == 0 and os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                # Print information for debugging
                print(f"Screenshot saved to {temp_file}")
                screenshot = Image.open(temp_file)
                return screenshot

            return None
        else:
            return None
        
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None

# Simulated AI API function (replace with real API later)
def simulate_ai_api(image, api_config, stream_call=None):
    # Placeholder: Pretend this processes the image and returns Japanese + English text
    english_text = translate.call_real_api(image, api_config, stream_call)
    return english_text

# Function to simulate speech
def simulate_speech(text, api_config):
    thread = translate.call_speech(text, api_config)
    # we don't need to wait for the thread to finish
    # because the mainloop will handle it
    '''
    if thread:
        thread.join()
    '''

# Function to process screenshot and update UI
def process_capture_window_text(api_config, message, stream_call=None):
    screenshot = capture_window(api_config, message)
    if screenshot:
        # Call Gemini API
        formatted_text = simulate_ai_api(screenshot, api_config, stream_call)
        return formatted_text
    else:
        return None


class KeyListener:
    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.monitor = None
        self.running = True
        
    """
    Handles keyboard events and puts corresponding task events into the event queue based on the key combination pressed.

    ctrl + t: APP_EVENT_CT
    ctrl + cmd + t: APP_EVENT_CMT
    """
    def handle_event(self, event):
        # Get the key information
        key_char = event.characters()
        key_code = event.keyCode()
        modifiers = event.modifierFlags()
        
        # Define modifier key masks
        control_key_mask = (1 << 18)  # NSControlKeyMask
        command_key_mask = (1 << 20)  # NSCommandKeyMask
        
        # Check for Ctrl+T
        if key_code == 17 and (modifiers & control_key_mask) and not (modifiers & command_key_mask):            
            print("Ctrl+T was pressed!")
            self.event_queue.put(APP_EVENT_CT)
        # Check for Ctrl+Cmd+T
        elif key_code == 17 and (modifiers & control_key_mask) and (modifiers & command_key_mask):
            print("Ctrl+Cmd+T was pressed!")
            self.event_queue.put(APP_EVENT_CMT)  # Different event for Ctrl+Cmd+T
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

        '''
        Here's the high cpu usage issue:
        Only use Tkinter's event loop (root.mainloop())
        This should significantly reduce your CPU usage by eliminating the competing event loops.
        '''
        #AppHelper.runEventLoop()
        
        # Release the pool
        del pool

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

        # Add a button(no border) to show tips
        # Build the file path to image
        qmark_path = os.path.dirname(os.path.realpath(__file__)) + "/question_mark.png"
        self.qmark_img = tk.PhotoImage(file=qmark_path)
        self.tips_btn = tk.Label(root, image=self.qmark_img, bg=self.text_box.cget("bg"), borderwidth=0, highlightthickness=0)
        self.tips_btn.place(relx=0.96, rely=0.96, anchor="se")

        """
        Handles the event when the text widget is modified.
        Checks the content of the text widget and manages the display state of the tips button based on whether the content is empty.        
        """
        def on_text_modified(event):
            widget = event.widget            
            # Check content whenever a modification occurs
            content = widget.get("1.0", "end-1c")
            if len(content) == 0:                
                # Hide button momentarily
                #self.tips_btn.place_forget()
                # Force display update
                #root.update_idletasks()                
                # Show button again
                #self.tips_btn.place(relx=0.96, rely=0.96, anchor="se")
                # Just lift the button to the top to appear
                self.tips_btn.lift()
            else:
                 # Hide button momentarily
                #self.tips_btn.place_forget()
                # Force display update
                #root.update_idletasks()                
                #self.tips_btn.place(x=-100, y=-100)
                # Just lower the button to the bottom to disappear
                self.tips_btn.lower(widget)
            # Now reset the modified flag at the end
            widget.edit_modified(False) 
                
        self.text_box.bind("<<Modified>>", on_text_modified)


        # bind the tooltip to the button
        tooltip_text = self.api_config["WIN"]["HOWTO"]
        self.dync_tooltip = tooltip.DynamicTooltip(
            self.tips_btn, 
            text=tk.StringVar(value=tooltip_text),
            bg_color="#2c2c2c",
            text_color="#ffffff",
            font=("Helvetica", 12),
            duration=4000
        )

        # Spinner (Progressbar in indeterminate mode)
        self.spinner_bar = ttk.Progressbar(root, mode="indeterminate", length=window_width/2)
        self.spinner_bar.pack(pady=(0,0))        
        
        # Create a queue for thread communication
        self.event_queue = queue.Queue()
        self.result_queue = queue.Queue()  # Queue for results from the worker thread
        self.worker_thread = None
        
        # Create a key listener
        self.listener = KeyListener(self.event_queue)
        
        # Start the Cocoa app and queue checking (time consuming tasks) in a separate thread
        self.start_thread(self.start_async_task)


    """
    Starts the Cocoa application and schedules queue checking tasks in separate threads.

    This method initializes and starts a Cocoa application in a separate thread using
    the CocoaAppThread class. It also schedules the polling of event and result queues
    by starting separate threads for each using the start_thread method.
    """
    def start_async_task(self):
        
        # Start the Cocoa app in a separate thread
        self.app_thread = CocoaAppThread(self.listener)
        self.app_thread.start()
        
        # Schedule the queue checking function
        self.start_thread(self.poll_event_queue)
        self.start_thread(self.poll_result_queue)


    def start_thread(self, func, args=()):
        thread = threading.Thread(target=func, args=args)
        thread.daemon = True
        thread.start()
        return thread
    
    # Function to check the queues
    # Two queues: event_queue and result_queue
    # event_queue: for key events
    # result_queue: for results from the worker thread
    def poll_event_queue(self):
        # Process event queue
        while True:
            message = self.event_queue.get()
            if message == APP_EVENT_CT or message == APP_EVENT_CMT:
                # Show the spinner and update status
                self.spinner_bar.start()  # Start the indeterminate animation                
                if self.worker_thread and self.worker_thread.is_alive():
                    #self.text_box.insert(tk.END, "Processing in progress. Please wait.\n")
                    #self.text_box.see(tk.END)
                    continue
                else:
                    # Create and start the worker thread
                    self.worker_thread = self.start_thread(self.run_process_and_get_response, (message,))                    

    """
    Continuously processes items from the result queue and updates the text box.

    Retrieves formatted text from the result queue and inserts it into the text box
    widget. Ensures the text box view is updated to show the latest inserted text.
    This method runs indefinitely in a separate thread.
    """
    def poll_result_queue(self):
        # Process result queue
        while True:
            formatted_text = self.result_queue.get()
            if formatted_text:                    
                self.text_box.insert(tk.END, formatted_text)
                self.text_box.see(tk.END)
            

    def stop_monitoring(self):
        # Stop the listener
        if hasattr(self, 'listener'):
            self.listener.stop()
            AppHelper.stopEventLoop()
            #self.stop_button.config(text="Monitoring Stopped", state=tk.DISABLED)
            self.text_box.insert(tk.END, "App stopped.\n")
            self.text_box.see(tk.END)
    
    def run_process_and_get_response(self, message):
        # This runs in the worker thread
        stream = self.api_config['API']['STREAM']
        stream = stream.lower()
        stream_result = True if stream == "true" or stream == "yes" else False
        # If not stream mode, put the result into the result queue
        if not stream_result:
            # time-consuming function, no streaming
            formatted_text = process_capture_window_text(self.api_config, message)  
            # Clear the text box
            self.text_box.delete(1.0, tk.END)
            # Directly put the result into the result queue
            self.result_queue.put(formatted_text)  
            # Reset spinner
            self.spinner_bar.stop()
        else:
            # time-consuming function, with streaming
            formatted_text = process_capture_window_text(self.api_config, message, self.stream_response_call)
            if formatted_text is None:
                # Nothing to translate (either user cancelled the capture or no text was detected)
                # Reset spinner
                self.spinner_bar.stop()
    
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
            # Reset spinner
            self.spinner_bar.stop()
            # Remove the counter attribute when done
            del self._stream_response_call_count
            # Call speech
            content = self.text_box.get("1.0", tk.END)
            simulate_speech(content, self.api_config)



if __name__ == "__main__":
    root = tk.Tk()
    app = TkinterApp(root)
    
    # Handle window close
    def on_closing():
        app.stop_monitoring()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()