import customtkinter as ctk
import threading
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.image_scraper import ImageScraper
from tkinter import filedialog

class ModernImageScraperApp:
    def __init__(self):
        # Set theme and color settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize main window
        self.window = ctk.CTk()
        self.window.title("Web Image Scraper - Modern UI")
        self.window.geometry("1200x800")
        
        # Initialize scraper with callbacks
        self.scraper = ImageScraper(
            log_callback=self.log_message,
            progress_callback=self.update_progress
        )
        
        # Track state
        self.last_url = None
        self.total_images = 0
        self.download_thread = None
        
        # Create main layout
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Create header first
        self.create_header()
        
        # Main container for content
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create main content area
        self.create_main_content()
        
        # Create right panel for advanced settings
        self.create_right_panel()
        
    def create_header(self):
        """Create the header section with title and theme switch"""
        header_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        # Left side - Title
        title = ctk.CTkLabel(
            header_frame,
            text="Web Image Scraper",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # Right side - Controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right", padx=10)
        
        # Theme switch
        self.theme_switch = ctk.CTkButton(
            controls_frame,
            text="🌙",  # Moon emoji for dark mode
            width=30,
            command=self.toggle_theme
        )
        self.theme_switch.pack(side="right", padx=5)
        
        # Advanced Settings Switch
        self.advanced_switch = ctk.CTkSwitch(
            controls_frame,
            text="Advanced",
            command=self.toggle_advanced_panel,
            width=40
        )
        self.advanced_switch.pack(side="right", padx=10)
        
    def create_main_content(self):
        # Create left and right panes
        self.create_panes()
        
    def create_panes(self):
        # Create left pane
        self.left_pane = ctk.CTkFrame(self.main_container)
        self.left_pane.pack(side="left", fill="both", expand=True)
        
        # Create right pane (advanced settings)
        self.right_pane = ctk.CTkFrame(self.main_container)
        self.right_pane.pack_forget()  # Hide initially
        
        # URL Input Section
        self.create_url_section()
        
        # Console Output
        self.create_console()
        
        # Create advanced settings content
        self.create_advanced_settings()
        
    def create_right_panel(self):
        pass
        
    def create_url_section(self):
        url_frame = ctk.CTkFrame(self.left_pane)
        url_frame.pack(fill="x", pady=(0, 20))
        
        # Website URL Section
        url_label = ctk.CTkLabel(
            url_frame,
            text="Website URL",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        url_label.pack(anchor="w", pady=(10, 5))
        
        input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 10))
        
        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter website URL",
            height=40
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(side="right")
        
        self.check_button = ctk.CTkButton(
            button_frame,
            text="Check Images",
            command=self.check_images,
            height=40
        )
        self.check_button.pack(side="left", padx=(0, 10))
        
        self.download_button = ctk.CTkButton(
            button_frame,
            text="Download",
            command=self.start_download,
            height=40,
            state="disabled"
        )
        self.download_button.pack(side="left")
        
        # Download Location Section
        location_label = ctk.CTkLabel(
            url_frame,
            text="Download Location",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        location_label.pack(anchor="w", pady=(20, 5))
        
        location_input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        location_input_frame.pack(fill="x", pady=(0, 10))
        
        self.location_entry = ctk.CTkEntry(
            location_input_frame,
            placeholder_text="Select download folder",
            height=40
        )
        self.location_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_button = ctk.CTkButton(
            location_input_frame,
            text="Browse",
            command=self.browse_location,
            height=40
        )
        browse_button.pack(side="right")
        
        # Progress bar
        self.progress_frame = ctk.CTkFrame(url_frame)
        self.progress_frame.pack(fill="x", pady=(10, 0))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(anchor="w", pady=(0, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
    def create_console(self):
        console_frame = ctk.CTkFrame(self.left_pane)
        console_frame.pack(fill="both", expand=True)
        
        console_label = ctk.CTkLabel(
            console_frame,
            text="Console Output",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        console_label.pack(anchor="w", pady=(10, 5))
        
        self.console = ctk.CTkTextbox(
            console_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.console.pack(fill="both", expand=True, pady=(0, 10))
        
    def create_advanced_settings(self):
        # Advanced Settings Header
        advanced_label = ctk.CTkLabel(
            self.right_pane,
            text="Advanced Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_label.pack(anchor="w", pady=(0, 20))
        
        # File types section
        types_label = ctk.CTkLabel(
            self.right_pane,
            text="Image Types",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        types_label.pack(anchor="w", pady=(0, 5))
        
        # Checkboxes for file types
        types_frame = ctk.CTkFrame(self.right_pane)
        types_frame.pack(fill="x", pady=(0, 20))
        
        self.file_types = {}
        for type_name in ['JPG/JPEG', 'PNG', 'SVG', 'WebP']:
            var = ctk.BooleanVar(value=True)
            self.file_types[type_name] = var
            checkbox = ctk.CTkCheckBox(
                types_frame,
                text=type_name,
                variable=var
            )
            checkbox.pack(anchor="w", padx=10, pady=5)
        
        # Size Filters
        size_label = ctk.CTkLabel(
            self.right_pane,
            text="Size Filters (KB)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        size_label.pack(anchor="w", pady=(0, 5))
        
        size_frame = ctk.CTkFrame(self.right_pane)
        size_frame.pack(fill="x", pady=(0, 20))
        
        # Min size
        min_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        min_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(min_frame, text="Min:").pack(side="left", padx=10)
        self.min_size = ctk.CTkEntry(
            min_frame,
            width=100,
            placeholder_text="0"
        )
        self.min_size.pack(side="left", padx=10)
        
        # Max size
        max_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        max_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(max_frame, text="Max:").pack(side="left", padx=10)
        self.max_size = ctk.CTkEntry(
            max_frame,
            width=100,
            placeholder_text="No limit"
        )
        self.max_size.pack(side="left", padx=10)
        
    def toggle_advanced_panel(self):
        if self.right_pane.winfo_ismapped():
            self.right_pane.pack_forget()
        else:
            self.right_pane.pack(side="right", fill="y", padx=(20, 0))
            
    def check_images(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log_message("Please enter a website URL", "error")
            return
            
        # Disable UI elements
        self.check_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.log_message("Checking website for images...", "info")
        
        def check_thread():
            try:
                # Only scan if URL has changed
                if url != self.last_url:
                    self.total_images = self.scraper.scan_webpage(url)
                    self.last_url = url
                
                if self.total_images > 0:
                    self.log_message(f"Found {self.total_images} images on the website", "success")
                    self.download_button.configure(state="normal")
                else:
                    self.log_message("No images found on the website", "warning")
                    self.download_button.configure(state="disabled")
                    
            except Exception as e:
                self.log_message(f"Error checking website: {str(e)}", "error")
                self.download_button.configure(state="disabled")
            finally:
                # Re-enable UI elements
                self.check_button.configure(state="normal")
                self.url_entry.configure(state="normal")
        
        # Start check in separate thread
        threading.Thread(target=check_thread, daemon=True).start()
        
    def start_download(self):
        url = self.url_entry.get().strip()
        save_location = self.location_entry.get().strip()
        
        if not url:
            self.log_message("Please enter a website URL", "error")
            return
            
        if not save_location:
            self.log_message("Please select a save location", "error")
            return
            
        if not os.path.exists(save_location):
            try:
                os.makedirs(save_location)
            except Exception as e:
                self.log_message(f"Error creating save directory: {str(e)}", "error")
                return
        
        # Get selected file types
        allowed_types = []
        for file_type, var in self.file_types.items():
            if var.get():
                if file_type == 'JPG/JPEG':
                    allowed_types.extend(['jpg', 'jpeg'])
                else:
                    allowed_types.append(file_type.lower())
                    
        if not allowed_types:
            self.log_message("Please select at least one file type", "error")
            return
            
        # Get size filters
        try:
            min_size = int(self.min_size.get() or 0) * 1024  # Convert to bytes
            max_size = int(self.max_size.get() or 0) * 1024  # Convert to bytes
            if max_size == 0:
                max_size = float('inf')
        except ValueError:
            self.log_message("Please enter valid numbers for size filters", "error")
            return
        
        # Update UI
        self.download_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.location_entry.configure(state="disabled")
        self.progress_label.configure(text="Downloading...")
        self.progress_bar.set(0)
        
        def download_thread():
            try:
                # Start download using existing scan results
                self.scraper.start_download(
                    url=url,
                    save_location=save_location,
                    allowed_types=allowed_types,
                    min_size=min_size,
                    max_size=max_size
                )
            except Exception as e:
                self.log_message(f"Error during download: {str(e)}", "error")
            finally:
                # Reset UI
                self.download_button.configure(state="normal")
                self.check_button.configure(state="normal")
                self.url_entry.configure(state="normal")
                self.location_entry.configure(state="normal")
                self.progress_label.configure(text="")
                self.progress_bar.set(0)
        
        # Start download in separate thread
        threading.Thread(target=download_thread, daemon=True).start()
        
    def log_message(self, message, level="info"):
        color_map = {
            "error": "red",
            "success": "green",
            "warning": "orange",
            "info": "white"
        }
        
        self.console.insert("end", f"{message}\n", color_map.get(level, "white"))
        self.console.see("end")
        
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="☀️")  # Sun emoji for light mode
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="🌙")  # Moon emoji for dark mode
            
    def browse_location(self):
        folder = filedialog.askdirectory()
        if folder:
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, folder)
            
    def update_progress(self, progress):
        self.progress_bar.set(progress)
        
    def run(self):
        self.window.mainloop()

def main():
    app = ModernImageScraperApp()
    app.run()

if __name__ == "__main__":
    main()
