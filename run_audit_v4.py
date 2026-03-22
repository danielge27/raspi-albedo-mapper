# run_audit_v2.py
# GUI version with live camera view, capture, and audit processing
# Optimized for Raspberry Pi 4B

import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import os
import time
from datetime import datetime

# Import your existing modules
from surface_detector import detect_surfaces
from report_generator import generate_full_report


class AuditGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Albedo mapper - by Cubeagle from SHS 2026")
        self.root.geometry("1600x1000")
        self.root.configure(bg="#1a1a2e")
        
        # State variables
        self.cap = None
        self.is_live = True
        self.captured_frame = None
        self.captured_image_path = None
        self.output_images = []
        self.camera_running = False
        self.use_picamera2 = False
        self.picam2 = None
        
        # Setup UI
        self.setup_ui()
        
        # Start camera after UI is ready
        self.root.after(500, self.start_camera)
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Albedo mapper - by Cubeagle, SHS, 2026",
            font=("Helvetica", 20, "bold"),
            fg="#e94560",
            bg="#1a1a2e"
        )
        title_label.pack(pady=(0, 10))
        
        # Video/Image display frame
        self.display_frame = tk.Frame(main_frame, bg="#0f0f23", relief=tk.RIDGE, bd=2)
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for video/image
        self.canvas = tk.Label(
            self.display_frame, 
            bg="#0f0f23", 
            text="Starting camera...", 
            fg="#ffffff", 
            font=("Helvetica", 14)
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status overlay label (for showing progress)
        self.status_label = tk.Label(
            self.display_frame,
            text="",
            font=("Helvetica", 12, "bold"),
            fg="#00ff88",
            bg="#0f0f23"
        )
        self.status_label.place(relx=0.5, rely=0.08, anchor="center")
        
        # Progress bar (hidden initially)
        self.progress_frame = tk.Frame(self.display_frame, bg="#0f0f23")
        self.progress = ttk.Progressbar(
            self.progress_frame, 
            mode='indeterminate',
            length=250
        )
        self.progress.pack(pady=10)
        self.progress_text = tk.Label(
            self.progress_frame,
            text="",
            font=("Helvetica", 11),
            fg="#ffffff",
            bg="#0f0f23"
        )
        self.progress_text.pack()
        
        # Neighborhood name input
        input_frame = tk.Frame(main_frame, bg="#1a1a2e")
        input_frame.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(
            input_frame,
            text="Output file name:",
            font=("Helvetica", 11),
            fg="#ffffff",
            bg="#1a1a2e"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.neighborhood_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 11),
            width=25,
            bg="#16213e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.neighborhood_entry.insert(0, "Captured Location")
        self.neighborhood_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#1a1a2e")
        button_frame.pack(fill=tk.X, pady=10)
        
        # Capture button
        self.capture_btn = tk.Button(
            button_frame,
            text="CAPTURE",
            font=("Helvetica", 12, "bold"),
            bg="#e94560",
            fg="#ffffff",
            activebackground="#ff6b6b",
            activeforeground="#ffffff",
            width=12,
            height=2,
            command=self.capture_image
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Calculate button (grayed out initially)
        self.calculate_btn = tk.Button(
            button_frame,
            text="CALCULATE",
            font=("Helvetica", 12, "bold"),
            bg="#555555",
            fg="#888888",
            disabledforeground="#888888",
            width=12,
            height=2,
            state=tk.DISABLED,
            command=self.run_calculation
        )
        self.calculate_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Reset button
        self.reset_btn = tk.Button(
            button_frame,
            text="RESET",
            font=("Helvetica", 12, "bold"),
            bg="#16213e",
            fg="#ffffff",
            activebackground="#1a1a2e",
            activeforeground="#ffffff",
            width=12,
            height=2,
            command=self.reset_to_live
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Results navigation (hidden initially)
        self.nav_frame = tk.Frame(main_frame, bg="#1a1a2e")
        self.current_output_idx = 0
        
        self.prev_btn = tk.Button(
            self.nav_frame,
            text="< Prev",
            font=("Helvetica", 11),
            bg="#16213e",
            fg="#ffffff",
            command=self.show_prev_output
        )
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        self.output_label = tk.Label(
            self.nav_frame,
            text="",
            font=("Helvetica", 11),
            fg="#ffffff",
            bg="#1a1a2e"
        )
        self.output_label.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = tk.Button(
            self.nav_frame,
            text="Next >",
            font=("Helvetica", 11),
            bg="#16213e",
            fg="#ffffff",
            command=self.show_next_output
        )
        self.next_btn.pack(side=tk.LEFT, padx=10)
    
    def start_camera(self):
        """Initialize and start the camera feed - tries multiple methods for RPi"""
        print("Attempting to start camera...")
        
        # Method 1: Try picamera2 (recommended for RPi)
        if self.try_picamera2():
            print("Using picamera2")
            self.use_picamera2 = True
            self.camera_running = True
            self.update_frame_picamera2()
            return
        
        # Method 2: Try OpenCV with different backends and indices
        if self.try_opencv_camera():
            print("Using OpenCV")
            self.use_picamera2 = False
            self.camera_running = True
            self.update_frame()
            return
        
        # Method 3: Try libcamera directly via OpenCV
        if self.try_libcamera():
            print("Using libcamera via OpenCV")
            self.use_picamera2 = False
            self.camera_running = True
            self.update_frame()
            return
        
        # No camera found
        self.canvas.configure(
            text="Camera not found!\n\nTry:\n"
                 "1. sudo raspi-config -> Interface -> Camera -> Enable\n"
                 "2. Reboot\n"
                 "3. Check cable connection",
            fg="#ff6b6b"
        )
        messagebox.showerror(
            "Camera Error", 
            "Could not open camera.\n\n"
            "Please check:\n"
            "1. Camera is enabled in raspi-config\n"
            "2. Camera cable is properly connected\n"
            "3. Run: sudo apt install python3-picamera2"
        )
    
    def try_picamera2(self):
        """Try to use picamera2 (best for RPi camera module)"""
        try:
            from picamera2 import Picamera2
            
            self.picam2 = Picamera2()
            
            # Get camera's maximum resolution
            camera_properties = self.picam2.camera_properties
            max_resolution = camera_properties.get('PixelArraySize', (1920, 1080))
            print(f"Camera max resolution: {max_resolution}")
            
            # Store max resolution for captures
            self.max_resolution = max_resolution
            
            # Use a high resolution for live view (can be same as max or slightly lower for performance)
            # For smooth live view, we use a reasonable high resolution
            live_width = min(max_resolution[0], 1920)  # Cap at 1920 for live view performance
            live_height = min(max_resolution[1], 1080)
            
            print(f"Live view resolution: {live_width}x{live_height}")
            
            # Configure for preview with high resolution
            config = self.picam2.create_preview_configuration(
                main={"size": (live_width, live_height), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            
            # Wait for camera to warm up
            time.sleep(1)
            
            # Test capture
            frame = self.picam2.capture_array()
            if frame is not None and frame.size > 0:
                print(f"picamera2 initialized: {frame.shape}")
                return True
            
        except ImportError:
            print("picamera2 not installed")
        except Exception as e:
            print(f"picamera2 error: {e}")
            if self.picam2:
                try:
                    self.picam2.stop()
                except:
                    pass
                self.picam2 = None
        
        return False
    
    def try_opencv_camera(self):
        """Try OpenCV with various camera indices and backends"""
        # Try different camera indices
        for idx in [0, 1, -1]:
            # Try different backends
            backends = [
                cv2.CAP_V4L2,      # Video4Linux2 (best for RPi)
                cv2.CAP_ANY,       # Auto-detect
            ]
            
            for backend in backends:
                try:
                    print(f"Trying OpenCV camera {idx} with backend {backend}")
                    self.cap = cv2.VideoCapture(idx, backend)
                    
                    if self.cap.isOpened():
                        # Set resolution
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_FPS, 30)
                        
                        # Wait and try to read
                        time.sleep(0.5)
                        
                        for _ in range(5):
                            ret, frame = self.cap.read()
                            if ret and frame is not None and frame.size > 0:
                                print(f"OpenCV camera {idx} working: {frame.shape}")
                                return True
                            time.sleep(0.1)
                    
                    self.cap.release()
                    
                except Exception as e:
                    print(f"OpenCV error: {e}")
                    if self.cap:
                        self.cap.release()
        
        self.cap = None
        return False
    
    def try_libcamera(self):
        """Try libcamera via GStreamer pipeline"""
        try:
            # GStreamer pipeline for libcamera
            gst_pipeline = (
                "libcamerasrc ! "
                "video/x-raw,width=640,height=480,framerate=30/1 ! "
                "videoconvert ! "
                "appsink"
            )
            
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if self.cap.isOpened():
                time.sleep(0.5)
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    print(f"libcamera working: {frame.shape}")
                    return True
            
            self.cap.release()
            
        except Exception as e:
            print(f"libcamera error: {e}")
            if self.cap:
                self.cap.release()
        
        self.cap = None
        return False
    
    def update_frame_picamera2(self):
        """Update display with picamera2 frame"""
        if self.is_live and self.picam2 is not None and self.camera_running:
            try:
                frame = self.picam2.capture_array()
                if frame is not None:
                    self.display_image(frame, is_rgb=True)
            except Exception as e:
                print(f"Frame capture error: {e}")
            
            self.root.after(33, self.update_frame_picamera2)  # ~30 fps
    
    def update_frame(self):
        """Update the display with OpenCV camera feed"""
        if self.is_live and self.cap is not None and self.cap.isOpened() and self.camera_running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.display_image(frame, is_rgb=False)
            
            self.root.after(33, self.update_frame)  # ~30 fps
    
    def display_image(self, frame, is_rgb=False):
        """Display an image/frame on the canvas"""
        try:
            # Convert BGR to RGB if needed
            if not is_rgb and len(frame.shape) == 3 and frame.shape[2] == 3:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame_rgb = frame
            
            # Convert to PIL Image
            img = Image.fromarray(frame_rgb)
            
            # Resize to fit canvas while maintaining aspect ratio
            canvas_width = 1500
            canvas_height = 800
            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update canvas
            self.canvas.configure(image=photo, text="")
            self.canvas.image = photo  # Keep reference
            
        except Exception as e:
            print(f"Display error: {e}")
    
    def capture_image(self):
        """Capture the current frame at maximum resolution"""
        frame = None
        frame_to_save = None
        
        try:
            if self.use_picamera2 and self.picam2 is not None:
                # Capture at full resolution if available
                if hasattr(self, 'max_resolution'):
                    # Switch to still configuration for max resolution capture
                    self.picam2.stop()
                    still_config = self.picam2.create_still_configuration(
                        main={"size": self.max_resolution, "format": "RGB888"}
                    )
                    self.picam2.configure(still_config)
                    self.picam2.start()
                    time.sleep(0.5)  # Let camera adjust
                    
                    frame = self.picam2.capture_array()
                    print(f"Captured at max resolution: {frame.shape if frame is not None else 'None'}")
                    
                    # Switch back to preview configuration
                    self.picam2.stop()
                    live_width = min(self.max_resolution[0], 1920)
                    live_height = min(self.max_resolution[1], 1080)
                    preview_config = self.picam2.create_preview_configuration(
                        main={"size": (live_width, live_height), "format": "RGB888"}
                    )
                    self.picam2.configure(preview_config)
                    self.picam2.start()
                else:
                    frame = self.picam2.capture_array()
                
                # Convert RGB to BGR for saving with cv2
                if frame is not None:
                    frame_to_save = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            elif self.cap is not None and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    frame_to_save = frame.copy()
                else:
                    frame = None
            
            if frame is not None and frame_to_save is not None:
                self.is_live = False
                self.captured_frame = frame.copy()
                
                # Save captured image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.captured_image_path = f"captured_{timestamp}.jpg"
                cv2.imwrite(self.captured_image_path, frame_to_save)
                print(f"Saved: {self.captured_image_path} (Resolution: {frame_to_save.shape[1]}x{frame_to_save.shape[0]})")
                
                # Display captured frame
                is_rgb = self.use_picamera2
                self.display_image(frame, is_rgb=is_rgb)
                
                # Update status
                self.status_label.configure(
                    text=f"Captured at {frame_to_save.shape[1]}x{frame_to_save.shape[0]}! Click CALCULATE.",
                    fg="#00ff88"
                )
                
                # Enable calculate button
                self.calculate_btn.configure(
                    state=tk.NORMAL,
                    bg="#00ff88",
                    fg="#000000"
                )
                
                # Update capture button
                self.capture_btn.configure(
                    text="RE-CAPTURE",
                    bg="#ff9f43"
                )
            else:
                messagebox.showwarning("Warning", "Could not capture frame!")
                
        except Exception as e:
            print(f"Capture error: {e}")
            messagebox.showerror("Error", f"Capture failed: {e}")
    
    def run_calculation(self):
        """Run the surface detection and report generation"""
        if self.captured_image_path is None:
            messagebox.showwarning("Warning", "Please capture an image first!")
            return
        
        # Disable buttons during processing
        self.calculate_btn.configure(state=tk.DISABLED, bg="#555555")
        self.capture_btn.configure(state=tk.DISABLED)
        self.reset_btn.configure(state=tk.DISABLED)
        
        # Show progress overlay
        self.progress_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.progress.start(10)
        
        # Run in separate thread
        thread = threading.Thread(target=self.process_audit)
        thread.start()
    
    def process_audit(self):
        """Process the audit (runs in background thread)"""
        try:
            neighborhood_name = self.neighborhood_entry.get() or "Captured Location"
            
            # Update progress
            self.root.after(0, lambda: self.update_progress("Detecting surfaces..."))
            
            # Detect surfaces
            original, annotated, results, total_px = detect_surfaces(
                self.captured_image_path
            )
            
            # Update progress
            self.root.after(0, lambda: self.update_progress("Analyzing coverage..."))
            
            # Print summary
            print(f"\nSurface Coverage for {neighborhood_name}:")
            for name, data in sorted(
                results.items(),
                key=lambda x: x[1]["coverage_pct"],
                reverse=True
            ):
                if data["coverage_pct"] > 1:
                    bar = "#" * int(data["coverage_pct"] / 2)
                    print(f"   {data['label']:<25}"
                          f" {data['coverage_pct']:>5.1f}%  {bar}")
            
            # Update progress
            self.root.after(0, lambda: self.update_progress("Generating report..."))
            
            # Generate report
            report_path = generate_full_report(
                self.captured_image_path,
                annotated,
                original,
                results,
                neighborhood_name
            )
            
            print(f"\nDone! Report: {report_path}\n")
            
            # Store output images for display
            self.output_images = []
            
            # First priority: Load the report PNG directly
            if report_path:
                # Check if report_path itself is a PNG
                if report_path.endswith('.png'):
                    report_img = cv2.imread(report_path)
                    if report_img is not None:
                        report_name = os.path.basename(report_path)
                        self.output_images.append((f"Report: {report_name}", report_img))
                
                # Also check for other report images in same directory
                output_dir = os.path.dirname(report_path)
                if os.path.exists(output_dir):
                    for f in sorted(os.listdir(output_dir)):
                        if f.endswith(('.png', '.jpg', '.jpeg')):
                            img_path = os.path.join(output_dir, f)
                            # Skip if already added as main report
                            if img_path != report_path:
                                img = cv2.imread(img_path)
                                if img is not None:
                                    self.output_images.append((f, img))
            
            # Add annotated image if not already included
            if annotated is not None:
                self.output_images.append(("Annotated Surface Map", annotated))
            
            # Add original for reference
            if original is not None:
                self.output_images.append(("Original Image", original))
            
            # Update UI on main thread
            self.root.after(0, self.show_results)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def update_progress(self, text):
        """Update progress text"""
        self.progress_text.configure(text=text)
        self.status_label.configure(text=text)
    
    def show_results(self):
        """Display the results"""
        # Hide progress
        self.progress.stop()
        self.progress_frame.place_forget()
        
        # Update status
        self.status_label.configure(
            text="Analysis Complete!",
            fg="#00ff88"
        )
        
        # Show first output image
        if self.output_images:
            self.current_output_idx = 0
            self.display_output_image()
            
            # Show navigation if multiple outputs
            if len(self.output_images) > 1:
                self.nav_frame.pack(fill=tk.X, pady=10)
                self.update_nav_label()
        
        # Re-enable buttons
        self.capture_btn.configure(state=tk.NORMAL)
        self.reset_btn.configure(state=tk.NORMAL)
        self.calculate_btn.configure(
            text="DONE",
            bg="#00ff88",
            fg="#000000",
            state=tk.DISABLED
        )
    
    def display_output_image(self):
        """Display current output image"""
        if 0 <= self.current_output_idx < len(self.output_images):
            name, img = self.output_images[self.current_output_idx]
            self.display_image(img, is_rgb=False)
            self.status_label.configure(text=f"{name}")
    
    def update_nav_label(self):
        """Update navigation label"""
        self.output_label.configure(
            text=f"Image {self.current_output_idx + 1} of {len(self.output_images)}"
        )
    
    def show_prev_output(self):
        """Show previous output image"""
        if self.current_output_idx > 0:
            self.current_output_idx -= 1
            self.display_output_image()
            self.update_nav_label()
    
    def show_next_output(self):
        """Show next output image"""
        if self.current_output_idx < len(self.output_images) - 1:
            self.current_output_idx += 1
            self.display_output_image()
            self.update_nav_label()
    
    def show_error(self, error_msg):
        """Show error message"""
        self.progress.stop()
        self.progress_frame.place_forget()
        
        self.status_label.configure(
            text=f"Error: {error_msg[:50]}...",
            fg="#ff6b6b"
        )
        
        # Re-enable buttons
        self.capture_btn.configure(state=tk.NORMAL)
        self.reset_btn.configure(state=tk.NORMAL)
        self.calculate_btn.configure(state=tk.NORMAL, bg="#00ff88")
        
        messagebox.showerror("Processing Error", error_msg)
    
    def reset_to_live(self):
        """Reset to live camera view"""
        self.is_live = True
        self.captured_frame = None
        self.output_images = []
        self.current_output_idx = 0
        
        # Hide navigation
        self.nav_frame.pack_forget()
        
        # Reset status
        self.status_label.configure(text="", fg="#00ff88")
        
        # Reset buttons
        self.capture_btn.configure(
            text="CAPTURE",
            bg="#e94560",
            state=tk.NORMAL
        )
        self.calculate_btn.configure(
            text="CALCULATE",
            bg="#555555",
            fg="#888888",
            state=tk.DISABLED
        )
        
        # Restart camera feed
        if self.use_picamera2:
            self.update_frame_picamera2()
        else:
            self.update_frame()
    
    def on_closing(self):
        """Clean up on window close"""
        self.camera_running = False
        
        if self.cap is not None:
            self.cap.release()
        
        if self.picam2 is not None:
            try:
                self.picam2.stop()
            except:
                pass
        
        self.root.destroy()


# ── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = AuditGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
