import sys
import os
import requests
import base64
import threading
import time
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse, unquote
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import hashlib
import mimetypes
import http.client
http.client._MAXHEADERS = 1000
from datetime import datetime

class RoundedFrame(ttk.Frame):
    def __init__(self, parent, radius=20, padding=15, background=None, **kwargs):
        super().__init__(parent, padding=padding, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=background)
        self.canvas.pack(fill='both', expand=True)
        
        def round_rectangle(x1, y1, x2, y2, radius=radius, **kwargs):
            points = [
                x1 + radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1
            ]
            return self.canvas.create_polygon(points, smooth=True, **kwargs)
        
        self.round_rectangle = round_rectangle
        self.bind('<Configure>', self._on_resize)
        
    def _on_resize(self, event):
        self.canvas.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        self.round_rectangle(0, 0, width, height, 
                           fill='#262626', outline='#333333')

class CustomProgressBar(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(height=6, bg='#262626', highlightthickness=0)  # Thinner, more Apple-like
        self.progress_rect = None
        self.bind('<Configure>', self._on_resize)
        
    def create_progress_bar(self):
        width = self.winfo_width()
        height = self.winfo_height()
        # Create background rounded rectangle
        self.create_rounded_rect(0, 0, width, height, 3, fill='#333333')
        # Create progress rounded rectangle
        self.progress_rect = self.create_rounded_rect(0, 0, 0, height, 3, fill='#0A84FF')
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def set_progress(self, value):
        if not self.progress_rect:
            self.create_progress_bar()
        width = self.winfo_width()
        height = self.winfo_height()
        progress_width = (value / 100) * width
        # Recreate progress rectangle with new width
        self.delete(self.progress_rect)
        self.progress_rect = self.create_rounded_rect(0, 0, progress_width, height, 3, fill='#0A84FF')
        
    def _on_resize(self, event):
        self.delete("all")
        self.create_progress_bar()

class CustomEntry(tk.Entry):  # Changed from ttk.Entry to tk.Entry
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent,
                        bg='#333333',  # Dark grey background
                        fg='#FFFFFF',  # White text
                        insertbackground='#FFFFFF',  # White cursor
                        relief='flat',
                        highlightthickness=1,
                        highlightbackground='#404040',  # Slightly lighter border
                        highlightcolor='#0A84FF',  # Accent color when focused
                        **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_fg = '#888888'  # Light grey for placeholder
        
        self.insert(0, placeholder)
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
        
        if self.get() == placeholder:
            self.configure(fg=self.placeholder_fg)
    
    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.configure(fg='#FFFFFF')
    
    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg=self.placeholder_fg)

class ImageScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Image Scraper")
        self.root.configure(bg='#2b2b2b')
        self.root.state('zoomed')  # Maximize the window on Windows
        self.is_downloading = False
        self.download_thread = None
        
        # Download statistics
        self.download_start_time = None
        self.bytes_downloaded = 0
        self.total_bytes = 0
        
        # Configure grid weights for root window
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Define colors
        self.colors = {
            'bg': '#1E1E1E',  # Dark background
            'input_bg': '#333333',  # Input background
            'fg': '#FFFFFF',  # White text
            'secondary_fg': '#86868A',  # Secondary text
            'accent': '#0A84FF',  # Apple blue
            'button_gradient': ['#0A84FF', '#0077ED']  # Button gradient
        }
        
        # Configure fonts - SF Pro-inspired (using Segoe UI as fallback)
        self.fonts = {
            'header': ('Segoe UI', 20, 'bold'),  # Reduced from 24
            'subheader': ('Segoe UI', 12),  # Reduced from 16
            'body': ('Segoe UI', 12),
            'small': ('Segoe UI', 10)
        }
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TFrame',
                           background=self.colors['bg'])
        
        self.style.configure('TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['fg'],
                           font=self.fonts['body'])
        
        # Configure entry style
        self.style.configure('Custom.TEntry',
                           fieldbackground=self.colors['input_bg'],
                           foreground=self.colors['fg'],
                           insertcolor=self.colors['fg'])
        
        # Configure the root window background
        self.root.configure(bg=self.colors['bg'])
        
        # Configure button style
        self.root.option_add('*Button.relief', 'flat')
        self.root.option_add('*Button.borderWidth', '0')
        self.root.option_add('*Button.highlightThickness', '0')
        self.root.option_add('*Button.padX', '20')
        self.root.option_add('*Button.padY', '10')
        self.root.option_add('*Button.Background', self.colors['accent'])
        self.root.option_add('*Button.Foreground', self.colors['fg'])
        
        # Main container using grid
        main_container = ttk.Frame(root)
        main_container.grid(row=0, column=0, sticky='nsew')
        main_container.grid_rowconfigure(1, weight=1)  # Content area can expand
        main_container.grid_columnconfigure(0, weight=1)
        
        # Combined header section
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, padx=40, pady=10, sticky='ew')  # Single row for header
        
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
        
        # Content area (scrollable)
        content_canvas = tk.Canvas(main_container, bg=self.colors['bg'], highlightthickness=0)
        content_canvas.grid(row=1, column=0, sticky='nsew', padx=40)  # Moved to row 1
        
        # Add scrollbar to content
        content_scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=content_canvas.yview)
        content_scrollbar.grid(row=1, column=1, sticky='ns')
        content_canvas.configure(yscrollcommand=content_scrollbar.set)
        
        # Frame for scrollable content
        content_frame = RoundedFrame(content_canvas, radius=20, background=self.colors['bg'], padding=30)
        content_canvas.create_window((0, 0), window=content_frame, anchor='nw', width=content_canvas.winfo_width())
        
        # Update scroll region when content size changes
        def configure_scroll_region(event):
            content_canvas.configure(scrollregion=content_canvas.bbox('all'))
        content_frame.bind('<Configure>', configure_scroll_region)
        
        # Update content frame width when canvas resizes
        def on_canvas_resize(event):
            content_canvas.itemconfig(content_canvas.find_withtag('all')[0], width=event.width)
        content_canvas.bind('<Configure>', on_canvas_resize)
        
        # Input section frame
        input_section = ttk.Frame(content_frame.canvas)
        input_section.pack(fill=tk.X, padx=15, pady=15)
        
        # URL input with consistent width
        url_input_frame = ttk.Frame(input_section)
        url_input_frame.pack(fill=tk.X, pady=(0, 15))
        
        url_label = ttk.Label(url_input_frame,
                            text="Website URL",
                            font=self.fonts['body'],
                            foreground=self.colors['fg'])
        url_label.pack(anchor='w', pady=(0, 5))
        
        entry_frame = ttk.Frame(url_input_frame)
        entry_frame.pack(fill=tk.X, padx=10)
        
        self.url_entry = CustomEntry(entry_frame,
                                   placeholder="Enter website URL",
                                   font=self.fonts['body'])
        self.url_entry.configure(background='#333333')  # Force background color
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10), ipady=10)  # Adjusted padding
        
        self.check_button = tk.Button(entry_frame,
                                    text="Check Images",
                                    font=self.fonts['body'],
                                    bg=self.colors['accent'],
                                    fg=self.colors['fg'],
                                    activebackground=self.colors['button_gradient'][1],
                                    activeforeground=self.colors['fg'],
                                    relief='flat',
                                    width=12,
                                    pady=10,
                                    command=self.check_images)
        self.check_button.pack(side=tk.RIGHT, padx=10)
        
        # Size filter section
        size_filter_frame = ttk.Frame(input_section)
        size_filter_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        size_filter_label = ttk.Label(size_filter_frame,
                                    text="Size Filter (KB)",
                                    font=self.fonts['body'],
                                    foreground=self.colors['fg'])
        size_filter_label.pack(anchor='w', pady=(0, 5))
        
        size_filter_entry_frame = ttk.Frame(size_filter_frame)
        size_filter_entry_frame.pack(fill=tk.X, padx=10)
        
        min_size_label = ttk.Label(size_filter_entry_frame,
                                 text="Min",
                                 font=self.fonts['small'],
                                 foreground=self.colors['secondary_fg'])
        min_size_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.min_size = CustomEntry(size_filter_entry_frame,
                                  placeholder="0",
                                  font=self.fonts['small'],
                                  width=5)
        self.min_size.configure(background='#333333')  # Force background color
        self.min_size.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
        max_size_label = ttk.Label(size_filter_entry_frame,
                                 text="Max",
                                 font=self.fonts['small'],
                                 foreground=self.colors['secondary_fg'])
        max_size_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.max_size = CustomEntry(size_filter_entry_frame,
                                  placeholder="inf",
                                  font=self.fonts['small'],
                                  width=5)
        self.max_size.configure(background='#333333')  # Force background color
        self.max_size.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
        # Progress section
        progress_frame = ttk.Frame(content_frame.canvas)
        progress_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        progress_header = ttk.Frame(progress_frame)
        progress_header.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_header,
                                    text="Ready",
                                    font=self.fonts['small'],
                                    foreground=self.colors['secondary_fg'])
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(progress_header,
                                      text="0%",
                                      font=self.fonts['small'],
                                      foreground=self.colors['secondary_fg'])
        self.progress_label.pack(side=tk.RIGHT)
        
        # Progress bar
        self.scan_progress_var = tk.DoubleVar()
        self.scan_progress = CustomProgressBar(progress_frame)
        self.scan_progress.pack(fill=tk.X, pady=(5, 0))
        
        # Filter section (initially hidden)
        self.filter_frame = ttk.Frame(content_frame.canvas)
        self.filter_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        self.filter_frame.pack_forget()  # Hide initially
        
        filter_label = ttk.Label(self.filter_frame,
                               text="Select Image Types to Download",
                               font=self.fonts['body'],
                               foreground=self.colors['fg'])
        filter_label.pack(anchor='w', pady=(0, 5))
        
        # Create checkbox frame with grid layout
        self.checkbox_frame = ttk.Frame(self.filter_frame)
        self.checkbox_frame.pack(fill=tk.X, pady=5)
        
        # Style for checkbuttons
        self.style.configure('Filter.TCheckbutton',
                           background=self.colors['bg'],
                           foreground=self.colors['fg'],
                           font=self.fonts['body'])
        
        # Image type filters - will be created dynamically after scan
        self.image_filters = {}
        self.filter_checkbuttons = []
        
        # Save location input (initially hidden)
        self.save_frame = ttk.Frame(content_frame.canvas)
        self.save_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        self.save_frame.pack_forget()  # Hide initially
        
        save_label = ttk.Label(self.save_frame,
                             text="Save Location",
                             font=self.fonts['body'],
                             foreground=self.colors['fg'])
        save_label.pack(anchor='w', pady=(0, 5))
        
        save_entry_frame = ttk.Frame(self.save_frame)
        save_entry_frame.pack(fill=tk.X, padx=10)
        
        self.save_input = CustomEntry(save_entry_frame,
                                    placeholder="Choose save location",
                                    font=self.fonts['body'])
        self.save_input.configure(background='#333333')  # Force background color
        self.save_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10), ipady=10)
        
        self.browse_button = tk.Button(save_entry_frame,
                                     text="Browse",
                                     font=self.fonts['body'],
                                     bg=self.colors['accent'],
                                     fg=self.colors['fg'],
                                     activebackground=self.colors['button_gradient'][1],
                                     activeforeground=self.colors['fg'],
                                     relief='flat',
                                     width=12,
                                     pady=10,
                                     command=self.browse_folder)
        self.browse_button.pack(side=tk.RIGHT, padx=10)
        
        # Start Download button between progress and console
        button_frame = ttk.Frame(content_frame.canvas)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Center container for Start Download button
        center_frame = ttk.Frame(button_frame)
        center_frame.pack(expand=True)
        
        self.start_button = tk.Button(center_frame,
                                    text="Start Download",
                                    font=self.fonts['body'],
                                    bg=self.colors['accent'],
                                    fg=self.colors['fg'],
                                    activebackground=self.colors['button_gradient'][1],
                                    activeforeground=self.colors['fg'],
                                    relief='flat',
                                    width=15,
                                    pady=10,
                                    command=self.start_download)
        self.start_button.pack(padx=10)
        self.start_button.config(state='disabled')
        
        # Console frame at bottom
        console_frame = ttk.Frame(main_container)
        console_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=40, pady=(20, 20))  # Adjusted padding
        
        console_label = ttk.Label(console_frame,
                                text="Console Output",
                                font=self.fonts['body'],
                                foreground=self.colors['fg'])
        console_label.pack(anchor='w', pady=(0, 5))
        
        self.console = scrolledtext.ScrolledText(console_frame,
                                               wrap=tk.WORD,
                                               height=12,  # Increased height from 8 to 12
                                               font=self.fonts['body'],
                                               bg='#333333',
                                               fg='#FFFFFF',
                                               insertbackground='#FFFFFF',
                                               relief='flat',
                                               state='normal')
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different message types
        self.console.tag_configure("error", foreground="#FF453A")
        self.console.tag_configure("success", foreground="#32D74B")
        self.console.tag_configure("info", foreground="#0A84FF")
        self.console.tag_configure("debug", foreground="#AAAAAA")
        
    def _on_progress_change(self, *args):
        value = self.scan_progress_var.get()
        self.scan_progress.set_progress(value)
        self.progress_label.config(text=f"{int(value)}%")
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_input.delete(0, tk.END)
            self.save_input.insert(0, folder)
            
    def start_download(self):
        """Start downloading images."""
        print("Starting download process...")  # Debug print
        
        if not hasattr(self, 'image_sources') or not self.image_sources:
            self.log_message("No images found to download. Please scan a webpage first", "error")
            return
        
        if self.is_downloading:
            # Stop the download
            self.is_downloading = False
            self.start_button.config(text="Start Download")
            self.log_message("Stopping download...", "info")
            return
        
        save_location = self.save_input.get()
        print(f"Save location: {save_location}")  # Debug print
        
        if not save_location or save_location == self.save_input.placeholder:
            self.log_message("Please select a save location", "error")
            return
        
        # Create the directory if it doesn't exist
        os.makedirs(save_location, exist_ok=True)
        
        # Update button state and text
        self.start_button.config(text="Stop Download")
        self.check_button.config(state='disabled')
        self.is_downloading = True
        
        print(f"Starting download thread with {len(self.image_sources)} images")  # Debug print
        
        # Start the download thread
        self.download_thread = threading.Thread(
            target=self.download_thread,
            args=(save_location,),
            daemon=True
        )
        self.download_thread.start()
    
    def download_thread(self, save_location):
        """Download thread to handle the image downloads."""
        try:
            os.makedirs(save_location, exist_ok=True)
            self.log_message(f"Save location: {save_location}", "info")
            
            total_images = len(self.image_sources)
            self.log_message(f"Total images to download: {total_images}", "info")
            downloaded = 0
            failed = 0
            
            # Create a session for better performance
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=20,
                pool_maxsize=20,
                max_retries=3,
                pool_block=False
            )
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Use ThreadPoolExecutor for parallel downloads
            with ThreadPoolExecutor(max_workers=8) as executor:
                self.log_message("Starting parallel download with 8 workers", "info")
                # Submit all download tasks
                future_to_url = {
                    executor.submit(
                        self.download_image, 
                        session, 
                        img_url, 
                        save_location,
                        idx
                    ): (idx, img_url) 
                    for idx, img_url in enumerate(self.image_sources, 1)
                }
                
                # Process completed downloads
                for future in concurrent.futures.as_completed(future_to_url):
                    if not self.is_downloading:
                        self.log_message("Download process stopped by user", "info")
                        # Cancel all pending futures
                        for f in future_to_url:
                            f.cancel()
                        executor.shutdown(wait=False)
                        break
                        
                    idx, url = future_to_url[future]
                    try:
                        success, filename = future.result(timeout=30)
                        if success:
                            downloaded += 1
                            self.log_message(f"Successfully downloaded ({downloaded}/{total_images}): {filename}", "success")
                        else:
                            failed += 1
                            self.log_message(f"Failed to download image {idx} ({failed} failures so far)", "error")
                    except concurrent.futures.TimeoutError:
                        failed += 1
                        self.log_message(f"Timeout downloading image {idx}", "error")
                    except Exception as e:
                        failed += 1
                        self.log_message(f"Error downloading image {idx}: {str(e)}", "error")
                        
                    # Update progress
                    progress = ((downloaded + failed) / total_images) * 100
                    self.update_progress(progress)
                    
            if self.is_downloading:
                self.log_message(f"Download complete. Success: {downloaded}, Failed: {failed}, Total: {total_images}", "info")
            else:
                self.log_message("Download stopped by user", "info")
                
        except Exception as e:
            self.log_message(f"Critical error during download process: {str(e)}", "error")
            
        finally:
            self.is_downloading = False
            session.close()
            self.root.after(0, lambda: self.start_button.config(text="Start Download"))
            self.root.after(0, lambda: self.update_progress(100))
            
    def download_image(self, session, img_url, save_location, idx):
        """Download a single image."""
        self.log_message(f"Attempting to download image {idx} from {img_url}", "info")
        
        for retry in range(2):  # Try twice
            try:
                # Try each URL variation
                for url in self.get_url_variations(img_url):
                    try:
                        self.log_message(f"Trying URL variation: {url}", "debug")
                        response = session.get(
                            url,
                            timeout=(3, 10),  # (connect timeout, read timeout)
                            stream=True,
                            verify=True,
                            allow_redirects=True,
                            headers=self.get_headers(url)
                        )
                        
                        self.log_message(f"Response status code: {response.status_code}", "debug")
                        if response.status_code == 200:
                            # Generate filename from URL
                            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                            content_type = response.headers.get('content-type', '').lower()
                            self.log_message(f"Content type: {content_type}", "debug")
                            
                            # Determine extension from content type or URL
                            if 'webp' in content_type:
                                ext = 'png'  # Convert WebP to PNG
                            elif 'svg' in content_type:
                                ext = 'svg'
                            elif 'png' in content_type:
                                ext = 'png'
                            elif 'jpeg' in content_type or 'jpg' in content_type:
                                ext = 'jpg'
                            else:
                                # Try to get extension from URL or default to jpg
                                ext = url.split('.')[-1].lower().split('?')[0]
                                if ext not in ['jpg', 'jpeg', 'png', 'svg', 'webp']:
                                    ext = 'jpg'
                            
                            filename = f"image_{url_hash}.{ext}"
                            filepath = os.path.join(save_location, filename)
                            self.log_message(f"Saving to: {filepath}", "debug")

                            # Handle WebP images
                            if 'webp' in content_type:
                                try:
                                    self.log_message("Converting WebP image to PNG", "debug")
                                    import io
                                    image_data = response.content
                                    image = Image.open(io.BytesIO(image_data))
                                    image.save(filepath, 'PNG', quality=90)
                                    if os.path.exists(filepath):
                                        self.log_message(f"Successfully converted and saved WebP image to {filepath}", "success")
                                        return True, filename
                                except Exception as e:
                                    self.log_message(f"Error converting WebP image: {str(e)}", "error")
                                    pass

                            # Normal save for non-WebP images or if conversion failed
                            try:
                                with open(filepath, 'wb') as f:
                                    total_size = 0
                                    for chunk in response.iter_content(chunk_size=32768):
                                        if chunk:
                                            total_size += len(chunk)
                                            f.write(chunk)
                                        elif not self.is_downloading:
                                            if os.path.exists(filepath):
                                                os.remove(filepath)
                                            self.log_message("Download cancelled by user", "info")
                                            return False, None
                                    
                                    self.log_message(f"Written {total_size} bytes to file", "debug")

                                if os.path.exists(filepath):
                                    actual_size = os.path.getsize(filepath)
                                    self.log_message(f"File saved successfully. Size: {actual_size} bytes", "success")
                                    return True, filename
                                else:
                                    self.log_message("File not found after writing", "error")
                            except Exception as e:
                                self.log_message(f"Error writing file: {str(e)}", "error")

                    except requests.exceptions.RequestException as e:
                        if retry == 1:  # Only log on last retry
                            self.log_message(f"Network error downloading URL {url}: {str(e)}", "error")
                    except Exception as e:
                        if retry == 1:  # Only log on last retry
                            self.log_message(f"Error downloading URL {url}: {str(e)}", "error")

                if retry < 1:  # Small delay between retries
                    self.log_message(f"Retry {retry + 2} for image {idx}", "debug")
                    time.sleep(0.5)

            except Exception as e:
                if retry == 1:  # Only log on last retry
                    self.log_message(f"Error downloading image {idx}: {str(e)}", "error")

        self.log_message(f"Failed to download image {idx} after all attempts", "error")
        return False, None

    def update_progress(self, value):
        """Update the progress bar and label"""
        self.scan_progress_var.set(value)
        self.progress_label.config(text=f"{int(value)}%")
        
    def update_download_button(self):
        """Enable download button only if at least one filter is selected"""
        if hasattr(self, 'image_sources') and self.image_sources:
            if any(var.get() for var in self.image_filters.values()):
                self.start_button.config(state='normal')
            else:
                self.start_button.config(state='disabled')
    
    def check_images(self):
        """Start the image scanning process"""
        url = self.url_entry.get()
        
        if url == self.url_entry.placeholder:
            self.log_message("Please enter a valid URL", "error")
            return
            
        # Add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"Checking images at URL: {url}")  # Debug print
        
        # Clear previous results
        self.image_sources = []
        self.update_progress(0)
        
        try:
            self.log_message(f"Scanning webpage: {url}", "info")
            self.scan_images(url)
            
            if self.image_sources:
                count = len(self.image_sources)
                self.log_message(f"Found {count} images", "success")
                print(f"Found {count} images at {url}")  # Debug print
                
                # Enable the download button
                self.start_button.config(state='normal')
                
                # Update image type checkboxes
                self.update_image_type_filters()
            else:
                self.log_message("No images found", "error")
                self.start_button.config(state='disabled')
                
        except Exception as e:
            self.log_message(f"Error scanning webpage: {str(e)}", "error")
            self.start_button.config(state='disabled')
    
    def scan_images(self, url):
        """Scan the webpage for images."""
        driver = None
        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
            ]
            user_agent = random.choice(user_agents)
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Initialize ChromeDriver using webdriver_manager
            self.log_message("Initializing Chrome WebDriver...", "info")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set various timeouts
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(20)
            
            # Try to load the page directly with Selenium first
            self.log_message(f"Loading page: {url}", "info")
            try:
                driver.get(url)
                
                # Wait for the page to load
                self.log_message("Waiting for page to load...", "info")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Scroll the page to load lazy images
                self.log_message("Scrolling page to load lazy images...", "info")
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                
                # Get all image elements using JavaScript
                self.log_message("Searching for images...", "info")
                js_images = driver.execute_script("""
                    var images = [];
                    // Get all img elements
                    document.querySelectorAll('img').forEach(function(img) {
                        var src = img.src || img.getAttribute('data-src') || 
                                img.getAttribute('data-original') || 
                                img.getAttribute('data-lazy-src');
                        if (src) images.push(src);
                        
                        // Check srcset
                        var srcset = img.srcset;
                        if (srcset) {
                            srcset.split(',').forEach(function(src) {
                                var url = src.trim().split(' ')[0];
                                if (url) images.push(url);
                            });
                        }
                    });
                    
                    // Get background images
                    document.querySelectorAll('*').forEach(function(el) {
                        var style = window.getComputedStyle(el);
                        var bg = style.backgroundImage;
                        if (bg && bg !== 'none') {
                            var url = bg.replace(/^url\(['"](.+)['"]\)/, '$1');
                            if (url) images.push(url);
                        }
                    });
                    
                    return Array.from(new Set(images));
                """)
                
                self.log_message(f"Found {len(js_images)} potential images", "info")
                
                # Process and validate image URLs
                image_urls = set()
                
                for src in js_images:
                    if src and not src.startswith('data:'):
                        abs_url = urljoin(url, src)
                        image_urls.add(abs_url)
                
                # Filter and store valid image URLs
                valid_urls = []
                session = requests.Session()
                session.headers.update({'User-Agent': user_agent})
                
                for img_url in image_urls:
                    try:
                        response = session.head(img_url, timeout=10, allow_redirects=True)
                        if response.status_code == 200 and 'image' in response.headers.get('content-type', '').lower():
                            valid_urls.append(img_url)
                            self.log_message(f"Found valid image: {img_url}", "info")
                    except Exception as e:
                        continue
                
                if valid_urls:
                    self.image_sources = valid_urls
                    self.log_message(f"Found {len(valid_urls)} valid image URLs", "success")
                else:
                    self.log_message("No valid images found on the page", "warning")
                
            except TimeoutException:
                self.log_message("Page load timed out, but continuing with available content", "warning")
            except Exception as e:
                self.log_message(f"Error loading page: {str(e)}", "error")
                raise
            
        except Exception as e:
            self.log_message(f"Error during scanning: {str(e)}", "error")
            raise
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def get_image_type(self, url):
        """Determine the image type from URL."""
        try:
            # Extract extension from URL
            parsed = urlparse(url)
            path = unquote(parsed.path.lower())
            
            # Check known extensions
            if path.endswith(('.jpg', '.jpeg')):
                return 'JPEG'
            elif path.endswith('.png'):
                return 'PNG'
            elif path.endswith('.gif'):
                return 'GIF'
            elif path.endswith('.webp'):
                return 'WEBP'
            elif path.endswith('.svg'):
                return 'SVG'
            
            # Try to guess type from URL
            guessed_type = mimetypes.guess_type(url)[0]
            if guessed_type:
                if 'jpeg' in guessed_type:
                    return 'JPEG'
                elif 'png' in guessed_type:
                    return 'PNG'
                elif 'gif' in guessed_type:
                    return 'GIF'
                elif 'webp' in guessed_type:
                    return 'WEBP'
                elif 'svg' in guessed_type:
                    return 'SVG'
                
        except Exception:
            pass
        return None

    def create_filter_checkboxes(self, available_types):
        """Create checkboxes for available image types"""
        # Clear existing checkboxes and filters
        for cb in self.filter_checkbuttons:
            cb.destroy()
        self.filter_checkbuttons.clear()
        self.image_filters.clear()
        
        # Create new checkboxes only for available types
        row = 0
        col = 0
        for img_type in sorted(available_types):
            self.image_filters[img_type] = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.checkbox_frame,
                               text=img_type,
                               variable=self.image_filters[img_type],
                               style='Filter.TCheckbutton',
                               command=self.update_download_button)
            cb.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            self.filter_checkbuttons.append(cb)
            col += 1
            if col > 2:  # 3 checkboxes per row
                col = 0
                row += 1
    
    def log_message(self, message, level="info"):
        """Log a message with the specified level."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level = level.upper()
        
        # Color mapping for different message levels
        colors = {
            "ERROR": "red",
            "SUCCESS": "green",
            "INFO": "white",
            "DEBUG": "yellow"
        }
        
        # Print to console for immediate feedback
        print(f"[{timestamp}] {level}: {message}")
        
        # Also log to the text widget if it exists
        if hasattr(self, 'log_text'):
            color = colors.get(level, "white")
            self.root.after(0, lambda: self.log_text.configure(state='normal'))
            self.root.after(0, lambda: self.log_text.insert('end', f"[{timestamp}] {level}: {message}\n", color))
            self.root.after(0, lambda: self.log_text.configure(state='disabled'))
            self.root.after(0, lambda: self.log_text.see('end'))
            
if __name__ == '__main__':
    root = tk.Tk()
    app = ImageScraperApp(root)
    root.mainloop()
