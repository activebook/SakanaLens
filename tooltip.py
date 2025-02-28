import tkinter as tk

class DynamicTooltip:
    def __init__(self, widget, text="", bg_color="#333333", text_color="#FFFFFF", 
                 duration=3000, width=200, font=("Helvetica", 10)):
        self.widget = widget
        self.bg_color = bg_color
        self.text_color = text_color
        self.duration = duration
        self.width = width
        self.font = font
        self.tooltip = None
        self.timer_id = None
        self.label = None
        # Support both StringVar and plain string for text
        if isinstance(text, tk.StringVar):
            self.text_var = text
        else:
            self.text_var = tk.StringVar(value=text)

        self.widget.bind("<Button-1>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def set_text(self, text):
        """Change the tooltip text"""
        self.text_var.set(text)
        # If tooltip is visible, update it immediately
        if self.tooltip and self.label:
            self.label.config(text=self.text_var.get())
            
    def get_text(self):
        """Get the current tooltip text"""
        return self.text_var.get()
    
    def show_tooltip(self, event):
        if self.tooltip:
            self.hide_tooltip()
            
        x, y = event.x_root, event.y_root
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        
        # Create a frame with padding
        frame = tk.Frame(self.tooltip, bg=self.bg_color, padx=12, pady=8)
        frame.pack(fill="both", expand=True)
        
        # Create modern looking label
        self.label = tk.Label(
            frame, 
            textvariable=self.text_var,  # Use textvariable instead of text
            background=self.bg_color,
            foreground=self.text_color,
            font=self.font,
            justify=tk.LEFT,
            wraplength=self.width if self.width else 200,
            bd=0
        )
        self.label.pack(fill="both", expand=True)

        # Get screen dimensions
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # Position below the widget with offset
        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_width()
        tooltip_height = self.tooltip.winfo_height()
        
        # Default position (right and below cursor)
        tooltip_x = x + 15
        tooltip_y = y + 15
        
        # Check if tooltip would go off right edge of screen
        if tooltip_x + tooltip_width > screen_width - 15:
            # Place to the left of cursor instead
            tooltip_x = x - tooltip_width - 15
        
        # Check if tooltip would go off bottom edge of screen
        if tooltip_y + tooltip_height > screen_height - 15:
            # Place above cursor instead
            tooltip_y = y - tooltip_height - 15
            
        # Apply the calculated position
        self.tooltip.geometry(f"+{tooltip_x}+{tooltip_y}")
        
        # Add fade-in effect (gradually increase opacity)
        self.tooltip.attributes("-alpha", 0.0)
        self._fade_in()
        
        # Auto-close after duration
        self.timer_id = self.widget.after(self.duration, self._fade_out)
    
    def _fade_in(self, alpha=0.0):
        alpha += 0.1
        if self.tooltip:
            self.tooltip.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.widget.after(20, lambda: self._fade_in(alpha))
    
    def _fade_out(self, alpha=1.0):
        alpha -= 0.1
        if alpha <= 0:
            self.hide_tooltip()
        else:
            if self.tooltip:
                self.tooltip.attributes("-alpha", alpha)
            self.timer_id = self.widget.after(20, lambda: self._fade_out(alpha))
    
    def hide_tooltip(self, event=None):
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.label = None


# test
if __name__ == "__main__":
    pass