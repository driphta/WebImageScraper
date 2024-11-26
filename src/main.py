import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
from ui.custom_widgets import RoundedFrame, CustomProgressBar, CustomEntry
from core.image_scraper import ImageScraper

class ImageScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Image Scraper")
        self.root.configure(bg='#2b2b2b')
        self.root.state('zoomed')
        
        # Initialize the image scraper
        self.scraper = ImageScraper(self.log_message)
        
        # Configure styles and UI elements
        self.setup_styles()
        self.create_main_layout()
        self.create_header()
        self.create_content_area()
        self.create_console()
        
    def setup_styles(self):
        self.colors = {
            'bg': '#1E1E1E',
            'input_bg': '#333333',
            'fg': '#FFFFFF',
            'secondary_fg': '#86868A',
            'accent': '#0A84FF',
            'button_gradient': ['#0A84FF', '#0077ED']
        }
        
        self.fonts = {
            'header': ('Segoe UI', 20, 'bold'),
            'subheader': ('Segoe UI', 12),
            'body': ('Segoe UI', 12),
            'small': ('Segoe UI', 10)
        }
        
        self.style = ttk.Style()
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['fg'],
                           font=self.fonts['body'])
        
        self.root.option_add('*Button.relief', 'flat')
        self.root.option_add('*Button.borderWidth', '0')
        self.root.option_add('*Button.highlightThickness', '0')
        self.root.option_add('*Button.padX', '20')
        self.root.option_add('*Button.padY', '10')
        self.root.option_add('*Button.Background', self.colors['accent'])
        self.root.option_add('*Button.Foreground', self.colors['fg'])

    def create_main_layout(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky='nsew')
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
    def create_header(self):
        header_frame = ttk.Frame(self.main_container)
        header_frame.grid(row=0, column=0, padx=40, pady=10, sticky='ew')
        
        title_label = ttk.Label(header_frame,
                              text="Web Image Scraper",
                              font=self.fonts['header'],
                              foreground=self.colors['fg'])
        title_label.pack(side=tk.LEFT, padx=(0, 10))
        
        subtitle_label = ttk.Label(header_frame,
                                 text="Download images from any website",
                                 font=self.fonts['subheader'],
                                 foreground=self.colors['secondary_fg'])
        subtitle_label.pack(side=tk.LEFT)
        
    def create_content_area(self):
        # Scrollable content area
        self.content_canvas = tk.Canvas(self.main_container, bg=self.colors['bg'], highlightthickness=0)
        self.content_canvas.grid(row=1, column=0, sticky='nsew', padx=40)
        
        scrollbar = ttk.Scrollbar(self.main_container, orient='vertical', command=self.content_canvas.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        content_frame = ttk.Frame(self.content_canvas)
        self.content_canvas.create_window((0, 0), window=content_frame, anchor='nw')
        
        # URL input section
        self.create_url_input(content_frame)
        
        # Size filter section
        self.create_size_filter(content_frame)
        
        # Progress section
        self.create_progress_section(content_frame)
        
        # Filter section
        self.create_filter_section(content_frame)
        
        # Save location section
        self.create_save_section(content_frame)
        
        # Download button
        self.create_download_button(content_frame)
        
        # Configure scroll region
        content_frame.bind('<Configure>', lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox('all')))
        self.content_canvas.bind('<Configure>', lambda e: self.content_canvas.itemconfig(
            self.content_canvas.find_withtag('all')[0], width=e.width))
        
    def create_url_input(self, parent):
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill=tk.X, padx=15, pady=15)
        
        url_label = ttk.Label(url_frame, text="Website URL")
        url_label.pack(anchor='w', pady=(0, 5))
        
        entry_frame = ttk.Frame(url_frame)
        entry_frame.pack(fill=tk.X)
        
        self.url_entry = CustomEntry(entry_frame, placeholder="Enter website URL")
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=10)
        
        self.check_button = tk.Button(entry_frame,
                                    text="Check Images",
                                    command=self.check_images,
                                    width=12)
        self.check_button.pack(side=tk.RIGHT)
        
    def create_size_filter(self, parent):
        size_frame = ttk.Frame(parent)
        size_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        size_label = ttk.Label(size_frame, text="Size Filter (KB)")
        size_label.pack(anchor='w', pady=(0, 5))
        
        filter_frame = ttk.Frame(size_frame)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Min", font=self.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
        self.min_size = CustomEntry(filter_frame, placeholder="0", width=5)
        self.min_size.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
        ttk.Label(filter_frame, text="Max", font=self.fonts['small']).pack(side=tk.LEFT, padx=(0, 5))
        self.max_size = CustomEntry(filter_frame, placeholder="inf", width=5)
        self.max_size.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
    def create_progress_section(self, parent):
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        progress_header = ttk.Frame(progress_frame)
        progress_header.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_header,
                                    text="Ready",
                                    font=self.fonts['small'])
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(progress_header,
                                      text="0%",
                                      font=self.fonts['small'])
        self.progress_label.pack(side=tk.RIGHT)
        
        self.progress_bar = CustomProgressBar(progress_frame)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
    def create_filter_section(self, parent):
        self.filter_frame = ttk.Frame(parent)
        self.filter_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        self.filter_frame.pack_forget()
        
        filter_label = ttk.Label(self.filter_frame,
                               text="Select Image Types to Download")
        filter_label.pack(anchor='w', pady=(0, 5))
        
        self.checkbox_frame = ttk.Frame(self.filter_frame)
        self.checkbox_frame.pack(fill=tk.X, pady=5)
        
        # Create checkboxes for each file type
        self.file_types = {
            'JPG/JPEG': tk.BooleanVar(value=True),
            'PNG': tk.BooleanVar(value=True),
            'SVG': tk.BooleanVar(value=True),
            'WebP': tk.BooleanVar(value=True)
        }
        
        for i, (file_type, var) in enumerate(self.file_types.items()):
            cb = ttk.Checkbutton(self.checkbox_frame,
                               text=file_type,
                               variable=var)
            cb.grid(row=i//2, column=i%2, padx=10, pady=5, sticky='w')
        
    def create_save_section(self, parent):
        self.save_frame = ttk.Frame(parent)
        self.save_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        self.save_frame.pack_forget()
        
        save_label = ttk.Label(self.save_frame, text="Save Location")
        save_label.pack(anchor='w', pady=(0, 5))
        
        save_entry_frame = ttk.Frame(self.save_frame)
        save_entry_frame.pack(fill=tk.X)
        
        self.save_input = CustomEntry(save_entry_frame, placeholder="Choose save location")
        self.save_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, ipady=10)
        
        self.browse_button = tk.Button(save_entry_frame,
                                     text="Browse",
                                     command=self.browse_folder,
                                     width=12)
        self.browse_button.pack(side=tk.RIGHT)
        
    def create_download_button(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        center_frame = ttk.Frame(button_frame)
        center_frame.pack(expand=True)
        
        self.start_button = tk.Button(center_frame,
                                    text="Start Download",
                                    command=self.start_download,
                                    width=15)
        self.start_button.pack()
        self.start_button.config(state='disabled')
        
    def create_console(self):
        console_frame = ttk.Frame(self.main_container)
        console_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=40, pady=20)
        
        console_label = ttk.Label(console_frame, text="Console Output")
        console_label.pack(anchor='w', pady=(0, 5))
        
        self.console = scrolledtext.ScrolledText(console_frame,
                                               wrap=tk.WORD,
                                               height=12,
                                               font=self.fonts['body'],
                                               bg='#333333',
                                               fg='#FFFFFF',
                                               insertbackground='#FFFFFF',
                                               relief='flat')
        self.console.pack(fill=tk.BOTH, expand=True)
        
        self.console.tag_configure("error", foreground="#FF453A")
        self.console.tag_configure("success", foreground="#32D74B")
        self.console.tag_configure("info", foreground="#0A84FF")
        self.console.tag_configure("debug", foreground="#AAAAAA")
        
    def log_message(self, message, level="info"):
        self.console.insert(tk.END, f"{message}\n", level)
        self.console.see(tk.END)
        
    def check_images(self):
        url = self.url_entry.get()
        if url == self.url_entry.placeholder:
            self.log_message("Please enter a valid URL", "error")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.status_label.config(text="Scanning...")
        self.progress_bar.set_progress(0)
        self.check_button.config(state='disabled')
        
        def scan_thread():
            try:
                image_count = self.scraper.scan_webpage(url)
                
                # Update UI in the main thread
                self.root.after(0, lambda: self._after_scan(image_count))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Error scanning webpage: {str(e)}", "error"))
                self.root.after(0, lambda: self._after_scan(0))
        
        # Start scanning in a separate thread
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def _after_scan(self, image_count):
        """Handle UI updates after scan completes"""
        if image_count > 0:
            self.start_button.config(state='normal')
            self.filter_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
            self.save_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        else:
            self.start_button.config(state='disabled')
            
        self.status_label.config(text="Ready")
        self.progress_bar.set_progress(100)
        self.check_button.config(state='normal')

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_input.delete(0, tk.END)
            self.save_input.insert(0, folder)
            
    def start_download(self):
        if self.scraper.is_downloading:
            self.scraper.is_downloading = False
            self.start_button.config(text="Start Download")
            return
            
        save_location = self.save_input.get()
        if not save_location or save_location == self.save_input.placeholder:
            self.log_message("Please select a save location", "error")
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
            self.log_message("Please select at least one file type to download", "error")
            return
            
        self.start_button.config(text="Stop Download")
        self.check_button.config(state='disabled')
        
        def download_thread():
            try:
                def update_progress(value):
                    self.root.after(0, lambda: self._update_download_progress(value))
                    
                self.scraper.download_images(save_location, allowed_types, update_progress)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Error during download: {str(e)}", "error"))
            finally:
                self.root.after(0, self._after_download)
                
        threading.Thread(target=download_thread, daemon=True).start()
        
    def _update_download_progress(self, value):
        """Update progress bar and label from the main thread"""
        self.progress_bar.set_progress(value)
        self.progress_label.config(text=f"{int(value)}%")
        
    def _after_download(self):
        """Handle UI updates after download completes"""
        self.start_button.config(text="Start Download")
        self.check_button.config(state='normal')
        
def main():
    root = tk.Tk()
    app = ImageScraperApp(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()
