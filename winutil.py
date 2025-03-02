"""
Fullscreen Drawing Application - A simple tool for drawing rectangles on a
transparent overlay window with a control panel for managing the overlay.
"""
# For macOS using PyObjC to access Cocoa/AppKit
from AppKit import NSScreen, NSWorkspace, NSApplicationActivateIgnoringOtherApps
from Cocoa import NSEvent, NSKeyDownMask
import tkinter as tk
import time

def switch_to_app(app_name):
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    for app in running_apps:
        if app.localizedName() == app_name:
            app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            return True
    return False

def get_screen_size():
    main_screen = NSScreen.mainScreen()
    frame = main_screen.frame()
    width = int(frame.size.width)
    height = int(frame.size.height)
    return width, height

class RegionManager:
    def __init__(self):
        self.last_region = None
        
    def select_region(self, region):
        self.last_region = region
        
    def get_last_region(self):
        return self.last_region

# Create single instance
region_manager = RegionManager()


class DrawingCanvas:
    """Canvas for drawing rectangles in a transparent overlay window."""
    
    def __init__(self, parent, color, end_callback):
        """Initialize the drawing canvas."""
        self.parent = parent
        self.color = color
        self.end_callback = end_callback
        
        # Create canvas with black background
        self.canvas = tk.Canvas(parent, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create coordinate label
        self.coord_label = tk.Label(
            self.canvas, 
            bg='white', 
            fg='black',
            font=('Arial', 10),
            padx=4,
            pady=2
        )
        
        # Initialize drawing state variables
        self.start_position = None
        self.drawing_region = None
        self.current_rectangle = None
        
        # Bind mouse events for drawing
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        # Drag while moving the mouse
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)        
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        
        # Bind Escape key to exit fullscreen
        # When setting up full-screen mode:
        #self.parent.bind("<Escape>", self._exit_fullscreen)
        #self.original_close_handler = self.parent.protocol("WM_DELETE_WINDOW", self._exit_fullscreen)  # Window close button

        # Modify the Escape key binding for macOS
        self.parent.bind("<Escape>", self._exit_fullscreen)
        
        # Add additional binding for Command-period (macOS standard escape equivalent)
        self.parent.bind("<Command-period>", self._exit_fullscreen)
        
        # Add binding at the canvas level too
        self.canvas.bind("<Escape>", self._exit_fullscreen)
        
        # Force focus to the canvas so it can receive keyboard events
        self.canvas.focus_set()
        
        # Store original handler
        self.original_close_handler = self.parent.protocol("WM_DELETE_WINDOW", self._exit_fullscreen)
    
    def _on_mouse_press(self, event):
        """Start drawing a rectangle when mouse button is pressed."""
        self.start_position = (event.x, event.y)
        self.current_rectangle = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, 
            outline=None, width=0,
            fill=self.color
        )

        # Display and position coordinate label
        self.coord_label.config(text=f"x: {event.x}, y: {event.y}")
        self.coord_label.place(x=event.x + 10, y=event.y + 10)
    
    def _on_mouse_drag(self, event):
        """Update rectangle dimensions during mouse drag."""
        if self.current_rectangle and self.start_position:
            start_x, start_y = self.start_position
            self.canvas.coords(
                self.current_rectangle, 
                start_x, start_y, event.x, event.y
            )
            # Update coordinate label text and position
            self.coord_label.config(text=f"({event.x}, {event.y})")
            self.coord_label.place(x=event.x + 10, y=event.y + 10)            
    
    def _on_mouse_release(self, event):
        """Complete rectangle drawing on mouse release."""
        if self.current_rectangle:
            # Calculate the bounding rectangle
            start_x, start_y = self.start_position
            last_x, last_y = event.x, event.y
            x1 = min(start_x, last_x)
            y1 = min(start_y, last_y)
            width = abs(last_x - start_x)
            height = abs(last_y - start_y)
            if width > 0 and height > 0:                
                self.drawing_region = (x1, y1, width, height)
            self.canvas.delete(self.current_rectangle)
            self.current_rectangle = None
            self.start_position = None
            # Hide the coordinate label
            self.coord_label.place_forget()
            self._exit_fullscreen()

    '''
    def _exit_fullscreen(self, event=None):
        # Perform exit full screen actions
        # Then unbind the events so they won't trigger again:
        print("Exiting fullscreen")
        self.parent.unbind("<Escape>")
        self.parent.protocol("WM_DELETE_WINDOW", self.original_close_handler)
        self.end_callback(self.drawing_region)
    '''
    
    def _exit_fullscreen(self, event=None):
        """Exit fullscreen mode."""
        #print("Exiting fullscreen")
        # Save the drawing region locally before any destruction occurs
        region = self.drawing_region
        
        # Unbind the events to prevent multiple calls
        self.parent.unbind("<Escape>")
        
        # Important: Don't restore the original handler yet - this can lead to race conditions
        # self.parent.protocol("WM_DELETE_WINDOW", self.original_close_handler)
        
        # Directly call the callback with our region data
        if self.end_callback:
            self.end_callback(region)


class ScreenCaptureWindow:
    """Main application for managing fullscreen drawing overlay."""
    
    def __init__(self, color):
        """Initialize the main application."""
        self.color = color
        self.overlay_window = None
        self.drawing_region = None
        self._open_drawing_canvas()
    
    def _open_drawing_canvas(self):
        """Open the transparent fullscreen drawing overlay."""
        # Return early if overlay window already exists
        if self.overlay_window and self.overlay_window.winfo_exists():
            return
            
        # Create new overlay window
        self.overlay_window = tk.Toplevel()
        
        # Configure overlay window properties
        self._configure_overlay_window()
        
        # Create drawing canvas within the overlay
        self.canvas = DrawingCanvas(self.overlay_window, self.color, self.close_drawing_canvas)

        # Add direct binding here as well for redundancy
        self.overlay_window.bind("<Escape>", lambda e: self.close_drawing_canvas(None))

    def wait(self):
        if self.overlay_window:
            self.overlay_window.wait_window()
    
    def _configure_overlay_window(self):
        """Configure the properties of the overlay window."""
        if not self.overlay_window:
            return
            
        # Remove window decorations
        self.overlay_window.overrideredirect(True)
        
        # Make window transparent (platform-specific settings)
        try:
            self.overlay_window.wm_attributes("-transparent", True)
            self.overlay_window.configure(bg="systemTransparent")
        except tk.TclError:
            # Fallback if not supported on current platform
            pass
            
        # Size and position
        screen_width,screen_height = get_screen_size()
        self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Other window properties
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.5)
        self.overlay_window.configure(bg='black')

        # For macOS, make sure the window can receive keyboard focus
        self.overlay_window.focus_force()
        
        # Add direct binding for Escape at this level too
        self.overlay_window.bind("<Escape>", lambda e: self.close_drawing_canvas(None))
        
        # Add Command-period binding (macOS standard)
        self.overlay_window.bind("<Command-period>", lambda e: self.close_drawing_canvas(None))
        
    
    '''
    def close_drawing_canvas(self, drawing_region):
        """Close the drawing overlay if it exists."""
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.drawing_region = drawing_region
            self.overlay_window.attributes('-fullscreen', False)
            self.overlay_window.destroy()
            self.overlay_window = None
            self.canvas = None
    '''
    def close_drawing_canvas(self, drawing_region):
        """Close the drawing overlay if it exists."""
        if self.overlay_window and self.overlay_window.winfo_exists():
            # Set the drawing region
            self.drawing_region = drawing_region
            
            # Clear existing protocol handlers before destroying
            self.overlay_window.protocol("WM_DELETE_WINDOW", "")
            
            # Destroy the window
            self.overlay_window.destroy()
            self.overlay_window = None
            self.canvas = None


# animate your tkinter window sliding in from the right side of the screen:
def animate_window_from_right(window, final_x, start_y, width, height, animation_duration=0.1):
    # Get screen width
    screen_width = window.winfo_screenwidth()
    
    # Start position (off-screen to the right)
    start_x = screen_width
    
    # Set initial window position and size
    window.geometry(f"{width}x{height}+{start_x}+{start_y}")
    window.update()
    
    # Calculate animation steps
    steps = 30
    delay = animation_duration / steps
    distance_per_step = (start_x - final_x) / steps
    
    # Animate window sliding in
    for step in range(steps + 1):
        current_x = start_x - int(step * distance_per_step)
        window.geometry(f"{width}x{height}+{current_x}+{start_y}")
        window.update()
        time.sleep(delay)

# animate your tkinter window sliding in from the left side of the screen
def animate_window_from_left(window, final_x, start_y, width, height, animation_duration=0.1):
    # Start position (off-screen to the left)
    start_x = -width
    
    # Set initial window position and size
    window.geometry(f"{width}x{height}+{start_x}+{start_y}")
    window.update()
    
    # Calculate animation steps
    steps = 20
    delay = animation_duration / steps
    distance_per_step = (final_x - start_x) / steps
    
    # Animate window sliding in
    for step in range(steps + 1):
        current_x = start_x + int(step * distance_per_step)
        window.geometry(f"{width}x{height}+{current_x}+{start_y}")
        window.update()
        time.sleep(delay)



# Mouse event masks
NSLeftMouseDownMask = 1 << 0
NSLeftMouseUpMask = 1 << 1
NSRightMouseDownMask = 1 << 2
NSRightMouseUpMask = 1 << 3
NSMouseMovedMask = 1 << 5
NSScrollWheelMask = 1 << 11

"""
Returns the current mouse position on the screen as (x, y) coordinates.
The origin (0,0) is at the bottom-left corner of the primary display.
"""
def get_mouse_position():
    mouse_location = NSEvent.mouseLocation()
    return (mouse_location.x, mouse_location.y)

class MouseListener:
    def __init__(self, notify=None):
        self.notify = notify
        self.monitors = []
        self.running = True
        self.last_position = (0, 0)
        
    """
    Handles mouse events and puts corresponding task events into the event queue.
    
    Tracks:
    - Mouse movement with position and delta
    - Left mouse clicks with position
    - Right mouse clicks with position
    - Scroll wheel events with delta
    """
    def handle_mouse_move(self, event):
        mouse_location = NSEvent.mouseLocation()
        current_position = (mouse_location.x, mouse_location.y)
        
        # Calculate movement delta
        delta_x = current_position[0] - self.last_position[0]
        delta_y = current_position[1] - self.last_position[1]
        self.last_position = current_position
        
        if self.notify:
            self.notify(NSMouseMovedMask, current_position)
        #print(f"Mouse moved to {current_position}, delta: {delta_x}, {delta_y}")

    def handle_left_click(self, event):
        mouse_location = NSEvent.mouseLocation()
        position = (mouse_location.x, mouse_location.y)
        if self.notify:
            self.notify(NSLeftMouseDownMask, position)
        #print(f"Left mouse button clicked at {position}")
    
    def handle_right_click(self, event):
        mouse_location = NSEvent.mouseLocation()
        position = (mouse_location.x, mouse_location.y)
        if self.notify:
            self.notify(NSRightMouseDownMask, position)
        #print(f"Right mouse button clicked at {position}")
        
    
    def handle_scroll(self, event):
        delta_x = event.scrollingDeltaX()
        delta_y = event.scrollingDeltaY()
        print(f"Scroll wheel: deltaX={delta_x}, deltaY={delta_y}")
        

    def start(self):
        # Set up separate monitors for different mouse events
        '''
        self.monitors.append(NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSMouseMovedMask, self.handle_mouse_move
        ))
        '''
        self.monitors.append(NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSLeftMouseDownMask, self.handle_left_click
        ))
        
        self.monitors.append(NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSRightMouseDownMask, self.handle_right_click
        ))
        '''
        self.monitors.append(NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSScrollWheelMask, self.handle_scroll
        ))
        '''
        # Initialize last position to current mouse position
        mouse_location = NSEvent.mouseLocation()
        self.last_position = (mouse_location.x, mouse_location.y)
    
    def stop(self):
        # Remove all monitors
        for monitor in self.monitors:
            if monitor:
                NSEvent.removeMonitor_(monitor)
        
        self.monitors = []


NSKeyCTRLTMask = 1 << 1 # ctrl + t
NSKeyCTRLCMDTMask = 1 << 2 # ctrl + cmd + t
NSKeyCTRLCMDRMask = 1 << 3 # ctrl + cmd + r

class KeyListener:
    def __init__(self, notify=None):
        self.notify = notify
        self.monitor = None
        self.running = True
        
    """
    Handles keyboard events and puts corresponding task events into the event queue based on the key combination pressed.

    ctrl + t: APP_EVENT_CT
    ctrl + cmd + t: APP_EVENT_CMT
    """
    def handle_event(self, event):
        if not self.notify:
            return
        
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
            self.notify(NSKeyCTRLTMask)            
        # Check for Ctrl+Cmd+T
        elif key_code == 17 and (modifiers & control_key_mask) and (modifiers & command_key_mask):
            print("Ctrl+Cmd+T was pressed!")
            self.notify(NSKeyCTRLCMDTMask)
        # Check for Ctrl+Cmd+R
        elif key_code == 15 and (modifiers & control_key_mask) and (modifiers & command_key_mask):
            print("Ctrl+Cmd+R was pressed!")
            self.notify(NSKeyCTRLCMDRMask)
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

