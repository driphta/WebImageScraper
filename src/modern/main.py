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
        
        # Initialize scraper
        self.scraper = ImageScraper(self.log_message)
        self.setup_ui()
        
    def setup_ui(self):
        # Create main container with padding
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with theme toggle
        self.create_header()
        
        # Create left and right panes
        self.create_panes()
        
    def create_panes(self):
        # Create paned window for left and right sections
        self.paned_window = ctk.CTkFrame(self.main_container)
        self.paned_window.pack(fill="both", expand=True, pady=(20, 0))
        
        # Left pane - Main controls
        self.left_pane = ctk.CTkFrame(self.paned_window)
        self.left_pane.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # URL Input Section
        self.create_url_section()
        
        # Settings Section
        self.create_settings_section()
        
        # Console Output
        self.create_console()
        
        # Right pane - Advanced settings
        self.right_pane = ctk.CTkFrame(self.paned_window)
        self.right_pane.pack(side="right", fill="both", padx=(10, 0))
        
        # Advanced Settings
        self.create_advanced_settings()
        
    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 4))  # Reduced bottom padding
        
        # Left side - Title and subtitle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        title = ctk.CTkLabel(
            title_frame, 
            text="Web Image Scraper",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="top", anchor="w")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Download images from any website",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(side="top", anchor="w", pady=(0, 0))  # Reduced bottom padding
        
        # Right side - Theme toggle
        theme_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_frame.pack(side="right")
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.select() if ctk.get_appearance_mode() == "dark" else self.theme_switch.deselect()
        self.theme_switch.pack(side="right", padx=10)
        
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
        
    def create_settings_section(self):
        self.settings_frame = ctk.CTkFrame(self.left_pane)
        self.settings_frame.pack(fill="x", pady=(0, 20))
        
        # File types section
        types_label = ctk.CTkLabel(
            self.settings_frame,
            text="Image Types",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        types_label.pack(anchor="w", pady=(10, 5))
        
        # Checkboxes for file types in one row
        self.file_types = {}
        types_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        types_frame.pack(fill="x", pady=(0, 10))
        
        for i, type_name in enumerate(['JPG/JPEG', 'PNG', 'SVG', 'WebP']):
            var = ctk.BooleanVar(value=True)
            self.file_types[type_name] = var
            checkbox = ctk.CTkCheckBox(
                types_frame,
                text=type_name,
                variable=var
            )
            checkbox.grid(row=0, column=i, padx=10, pady=5, sticky="w")
            
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
        advanced_label.pack(anchor="w", pady=(10, 20))
        
        # Size Filters
        size_frame = ctk.CTkFrame(self.right_pane)
        size_frame.pack(fill="x", pady=(0, 10))
        
        size_label = ctk.CTkLabel(
            size_frame,
            text="Size Filters (KB)",
            font=ctk.CTkFont(size=14)
        )
        size_label.pack(anchor="w", pady=(5, 10))
        
        # Min size
        min_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        min_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(min_frame, text="Min:").pack(side="left")
        self.min_size = ctk.CTkEntry(min_frame, width=100)
        self.min_size.pack(side="left", padx=10)
        
        # Max size
        max_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        max_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(max_frame, text="Max:").pack(side="left")
        self.max_size = ctk.CTkEntry(max_frame, width=100)
        self.max_size.pack(side="left", padx=10)
        
    def check_images(self):
        url = self.url_entry.get()
        if not url:
            self.log_message("Please enter a valid URL", "error")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.check_button.configure(state="disabled")
        
        def scan_thread():
            try:
                image_count = self.scraper.scan_webpage(url)
                self.window.after(0, lambda: self._after_scan(image_count))
            except Exception as e:
                self.window.after(0, lambda: self.log_message(f"Error scanning webpage: {str(e)}", "error"))
                self.window.after(0, lambda: self._after_scan(0))
        
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def _after_scan(self, image_count):
        self.check_button.configure(state="normal")
        if image_count > 0:
            self.log_message(f"Found {image_count} images", "success")
            self.download_button.configure(state="normal")
        else:
            self.log_message("No images found", "warning")
            
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
        new_mode = self.theme_switch.get()
        ctk.set_appearance_mode(new_mode)
        
    def browse_location(self):
        folder = filedialog.askdirectory()
        if folder:
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, folder)
            
    def start_download(self):
        if not self.location_entry.get():
            self.log_message("Please select a download location", "error")
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
            min_size = int(self.min_size.get()) if self.min_size.get() else 0
            max_size = int(self.max_size.get()) if self.max_size.get() else float('inf')
        except ValueError:
            self.log_message("Please enter valid numbers for size filters", "error")
            return
            
        self.download_button.configure(state="disabled")
        self.check_button.configure(state="disabled")
        self.progress_label.configure(text="Downloading...")
        
        def update_progress(value):
            self.window.after(0, lambda: self._update_progress(value))
            
        def download_thread():
            error_message = None
            try:
                self.scraper.download_images(
                    self.location_entry.get(),
                    allowed_types,
                    update_progress,
                    min_size=min_size,
                    max_size=max_size
                )
            except Exception as e:
                error_message = str(e)
            finally:
                def cleanup():
                    if error_message:
                        self.log_message(f"Error during download: {error_message}", "error")
                    self._after_download()
                self.window.after(0, cleanup)
                
        threading.Thread(target=download_thread, daemon=True).start()
        
    def _update_progress(self, value):
        self.progress_bar.set(value / 100)
        self.progress_label.configure(text=f"Downloading... {int(value)}%")
        
    def _after_download(self):
        self.download_button.configure(state="normal")
        self.check_button.configure(state="normal")
        self.progress_label.configure(text="Ready")
        self.progress_bar.set(0)
        
    def run(self):
        self.window.mainloop()

def main():
    app = ModernImageScraperApp()
    app.run()

if __name__ == "__main__":
    main()
