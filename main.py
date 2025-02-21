import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from queue import Queue
from dualsense_controller import DualSenseController
import math
from tkinter import ttk
from tkinter import messagebox
from tkinter import colorchooser
import os
import sys

class DualSenseGUI:
    def __init__(self):
        try:
            from ctypes import windll  # Only exists on Windows.

            myappid = "aneeskhan47.DualSenseControllerTester.1.0.0"
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except ImportError:
            pass
        self.root = tk.Tk()
        self.root.title("DualSense Controller Tester By AneesKhan47 (Version v1.0.0)")
        self.root.geometry("900x600")
        
        # Disable resizing and maximize button
        self.root.resizable(0, 0)
        
        # Center the window
        # Get the screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate the x and y coordinates for the window
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        
        # Set the position of the window to the center of the screen
        self.root.geometry(f"900x600+{x}+{y}")
        
        # Create update queue
        self.update_queue = Queue()
        
        # Controller status
        self.controller = None
        self.is_running = True
        
        # Initialize image attributes
        self.base_resized = None
        self.working_image = None
        self.controller_image = None
        self.image_on_canvas = None
        
        # Add stick position tracking with previous values
        self.left_stick_x = 0
        self.left_stick_y = 0
        self.prev_stick_x = 0
        self.prev_stick_y = 0
        self.right_stick_x = 0
        self.right_stick_y = 0
        self.prev_right_x = 0
        self.prev_right_y = 0
        
        # Update stick positions
        self.stick_positions = {
            'L3': (452, 688),  # Left analog stick position
            'R3': (755, 688)   # Right analog stick position
        }
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both')
        
        # Controller status label
        self.status_label = tk.Label(self.main_frame, text="Controller Status", font=('Arial', 14))
        self.status_label.pack(pady=10)
        
        # Create a frame for battery and connection indicators
        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(pady=5)
        
        # Battery indicator with better styling
        self.battery_label = tk.Label(
            self.status_frame, 
            text="Battery: ", 
            font=('Arial', 12)
        )
        self.battery_label.pack(side='left', padx=5)
        
        self.battery_value = tk.Label(
            self.status_frame,
            text="--",
            font=('Arial', 12, 'bold')
        )
        self.battery_value.pack(side='left', padx=(0, 20))
        
        # Connection type indicator
        self.connection_label = tk.Label(
            self.status_frame,
            text="Connection: ",
            font=('Arial', 12)
        )
        self.connection_label.pack(side='left', padx=5)
        
        self.connection_value = tk.Label(
            self.status_frame,
            text="--",
            font=('Arial', 12, 'bold')
        )
        self.connection_value.pack(side='left', padx=(0, 5))
        
        # Create frame for top controls (Haptic, Lightbar, and Player LEDs)
        self.top_controls_frame = tk.Frame(self.main_frame)
        self.top_controls_frame.pack(pady=5)
        
        # Haptic Feedback controls (left)
        self.rumble_frame = tk.Frame(self.top_controls_frame)
        self.rumble_frame.pack(side='left', padx=10)
        
        tk.Label(
            self.rumble_frame,
            text="Haptic Feedback (Rumble):",
            font=('Arial', 12)
        ).pack(side='left', padx=2)
        
        self.start_btn = tk.Button(
            self.rumble_frame,
            text="Start",
            command=self.start_rumble,
            width=6
        )
        self.start_btn.pack(side='left', padx=1)
        
        # Lightbar controls (middle)
        self.lightbar_frame = tk.Frame(self.top_controls_frame)
        self.lightbar_frame.pack(side='left', padx=5)
        
        tk.Label(
            self.lightbar_frame,
            text="Lightbar Color:",
            font=('Arial', 12)
        ).pack(side='left', padx=2)
        
        self.color_preview = tk.Label(
            self.lightbar_frame,
            width=3,
            height=1,
            relief="solid",
            borderwidth=1
        )
        self.color_preview.pack(side='left', padx=2)
        
        self.color_btn = tk.Button(
            self.lightbar_frame,
            text="Choose Color",
            command=self.choose_color,
            width=10
        )
        self.color_btn.pack(side='left', padx=2)
        
        # Player LEDs controls (right)
        self.leds_frame = tk.Frame(self.top_controls_frame)
        self.leds_frame.pack(side='left', padx=5)
        
        tk.Label(
            self.leds_frame,
            text="Player LEDs:",
            font=('Arial', 12)
        ).pack(side='left', padx=2)
        
        # LED Pattern Combo
        self.led_patterns = {
            'All': lambda c: c.player_leds.set_all(),
            'Inner': lambda c: c.player_leds.set_inner(),
            'Outer': lambda c: c.player_leds.set_outer(),
            'Center': lambda c: c.player_leds.set_center(),
            'Center & Outer': lambda c: c.player_leds.set_center_and_outer(),
            'Off': lambda c: c.player_leds.set_off()
        }
        
        self.led_var = tk.StringVar(value='Off')
        self.led_combo = ttk.Combobox(
            self.leds_frame,
            textvariable=self.led_var,
            values=list(self.led_patterns.keys()),
            state='readonly',
            width=12
        )
        self.led_combo.pack(side='left', padx=2)
        
        # LED Brightness Combo
        self.brightness_patterns = {
            'High': lambda c: c.player_leds.set_brightness_high(),
            'Medium': lambda c: c.player_leds.set_brightness_medium(),
            'Low': lambda c: c.player_leds.set_brightness_low()
        }
        
        self.brightness_var = tk.StringVar(value='High')
        self.brightness_combo = ttk.Combobox(
            self.leds_frame,
            textvariable=self.brightness_var,
            values=list(self.brightness_patterns.keys()),
            state='readonly',
            width=8
        )
        self.brightness_combo.pack(side='left', padx=5)
        
        # Apply button
        self.led_btn = tk.Button(
            self.leds_frame,
            text="Apply",
            command=self.apply_led_settings,
            width=6
        )
        self.led_btn.pack(side='left', padx=2)
        
        # Load and display controller image
        self.setup_controller_image()
        
        # Create frame for Adaptive Triggers (centered)
        self.triggers_frame = tk.Frame(self.main_frame)
        self.triggers_frame.pack(pady=10)
        
        tk.Label(
            self.triggers_frame,
            text="Adaptive Triggers:",
            font=('Arial', 12)
        ).pack(side='left', padx=5)
        
        self.trigger_effects = {
            'Off': lambda c: c.effect.off(),
            'Continuous Resistance': lambda c: c.effect.continuous_resistance(start_position=0, force=255),
            'Feedback': lambda c: c.effect.feedback(start_position=0, strength=8),
            'Weapon': lambda c: c.effect.weapon(start_position=2, end_position=5, strength=8),
            'Bow': lambda c: c.effect.bow(start_position=1, end_position=4, strength=1, snap_force=8),
            'Machine': lambda c: c.effect.machine(start_position=1, end_position=9, amplitude_a=2, amplitude_b=7, frequency=5, period=3)
        }
        
        self.trigger_var = tk.StringVar(value='Off')
        self.trigger_combo = ttk.Combobox(
            self.triggers_frame,
            textvariable=self.trigger_var,
            values=list(self.trigger_effects.keys()),
            state='readonly',
            width=20
        )
        self.trigger_combo.pack(side='left', padx=5)
        
        self.left_trigger_btn = tk.Button(
            self.triggers_frame,
            text="Apply Left",
            command=self.apply_left_trigger,
            width=8
        )
        self.left_trigger_btn.pack(side='left', padx=2)
        
        self.right_trigger_btn = tk.Button(
            self.triggers_frame,
            text="Apply Right",
            command=self.apply_right_trigger,
            width=8
        )
        self.right_trigger_btn.pack(side='left', padx=2)
        
        # Input status label (centered)
        self.input_status = tk.Label(self.main_frame, text="No inputs active", font=('Arial', 12))
        self.input_status.pack(pady=10)
        
        # Create frame for credit
        self.bottom_frame = tk.Frame(self.main_frame)
        self.bottom_frame.pack(fill='x', pady=5)
        
        # Developer credit (right aligned)
        self.credit_label = tk.Label(
            self.bottom_frame, 
            text="Developed by aneeskhan47", 
            font=('Arial', 9),
            fg='blue',
            cursor='hand2'
        )
        self.credit_label.pack(side='right', padx=10)
        self.credit_label.bind('<Button-1>', lambda e: self.open_github())
        
        # Button press coordinates (x, y) relative to image
        self.button_positions = {
            'L2': (298, 313),
            'L1': (292, 360),
            'R2': (907, 313),
            'R1': (909, 360),
            'Triangle': (901, 481),
            'Circle': (971, 551),
            'Cross': (901, 620),
            'Square': (830, 553),
            'D-Pad Up': (311, 508),
            'D-Pad Right': (354, 550),
            'D-Pad Down': (311, 588),
            'D-Pad Left': (266, 550),
            'Create': (385, 444),
            'Options': (827, 444),
            'PS': (604, 669),
            'Touchpad': (605, 477),
            'L3': (452, 688),
            'R3': (755, 688)
        }
        
        # Add button state tracking
        self.button_states = {
            'L2': False, 'L1': False,
            'R2': False, 'R1': False,
            'Triangle': False, 'Circle': False,
            'Cross': False, 'Square': False,
            'D-Pad Up': False, 'D-Pad Right': False,
            'D-Pad Down': False, 'D-Pad Left': False,
            'Create': False, 'Options': False,
            'PS': False, 'Touchpad': False,
            'L3': False, 'R3': False
        }
        
        # Start checking for controller
        self.check_controller()
        
        # Start processing GUI updates
        self.process_updates()
        
        self.rumble_active = False  # Add this to track rumble state

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def setup_controller_image(self):
        # Load the controller image
        self.original_image = Image.open(self.resource_path("ps5_controller.png"))
        
        # Create canvas that fills the window
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(expand=True, fill='both', pady=20)
        
        # Bind resize event
        self.canvas.bind('<Configure>', self.resize_image)
        
        # Initial image setup
        self.resize_image(None)

    def resize_image(self, event):
        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Ensure valid dimensions
            # Set minimum dimensions for the image (2x original size)
            min_width = 800  # Minimum width
            min_height = 500  # Minimum height
            
            # Resize image to fit canvas while maintaining aspect ratio
            resized_image = self.original_image.copy()
            # Calculate scaling factor while maintaining aspect ratio
            img_ratio = resized_image.size[0] / resized_image.size[1]
            canvas_ratio = canvas_width / canvas_height
            
            if canvas_ratio > img_ratio:
                new_height = max(canvas_height, min_height)
                new_width = int(new_height * img_ratio)
            else:
                new_width = max(canvas_width, min_width)
                new_height = int(new_width / img_ratio)
                
            # Store the base resized image
            self.base_resized = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Update the working image and display
            self.working_image = self.base_resized.copy()
            self.controller_image = ImageTk.PhotoImage(self.working_image)
            
            # Center the image on canvas
            x = canvas_width // 2
            y = canvas_height // 2
            
            # Create or update image on canvas
            if hasattr(self, 'image_on_canvas') and self.image_on_canvas:
                self.canvas.coords(self.image_on_canvas, x, y)
                self.canvas.itemconfig(self.image_on_canvas, image=self.controller_image)
            else:
                self.image_on_canvas = self.canvas.create_image(x, y, image=self.controller_image)

    def update_button_state(self, button, is_pressed):
        if button in self.button_positions:
            # Update button state
            self.button_states[button] = is_pressed
            
            # Reset to the base resized image first
            self.working_image = self.base_resized.copy()
            
            # Draw indicators for all pressed buttons
            for btn, state in self.button_states.items():
                if state and btn in self.button_positions:
                    # Get current image size
                    current_width = self.working_image.size[0]
                    current_height = self.working_image.size[1]
                    
                    # Scale the button positions according to current image size
                    orig_x, orig_y = self.button_positions[btn]
                    scale_x = current_width / 1200
                    scale_y = current_height / 1200
                    x = int(orig_x * scale_x)
                    y = int(orig_y * scale_y)
                    
                    self.draw = ImageDraw.Draw(self.working_image)
                    
                    # Draw indicator for pressed button
                    circle_radius = int(10 * min(scale_x, scale_y))
                    self.draw.ellipse([x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius], fill='red')
            
            # Update the image on canvas
            self.controller_image = ImageTk.PhotoImage(self.working_image)
            self.canvas.itemconfig(self.image_on_canvas, image=self.controller_image)
            
            # Update input status text
            self.update_input_status()

    def check_controller(self):
        if self.controller is None:
            device_infos = DualSenseController.enumerate_devices()
            if len(device_infos) > 0:
                try:
                    self.controller = DualSenseController()
                    self.setup_controller_callbacks()
                    self.controller.activate()
                    self.queue_update('status', "DualSense Controller connected!", 'green')
                    # Update connection type when controller connects
                    self.queue_update('connection', self.controller.connection_type.value)
                except Exception as e:
                    self.queue_update('status', f"Error connecting to controller: {e}", 'red')
                    self.controller = None
            else:
                self.queue_update('status', "No DualSense Controller available!", 'red')
        
        # Check again in 1 second
        if self.is_running:
            self.root.after(1000, self.check_controller)

    def setup_controller(self):
        # Remove controller initialization from here
        # It will be handled by check_controller
        pass

    def setup_controller_callbacks(self):
        # Move callback setup from setup_controller to here
        # Left side buttons
        self.controller.btn_l2.on_down(lambda: self.queue_update('button', ('L2', True)))
        self.controller.btn_l2.on_up(lambda: self.queue_update('button', ('L2', False)))
        
        self.controller.btn_l1.on_down(lambda: self.queue_update('button', ('L1', True)))
        self.controller.btn_l1.on_up(lambda: self.queue_update('button', ('L1', False)))
        
        # D-Pad
        self.controller.btn_up.on_down(lambda: self.queue_update('button', ('D-Pad Up', True)))
        self.controller.btn_up.on_up(lambda: self.queue_update('button', ('D-Pad Up', False)))
        
        self.controller.btn_right.on_down(lambda: self.queue_update('button', ('D-Pad Right', True)))
        self.controller.btn_right.on_up(lambda: self.queue_update('button', ('D-Pad Right', False)))
        
        self.controller.btn_down.on_down(lambda: self.queue_update('button', ('D-Pad Down', True)))
        self.controller.btn_down.on_up(lambda: self.queue_update('button', ('D-Pad Down', False)))
        
        self.controller.btn_left.on_down(lambda: self.queue_update('button', ('D-Pad Left', True)))
        self.controller.btn_left.on_up(lambda: self.queue_update('button', ('D-Pad Left', False)))
        
        # Center buttons
        self.controller.btn_create.on_down(lambda: self.queue_update('button', ('Create', True)))
        self.controller.btn_create.on_up(lambda: self.queue_update('button', ('Create', False)))
        
        self.controller.btn_touchpad.on_down(lambda: self.queue_update('button', ('Touchpad', True)))
        self.controller.btn_touchpad.on_up(lambda: self.queue_update('button', ('Touchpad', False)))
        
        self.controller.btn_options.on_down(lambda: self.queue_update('button', ('Options', True)))
        self.controller.btn_options.on_up(lambda: self.queue_update('button', ('Options', False)))
        
        # Right side buttons
        self.controller.btn_r2.on_down(lambda: self.queue_update('button', ('R2', True)))
        self.controller.btn_r2.on_up(lambda: self.queue_update('button', ('R2', False)))
        
        self.controller.btn_r1.on_down(lambda: self.queue_update('button', ('R1', True)))
        self.controller.btn_r1.on_up(lambda: self.queue_update('button', ('R1', False)))
        
        # Face buttons
        self.controller.btn_triangle.on_down(lambda: self.queue_update('button', ('Triangle', True)))
        self.controller.btn_triangle.on_up(lambda: self.queue_update('button', ('Triangle', False)))
        
        self.controller.btn_circle.on_down(lambda: self.queue_update('button', ('Circle', True)))
        self.controller.btn_circle.on_up(lambda: self.queue_update('button', ('Circle', False)))
        
        self.controller.btn_cross.on_down(lambda: self.queue_update('button', ('Cross', True)))
        self.controller.btn_cross.on_up(lambda: self.queue_update('button', ('Cross', False)))
        
        self.controller.btn_square.on_down(lambda: self.queue_update('button', ('Square', True)))
        self.controller.btn_square.on_up(lambda: self.queue_update('button', ('Square', False)))
        
        # PS button
        self.controller.btn_ps.on_down(lambda: self.queue_update('button', ('PS', True)))
        self.controller.btn_ps.on_up(lambda: self.queue_update('button', ('PS', False)))

        # L3 and R3
        self.controller.btn_l3.on_down(lambda: self.queue_update('button', ('L3', True)))
        self.controller.btn_l3.on_up(lambda: self.queue_update('button', ('L3', False)))
        
        self.controller.btn_r3.on_down(lambda: self.queue_update('button', ('R3', True)))
        self.controller.btn_r3.on_up(lambda: self.queue_update('button', ('R3', False)))
        
        # Battery callbacks - fixed to handle parameters
        self.controller.battery.on_change(lambda b: self.queue_update('battery', b))
        self.controller.battery.on_lower_than(20, lambda _: self.queue_update('battery_warning', 'Low battery!'))  # Added _ parameter
        self.controller.battery.on_charging(lambda _: self.queue_update('battery_status', 'charging'))
        self.controller.battery.on_discharging(lambda _: self.queue_update('battery_status', 'discharging'))
        
        # Error callback
        self.controller.on_error(lambda e: self.queue_update('error', e))

        # Add analog stick callbacks
        self.controller.left_stick_x.on_change(self.on_left_stick_x)
        self.controller.left_stick_y.on_change(self.on_left_stick_y)

        # Add right analog stick callbacks
        self.controller.right_stick_x.on_change(self.on_right_stick_x)
        self.controller.right_stick_y.on_change(self.on_right_stick_y)

    def on_left_stick_x(self, value):
        self.left_stick_x = value
        self.update_stick_indicator()

    def on_left_stick_y(self, value):
        # Invert the Y value
        self.left_stick_y = -value  # Invert Y axis
        self.update_stick_indicator()

    def on_right_stick_x(self, value):
        self.right_stick_x = value
        self.update_right_stick_indicator()

    def on_right_stick_y(self, value):
        # Invert the Y value like we did for left stick
        self.right_stick_y = -value
        self.update_right_stick_indicator()

    def update_stick_indicator(self):
        # Check if we have a valid base image
        if self.base_resized is None:
            return
            
        # Only update if stick position changed significantly
        if (abs(self.left_stick_x - self.prev_stick_x) < 0.01 and 
            abs(self.left_stick_y - self.prev_stick_y) < 0.01):
            return
            
        # Update previous values
        self.prev_stick_x = self.left_stick_x
        self.prev_stick_y = self.left_stick_y
        
        # Get current image size and position
        current_width = self.working_image.size[0]
        current_height = self.working_image.size[1]
        
        # Get the image position on canvas
        image_x = self.canvas.coords(self.image_on_canvas)[0]  # Center X of image
        image_y = self.canvas.coords(self.image_on_canvas)[1]  # Center Y of image
        
        # Get stick center position and scale it
        stick_x, stick_y = self.stick_positions['L3']
        scale_x = current_width / 1200
        scale_y = current_height / 1200
        
        # Calculate center position relative to the image position
        center_x = image_x - (current_width/2) + int(stick_x * scale_x)
        center_y = image_y - (current_height/2) + int(stick_y * scale_y)
        
        # Calculate arrow endpoint using stick values (-1 to 1)
        arrow_length = 30 * min(scale_x, scale_y)
        end_x = center_x + int(self.left_stick_x * arrow_length)
        end_y = center_y + int(self.left_stick_y * arrow_length)
        
        # Draw on the canvas directly
        if abs(self.left_stick_x) > 0.1 or abs(self.left_stick_y) > 0.1:
            # Delete previous arrow if it exists
            if hasattr(self, 'stick_arrow'):
                self.canvas.delete(self.stick_arrow)
                self.canvas.delete(self.stick_arrowhead)
            
            # Draw arrow line
            self.stick_arrow = self.canvas.create_line(
                center_x, center_y, end_x, end_y,
                fill='red', width=4
            )
            
            # Draw arrow head
            arrow_head_length = 10 * min(scale_x, scale_y)
            angle = math.atan2(end_y - center_y, end_x - center_x)
            
            # Calculate arrow head points
            head_angle = math.pi / 6  # 30 degrees
            point1_x = end_x - arrow_head_length * math.cos(angle + head_angle)
            point1_y = end_y - arrow_head_length * math.sin(angle + head_angle)
            point2_x = end_x - arrow_head_length * math.cos(angle - head_angle)
            point2_y = end_y - arrow_head_length * math.sin(angle - head_angle)
            
            # Draw arrow head
            self.stick_arrowhead = self.canvas.create_polygon(
                end_x, end_y, point1_x, point1_y, point2_x, point2_y,
                fill='red'
            )
        else:
            # Remove the arrow when stick is centered
            if hasattr(self, 'stick_arrow'):
                self.canvas.delete(self.stick_arrow)
                self.canvas.delete(self.stick_arrowhead)
        
        # Update input status text
        self.update_input_status()

    def update_right_stick_indicator(self):
        # Check if we have a valid base image
        if self.base_resized is None:
            return
            
        # Only update if stick position changed significantly
        if (abs(self.right_stick_x - self.prev_right_x) < 0.01 and 
            abs(self.right_stick_y - self.prev_right_y) < 0.01):
            return
            
        # Update previous values
        self.prev_right_x = self.right_stick_x
        self.prev_right_y = self.right_stick_y
        
        # Get current image size and position
        current_width = self.working_image.size[0]
        current_height = self.working_image.size[1]
        
        # Get the image position on canvas
        image_x = self.canvas.coords(self.image_on_canvas)[0]  # Center X of image
        image_y = self.canvas.coords(self.image_on_canvas)[1]  # Center Y of image
        
        # Get stick center position and scale it
        stick_x, stick_y = self.stick_positions['R3']
        scale_x = current_width / 1200
        scale_y = current_height / 1200
        
        # Calculate center position relative to the image position
        center_x = image_x - (current_width/2) + int(stick_x * scale_x)
        center_y = image_y - (current_height/2) + int(stick_y * scale_y)
        
        # Calculate arrow endpoint using stick values (-1 to 1)
        arrow_length = 30 * min(scale_x, scale_y)
        end_x = center_x + int(self.right_stick_x * arrow_length)
        end_y = center_y + int(self.right_stick_y * arrow_length)
        
        # Draw on the canvas directly
        if abs(self.right_stick_x) > 0.1 or abs(self.right_stick_y) > 0.1:
            # Delete previous arrow if it exists
            if hasattr(self, 'right_stick_arrow'):
                self.canvas.delete(self.right_stick_arrow)
                self.canvas.delete(self.right_stick_arrowhead)
            
            # Draw arrow line
            self.right_stick_arrow = self.canvas.create_line(
                center_x, center_y, end_x, end_y,
                fill='red', width=4
            )
            
            # Draw arrow head
            arrow_head_length = 10 * min(scale_x, scale_y)
            angle = math.atan2(end_y - center_y, end_x - center_x)
            
            # Calculate arrow head points
            head_angle = math.pi / 6  # 30 degrees
            point1_x = end_x - arrow_head_length * math.cos(angle + head_angle)
            point1_y = end_y - arrow_head_length * math.sin(angle + head_angle)
            point2_x = end_x - arrow_head_length * math.cos(angle - head_angle)
            point2_y = end_y - arrow_head_length * math.sin(angle - head_angle)
            
            # Draw arrow head
            self.right_stick_arrowhead = self.canvas.create_polygon(
                end_x, end_y, point1_x, point1_y, point2_x, point2_y,
                fill='red'
            )
        else:
            # Remove the arrow when stick is centered
            if hasattr(self, 'right_stick_arrow'):
                self.canvas.delete(self.right_stick_arrow)
                self.canvas.delete(self.right_stick_arrowhead)
        
        # Update input status text
        self.update_input_status()

    def update_input_status(self):
        # Collect active buttons
        active_buttons = [btn for btn, state in self.button_states.items() if state]
        
        # Format stick positions if they're being moved
        stick_info = []
        if abs(self.left_stick_x) > 0.1 or abs(self.left_stick_y) > 0.1:
            stick_info.append(f"Left Stick (x: {self.left_stick_x:.2f}, y: {self.left_stick_y:.2f})")
        if abs(self.right_stick_x) > 0.1 or abs(self.right_stick_y) > 0.1:
            stick_info.append(f"Right Stick (x: {self.right_stick_x:.2f}, y: {self.right_stick_y:.2f})")
        
        # Combine all active inputs
        all_inputs = active_buttons + stick_info
        
        if all_inputs:
            status_text = "Active Inputs: " + " | ".join(all_inputs)
        else:
            status_text = "No inputs active"
        
        # Update the label
        self.input_status.config(text=status_text)

    def queue_update(self, update_type, data, *args):
        self.update_queue.put((update_type, data, args))

    def process_updates(self):
        try:
            while not self.update_queue.empty():
                update_type, data, args = self.update_queue.get_nowait()
                
                if update_type == 'button':
                    button, is_pressed = data
                    self.update_button_state(button, is_pressed)
                elif update_type == 'battery':
                    self.update_battery_status(data)
                elif update_type == 'battery_warning':
                    # Flash the battery indicator red for low battery
                    self.battery_value.config(fg='#e74c3c')
                    self.root.bell()  # Optional: Make a sound for low battery
                elif update_type == 'battery_status':
                    # Update charging status
                    if data == 'charging':
                        self.battery_value.config(fg='#2ecc71')
                    else:  # discharging
                        # Revert to normal color based on level
                        self.update_battery_status(self.controller.battery)
                elif update_type == 'connection':
                    self.update_connection_status(data)
                elif update_type == 'error':
                    self.status_label.config(text=f"Error: {data}", fg='red')
                    self.is_running = False
                elif update_type == 'status':
                    self.status_label.config(text=data, fg=args[0])
        except:
            pass
        finally:
            # Schedule the next update
            if self.is_running:
                self.root.after(10, self.process_updates)

    def update_battery_status(self, battery_data):
        try:
            # Parse battery data
            level = battery_data.level_percentage
            is_full = battery_data.full
            is_charging = battery_data.charging
            
            # Determine color based on battery level
            if is_charging:
                color = '#2ecc71'  # Green for charging
            elif level > 50:
                color = '#2ecc71'  # Green for good battery
            elif level > 20:
                color = '#f1c40f'  # Yellow for medium battery
            else:
                color = '#e74c3c'  # Red for low battery
            
            # Create status text
            status = []
            status.append(f"{level}%")
            if is_charging:
                status.append("⚡")  # Lightning bolt for charging
            if is_full:
                status.append("(Full)")
            
            # Update the value label only
            self.battery_value.config(
                text=" ".join(status),
                fg=color
            )
        except:
            self.battery_value.config(
                text="Unknown",
                fg='gray'
            )

    def update_connection_status(self, connection_type):
        try:
            # Get the first value from the tuple
            conn_type = connection_type[0] if isinstance(connection_type, tuple) else connection_type
            
            # Determine connection type and icon
            if conn_type == 'Bluetooth':
                icon = "🔵"  # Blue circle for Bluetooth
                text = "Bluetooth"
                color = '#3498db'  # Blue color
            elif conn_type == 'USB':
                icon = "🔌"  # Electric plug for USB
                text = "USB"
                color = '#2ecc71'  # Green color
            else:
                icon = "❓"  # Question mark for unknown
                text = "Unknown"
                color = 'gray'
            
            # Update the value label only
            self.connection_value.config(
                text=f"{icon} {text}",
                fg=color
            )
        except:
            self.connection_value.config(
                text="Unknown",
                fg='gray'
            )

    def start_rumble(self):
        if self.controller:
            self.rumble_active = True  # Set state to active
            self.controller.left_rumble.set(255)
            self.controller.right_rumble.set(255)

    def stop_rumble(self):
        if self.controller:
            self.rumble_active = False  # Set state to inactive
            self.controller.left_rumble.set(0)
            self.controller.right_rumble.set(0)

    def choose_color(self):
        # Open color picker
        color = tk.colorchooser.askcolor(title="Choose Lightbar Color")
        if color[0]:  # color[0] contains RGB values, color[1] contains hex
            r, g, b = [int(x) for x in color[0]]
            # Update controller lightbar
            if self.controller:
                self.controller.lightbar.set_color(r, g, b)
            # Update preview color
            self.color_preview.configure(bg=color[1])

    def apply_left_trigger(self):
        if self.controller:
            # Ensure rumble is off
            if self.rumble_active:
                self.stop_rumble()
            effect_func = self.trigger_effects[self.trigger_var.get()]
            effect_func(self.controller.left_trigger)

    def apply_right_trigger(self):
        if self.controller:
            # Ensure rumble is off
            if self.rumble_active:
                self.stop_rumble()
            effect_func = self.trigger_effects[self.trigger_var.get()]
            effect_func(self.controller.right_trigger)

    def apply_led_settings(self):
        if self.controller:
            # Apply brightness first
            brightness_func = self.brightness_patterns[self.brightness_var.get()]
            brightness_func(self.controller)
            
            # Then apply LED pattern
            pattern_func = self.led_patterns[self.led_var.get()]
            pattern_func(self.controller)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.iconbitmap(self.resource_path("icon.ico"))
        self.root.mainloop()

    def on_closing(self):
        # Show message box
        tk.messagebox.showinfo(
            "Controller Reset",
            "Disconnect your controller to reset the changes :)",
            parent=self.root
        )
        
        # Clean up and close
        self.is_running = False
        if self.controller:
            self.controller.deactivate()
        self.root.destroy()

    def open_github(self):
        import webbrowser
        webbrowser.open('http://github.com/aneeskhan47')

if __name__ == "__main__":
    app = DualSenseGUI()
    app.run()