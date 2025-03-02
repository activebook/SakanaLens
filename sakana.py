import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from AppKit import NSApplication, NSWorkspace
from PyObjCTools import AppHelper
from PIL import Image
import Quartz
import threading
import Foundation
import queue
import subprocess
import os
import sys
import tempfile
import pyautogui
import winutil
import tooltip
import translate
import config

"""
Custom handler for unraisable exceptions.

This function filters out specific unraisable exceptions related to
dummy thread finalization by checking the object's representation.
If the exception is related to 'DeleteDummyThreadOnDel', it is ignored.
For all other unraisable exceptions, the default system exception
hook is used to handle them.

Parameters:
    unraisable (unraisablehookargs): The unraisable exception details.
"""
def my_unraisable_hook(unraisable):
    # Filter out the dummy thread finalization error by checking the object's representation.
    if "DeleteDummyThreadOnDel" in repr(unraisable.object):
        # Ignore this error.
        return
    # For any other unraisable exception, use the default behavior.
    sys.__excepthook__(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback)

sys.unraisablehook = my_unraisable_hook


APP_TITLE = "Sakana Lens 日本語の自動翻訳"
# Constants for keyboard shortcut events
APP_EVENT_CT = "app.shortcut.ctrl_t.task"  # Event for Ctrl+T
APP_EVENT_CMT = "app.shortcut.ctrl_cmd_t.special"  # Event for Ctrl+Cmd+T
APP_EVENT_CMR = "app.shortcut.ctrl_cmd_r.special"  # Event for Ctrl+Cmd+R

# PyObjC approach: Python script to capture the active window screenshot
def capture_window(api_config, message):

    temp_file = api_config["DEBUG"]["SCREENSHOT"]
    try:
        # Get front window info
        front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        front_app_name = front_app.localizedName()

        # print("Ctrl+T pressed")
        if message == APP_EVENT_CT:
            last_region = winutil.region_manager.get_last_region()
            if last_region is None:    
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
                last_region = (x, y, width, height)
            
            screenshot = pyautogui.screenshot(region=last_region)   
            if temp_file != "":
                # Print information for debugging
                print(f"Window detected: {front_app_name}")
                print(f"Screen Position: {last_region}")
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
        
        # print("Ctrl+Cmd+R pressed")
        elif message == APP_EVENT_CMR:
            
            # Capture the selection region
            region_color = api_config["WIN"]["REGION"]
            scw = winutil.ScreenCaptureWindow(region_color)
            # Block until the overlay window is destroyed
            scw.wait()
            
            # This step is very important, it cannot interfere with the window switching
            # Switch to the front app after closing the cover window
            winutil.switch_to_app(front_app_name)

            # No selected region
            if scw.drawing_region is None:
                return None
            
            # Get the drawing region            
            winutil.region_manager.select_region(scw.drawing_region)
            last_region = winutil.region_manager.get_last_region()
            screenshot = pyautogui.screenshot(region=last_region)   
            if temp_file != "":
                # Print information for debugging
                print(f"Window detected: {front_app_name}")
                print(f"Screen Position: {last_region}")
                print(f"Screenshot saved to {temp_file}")
                screenshot.save(temp_file)
            return screenshot
            
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
        root.withdraw()  # Hide window initially

        # Create a text widget to display key events
        text_font = self.api_config['WIN']['TEXT_FONT']
        self.text_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=40, height=30, 
                                                  font=tuple(text_font),  # Font family and size
                                                  padx=5,               # Horizontal padding inside the text area
                                                pady=5,                # Vertical padding inside the text area)
                                                highlightthickness=0, bd=0 # Remove border and no highlight
                                                ) 

        # Access the vertical scrollbar
        #self.text_box.vbar.config(width=0)  # Sets scrollbar width (thickness) in pixels
        self.text_box.vbar.pack_forget() # Hide the vertical scrollbar to make it more slight
        self.text_box.pack(padx=0, pady=(0,0), fill=tk.BOTH, expand=True)  

        # Add a button(no border) to show info
        imark_path = os.path.dirname(os.path.realpath(__file__)) + "/info_mark.png"
        self.imark_img = tk.PhotoImage(file=imark_path)
        self.info_btn = tk.Label(root, image=self.imark_img, bg=self.text_box.cget("bg"), borderwidth=0, highlightthickness=0)
        self.info_btn.place(relx=0.05, rely=0.95, anchor="sw")     

        # Add a button(no border) to show tips
        # Build the file path to image
        qmark_path = os.path.dirname(os.path.realpath(__file__)) + "/question_mark.png"
        self.qmark_img = tk.PhotoImage(file=qmark_path)
        self.tips_btn = tk.Label(root, image=self.qmark_img, bg=self.text_box.cget("bg"), borderwidth=0, highlightthickness=0)
        self.tips_btn.place(relx=0.95, rely=0.95, anchor="se")

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
                self.info_btn.lift()
                self.tips_btn.lift()
            else:
                 # Hide button momentarily
                #self.tips_btn.place_forget()
                # Force display update
                #root.update_idletasks()                
                #self.tips_btn.place(x=-100, y=-100)

                # Just lower the button to the bottom to disappear
                self.info_btn.lower(widget)
                self.tips_btn.lower(widget)

            # Now reset the modified flag at the end
            widget.edit_modified(False) 
                
        self.text_box.bind("<<Modified>>", on_text_modified)


        # bind the tooltip to the info button
        info_text = self.api_config["WIN"]["INFO"]
        self.dync_info = tooltip.DynamicTooltip(
            self.info_btn, 
            text=tk.StringVar(value=info_text),
            bg_color="#2c2c2c",
            text_color="#ffffff",
            font=("Helvetica", 12),
            duration=4000
        )

        # bind the tooltip to the tips button
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
        self.spinner_bar = ttk.Progressbar(root, mode="indeterminate", length=200)
        self.spinner_bar.pack(pady=(0,0))        
        
        # Create a queue for thread communication
        self.event_queue = queue.Queue()
        self.result_queue = queue.Queue()  # Queue for results from the worker thread
        self.worker_thread = None
        
        # Create a key listener
        def on_key_press(event):
            if event == winutil.NSKeyCTRLTMask:
                self.event_queue.put(APP_EVENT_CT)
            elif event == winutil.NSKeyCTRLCMDTMask:
                self.event_queue.put(APP_EVENT_CMT)
            elif event == winutil.NSKeyCTRLCMDRMask:
                self.event_queue.put(APP_EVENT_CMR)
            
        self.key_listener = winutil.KeyListener(on_key_press)
        
        # Start the Cocoa app and queue checking (time consuming tasks) in a separate thread
        self.start_thread(self.start_async_task)

        # Show the window with animation
        self.show_window(root)
            
    # Show the window with animation
    def show_window(self, root):
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Set window size and position
        window_width = int(self.api_config['WIN']['WIDTH'])
        window_height = int(self.api_config['WIN']['HEIGHT'])
        window_pos = self.api_config['WIN']['POSITION']
        if window_pos == "left":
            final_x = 0 # Leftcorner            
            y = (screen_height - window_height) // 2
            #root.geometry(f"{window_width}x{window_height}+{0}+{y}")
            # Show window and animate
            root.deiconify()
            winutil.animate_window_from_left(root, final_x, y, window_width, window_height)
        elif window_pos == "right":
            final_x = (root.winfo_screenwidth() - window_width) # Rightcorner
            y = (screen_height - window_height) // 2
            #root.geometry(f"{window_width}x{window_height}+{screen_width-window_width+2}+{y}")
            # Show window and animate
            root.deiconify()
            winutil.animate_window_from_right(root, final_x, y, window_width, window_height)
        else:
            # Center the window
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            root.deiconify()
            root.geometry(f"{window_width}x{window_height}+{x}+{y}")


    """
    Starts the Cocoa application and schedules queue checking tasks in separate threads.

    This method initializes and starts a Cocoa application in a separate thread using
    the CocoaAppThread class. It also schedules the polling of event and result queues
    by starting separate threads for each using the start_thread method.
    """
    def start_async_task(self):
        
        # Start the Cocoa app in a separate thread
        # monitor the key events
        self.app_key_thread = CocoaAppThread(self.key_listener)
        self.app_key_thread.start()
        
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
            if message == APP_EVENT_CT or message == APP_EVENT_CMT or message == APP_EVENT_CMR:
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
            if self.key_listener:
                self.key_listener.stop()
            AppHelper.stopEventLoop()
            
    
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