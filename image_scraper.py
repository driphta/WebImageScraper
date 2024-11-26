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
from PIL import Image
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
        self.is_downloading = False
        self.download_thread = None
        
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
            'header': ('Segoe UI', 24, 'bold'),
            'subheader': ('Segoe UI', 16),
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
        
        # Create main container with padding
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title section with larger, bolder font
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, padx=40, pady=(40, 5))  # Reduced bottom padding
        
        title_label = ttk.Label(title_frame,
                              text="Web Image Scraper",
                              font=self.fonts['header'],
                              foreground=self.colors['fg'])
        title_label.pack(anchor='center')  # Changed to center
        
        subtitle_frame = ttk.Frame(main_container)
        subtitle_frame.pack(fill=tk.X, padx=40, pady=(0, 30))
        
        subtitle_label = ttk.Label(subtitle_frame,
                                 text="Download images from any website",
                                 font=self.fonts['subheader'],
                                 foreground=self.colors['secondary_fg'])
        subtitle_label.pack(anchor='center')  # Changed to center
        
        # Main content frame with increased corner radius
        content_frame = RoundedFrame(main_container, radius=20, background=self.colors['bg'], padding=30)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 40))
        
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
        entry_frame.pack(fill=tk.X, pady=(0, 0), padx=10)
        
        self.url_entry = CustomEntry(entry_frame,
                                   placeholder="Enter website URL",
                                   font=self.fonts['body'])
        self.url_entry.configure(background='#333333')  # Force background color
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
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
        self.check_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Save location input with matching width
        save_input_frame = ttk.Frame(input_section)
        save_input_frame.pack(fill=tk.X, pady=(0, 15))
        
        save_label = ttk.Label(save_input_frame,
                             text="Save Location",
                             font=self.fonts['body'],
                             foreground=self.colors['fg'])
        save_label.pack(anchor='w', pady=(0, 5))
        
        save_entry_frame = ttk.Frame(save_input_frame)
        save_entry_frame.pack(fill=tk.X, pady=(0, 0), padx=10)
        
        self.save_input = CustomEntry(save_entry_frame,
                                    placeholder="Choose save location",
                                    font=self.fonts['body'])
        self.save_input.configure(background='#333333')  # Force background color
        self.save_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
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
        self.browse_button.pack(side=tk.RIGHT, padx=(0, 10))
        
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
        
        # Bind progress updates
        self.scan_progress_var.trace_add('write', self._on_progress_change)
        
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
        self.start_button.pack(padx=10)  # Added padding for visual balance
        
        # Console output
        console_frame = ttk.Frame(content_frame.canvas)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=15)
        
        self.console = scrolledtext.ScrolledText(console_frame,
                                               wrap=tk.WORD,
                                               height=10,
                                               font=self.fonts['body'],
                                               bg='#333333',
                                               fg='#FFFFFF',
                                               insertbackground='#FFFFFF',
                                               relief='flat',
                                               state='normal')  # Changed from 'disabled' to 'normal'
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
        """Start downloading the found images"""
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
        if save_location == self.save_input.placeholder:
            self.log_message("Please select a save location", "error")
            return
        
        # Create the directory if it doesn't exist
        os.makedirs(save_location, exist_ok=True)
        
        # Update button state and text
        self.start_button.config(text="Stop Download")
        self.check_button.config(state='disabled')
        self.is_downloading = True
        
        def download_thread():
            try:
                total_images = len(self.image_sources)
                downloaded = 0
                failed = 0
                retry_count = 2  # Reduced retry count
                timeout = 30    # Reduced timeout
                
                # Create a session for better performance
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                })
                
                def get_image_type(self, url, content_type=None):
                    """Determine the image type from URL and content type."""
                    url_lower = url.lower()
                    image_type = None
                    
                    # Check content type first if available
                    if content_type and isinstance(content_type, str):
                        content_type = content_type.lower()
                        if 'webp' in content_type:
                            image_type = 'webp'
                        elif 'svg' in content_type:
                            image_type = 'svg'
                        elif 'png' in content_type:
                            image_type = 'png'
                        elif 'jpeg' in content_type or 'jpg' in content_type:
                            image_type = 'jpg'
                    
                    # If no type detected from content-type, check URL
                    if not image_type:
                        if '.webp' in url_lower:
                            image_type = 'webp'
                        elif '.svg' in url_lower:
                            image_type = 'svg'
                        elif '.png' in url_lower:
                            image_type = 'png'
                        elif '.jpg' in url_lower or '.jpeg' in url_lower:
                            image_type = 'jpg'
                        else:
                            # Default to png for unknown types
                            image_type = 'png'
                    
                    return image_type

                for idx, img_url in enumerate(self.image_sources, 1):
                    if not self.is_downloading:
                        self.log_message("Download stopped by user", "info")
                        break
                        
                    try:
                        url_lower = img_url.lower()
                        original_url = img_url
                        
                        # Get image type
                        content_type = None
                        try:
                            head_response = session.head(img_url, timeout=5, allow_redirects=True)
                            content_type = head_response.headers.get('content-type', '')
                        except Exception as e:
                            pass
                        
                        img_type = get_image_type(self, img_url, content_type)
                        
                        # Handle SVG files differently
                        if img_type == 'svg':
                            success, filename = self.download_svg(session, img_url, save_location, idx)
                            if success:
                                downloaded += 1
                                self.log_message(f"Downloaded SVG: {filename}", "success")
                                continue
                            else:
                                self.log_message(f"Failed to download SVG {idx}, skipping...", "error")
                                failed += 1
                                continue
                        
                        # For WebP and other images, prefer PNG format if from CDN
                        if (img_type == 'webp' or 'cdn' in url_lower or 'assets' in url_lower) and '?' in img_url:
                            try:
                                parsed_url = urlparse(img_url)
                                query_params = parse_qs(parsed_url.query)
                                query_params.update({
                                    'format': ['png'],
                                    'w': query_params.get('w', ['800']),
                                    'q': ['90']
                                })
                                new_query = urlencode(query_params, doseq=True)
                                img_url = urlunparse((
                                    parsed_url.scheme,
                                    parsed_url.netloc,
                                    parsed_url.path,
                                    '',
                                    new_query,
                                    ''
                                ))
                            except:
                                # If URL manipulation fails, use original URL
                                img_url = original_url
                        
                        # Set appropriate headers
                        session.headers.update({
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'image/webp,image/png,image/jpeg,image/*,*/*',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Referer': f"{urlparse(img_url).scheme}://{urlparse(img_url).netloc}/",
                            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                            'Sec-Fetch-Dest': 'image',
                            'Sec-Fetch-Mode': 'no-cors',
                            'Sec-Fetch-Site': 'same-origin'
                        })
                        
                        # Try to download with retries
                        for retry in range(retry_count):
                            if not self.is_downloading:
                                break
                            
                            try:
                                current_url = img_url if retry == 0 else original_url
                                response = session.get(
                                    current_url,
                                    timeout=(10, 30),  # (connect timeout, read timeout)
                                    stream=True,
                                    allow_redirects=True,
                                    verify=True
                                )
                                
                                if response.status_code == 200:
                                    # Determine file extension based on content type and URL
                                    content_type = response.headers.get('content-type', '').lower()
                                    
                                    # Determine extension based on content-type first
                                    if 'webp' in content_type:
                                        ext = '.png'  # Convert WebP to PNG
                                    elif 'svg' in content_type:
                                        ext = '.svg'
                                    elif 'png' in content_type:
                                        ext = '.png'
                                    elif 'jpeg' in content_type or 'jpg' in content_type:
                                        ext = '.jpg'
                                    else:
                                        # Fallback to URL extension
                                        if '.webp' in current_url.lower():
                                            ext = '.png'  # Convert WebP to PNG
                                        elif '.svg' in current_url.lower() and 'image/svg' in content_type:
                                            ext = '.svg'  # Only use SVG if content-type confirms it
                                        elif '.png' in current_url.lower():
                                            ext = '.png'
                                        elif '.jpg' in current_url.lower() or '.jpeg' in current_url.lower():
                                            ext = '.jpg'
                                        else:
                                            ext = '.png'  # Default to PNG
                                    
                                    filename = f"image_{idx}{ext}"
                                    filepath = os.path.join(save_location, filename)
                                    
                                    # For WebP images, try to convert to PNG if possible
                                    if 'webp' in content_type:
                                        try:
                                            from PIL import Image
                                            import io
                                            
                                            # Load WebP image
                                            image_data = response.content
                                            image = Image.open(io.BytesIO(image_data))
                                            
                                            # Save as PNG
                                            image.save(filepath, 'PNG', quality=95)
                                            if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
                                                downloaded += 1
                                                self.log_message(f"Downloaded: {filename}", "success")
                                                continue
                                        except Exception as e:
                                            pass  # Silently fall back to direct save
                                    
                                    # Normal save for non-WebP images or if conversion failed
                                    with open(filepath, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            if chunk and self.is_downloading:
                                                f.write(chunk)
                                            elif not self.is_downloading:
                                                break
                                    
                                    if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
                                        downloaded += 1
                                        self.log_message(f"Downloaded: {filename}", "success")
                                        break
                                    else:
                                        if os.path.exists(filepath):
                                            os.remove(filepath)
                                elif retry == retry_count - 1:
                                    self.log_message(f"Failed to download image {idx}: HTTP {response.status_code} for URL: {current_url}", "error")
                                    failed += 1
                            
                            except Exception as e:
                                if retry == retry_count - 1:
                                    self.log_message(f"Error downloading image {idx}: {str(e)} for URL: {current_url}", "error")
                                    failed += 1
                            
                            if retry < retry_count - 1 and self.is_downloading:
                                time.sleep(1)
                    
                    except Exception as e:
                        self.log_message(f"Error processing image {idx}: {str(e)}", "error")
                
                # Final status update
                if self.is_downloading:
                    self.log_message(f"Download complete! Successfully downloaded {downloaded} of {total_images} images", "success")
                self.root.after(0, lambda: self.update_progress(100))
            
            finally:
                # Reset button states
                self.is_downloading = False
                self.root.after(0, lambda: self.start_button.config(text="Start Download"))
                self.root.after(0, lambda: self.check_button.config(state='normal'))
                session.close()
        
        # Start download in a separate thread
        self.download_thread = threading.Thread(target=download_thread, daemon=True)
        self.download_thread.start()
    
    def download_svg(self, session, img_url, save_location, idx):
        """Dedicated method for downloading SVG files."""
        try:
            # Strip all query parameters and fragments
            parsed_url = urlparse(img_url)
            clean_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                '',
                '',
                ''
            ))
            
            # Set up headers specifically for SVG
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/svg+xml, image/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': f"{parsed_url.scheme}://{parsed_url.netloc}/",
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            # Try downloading with a very short timeout first
            response = session.get(
                clean_url,
                headers=headers,
                timeout=(5, 10),
                stream=False,
                verify=True
            )
            
            if response.status_code == 200:
                # Check if content is actually SVG
                content_type = response.headers.get('content-type', '').lower()
                if 'svg' in content_type or response.content.startswith(b'<?xml') or response.content.startswith(b'<svg'):
                    filename = f"image_{idx}.svg"
                    filepath = os.path.join(save_location, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        return True, filename
            
            return False, None
            
        except (requests.Timeout, requests.RequestException) as e:
            self.log_message(f"SVG download failed: {str(e)}", "error")
            return False, None

    def update_progress(self, value):
        """Update the progress bar and label"""
        self.scan_progress_var.set(value)
        self.progress_label.config(text=f"{int(value)}%")
        
    def check_images(self):
        """Start the image scanning process"""
        url = self.url_entry.get()
        if url == self.url_entry.placeholder:
            self.log_message("Please enter a valid URL", "error")
            return
        
        # Add http:// if not present
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Disable buttons during scan
        self.check_button.config(state='disabled')
        self.start_button.config(state='disabled')
        
        def scan_thread():
            try:
                self.scan_images(url)
            finally:
                # Re-enable buttons
                self.root.after(0, lambda: self.check_button.config(state='normal'))
                self.root.after(0, lambda: self.start_button.config(state='normal'))
        
        # Start scanning in a separate thread
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def scan_images(self, url):
        """Scan the webpage for images"""
        try:
            self.log_message(f"Starting Chrome WebDriver...")
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            driver = webdriver.Chrome(options=options)
            
            self.log_message(f"Loading webpage: {url}")
            driver.get(url)
            
            # Wait for page to load and dynamic content
            self.log_message("Waiting for page to load...")
            wait = WebDriverWait(driver, 20)  # Increased timeout
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll page to load lazy content
            self.log_message("Scrolling page to load dynamic content...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                time.sleep(2)
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            
            # Log page readiness
            ready_state = driver.execute_script("return document.readyState")
            self.log_message(f"Page ready state: {ready_state}", "info")
            
            # Get page metrics
            metrics = driver.execute_script("""
                return {
                    'totalElements': document.getElementsByTagName('*').length,
                    'iframes': document.getElementsByTagName('iframe').length,
                    'scripts': document.getElementsByTagName('script').length
                }
            """)
            self.log_message(f"Page metrics - Total elements: {metrics['totalElements']}, iFrames: {metrics['iframes']}, Scripts: {metrics['scripts']}", "info")
            
            # Method 1: Direct img tags
            images = driver.find_elements(By.TAG_NAME, 'img')
            self.log_message(f"Found {len(images)} direct <img> tags", "info")
            
            # Method 2: Background images with expanded search
            background_elements = driver.execute_script("""
                function getBackgroundImages() {
                    const images = new Set();
                    const elements = document.getElementsByTagName('*');
                    
                    for (const el of elements) {
                        // Check computed style
                        const style = window.getComputedStyle(el);
                        if (style.backgroundImage && style.backgroundImage !== 'none') {
                            images.add(style.backgroundImage);
                        }
                        
                        // Check inline style
                        if (el.style.backgroundImage && el.style.backgroundImage !== 'none') {
                            images.add(el.style.backgroundImage);
                        }
                        
                        // Check data attributes
                        for (const attr of el.attributes) {
                            if (attr.name.startsWith('data-') && 
                                (attr.value.includes('.jpg') || 
                                 attr.value.includes('.jpeg') || 
                                 attr.value.includes('.png') || 
                                 attr.value.includes('.gif') || 
                                 attr.value.includes('.webp'))) {
                                images.add(`url(${attr.value})`);
                            }
                        }
                    }
                    return Array.from(images);
                }
                return getBackgroundImages();
            """)
            self.log_message(f"Found {len(background_elements)} background images", "info")
            
            # Method 3: Picture elements
            picture_elements = driver.find_elements(By.TAG_NAME, 'picture')
            self.log_message(f"Found {len(picture_elements)} <picture> elements", "info")
            
            # Method 4: SVG images
            svg_images = driver.find_elements(By.TAG_NAME, 'svg')
            self.log_message(f"Found {len(svg_images)} SVG elements", "info")
            
            # Method 5: Look for images in data attributes
            data_images = driver.execute_script("""
                function getDataImages() {
                    const images = new Set();
                    const elements = document.getElementsByTagName('*');
                    
                    for (const el of elements) {
                        for (const attr of el.attributes) {
                            if (attr.name.startsWith('data-') && 
                                (attr.value.includes('.jpg') || 
                                 attr.value.includes('.jpeg') || 
                                 attr.value.includes('.png') || 
                                 attr.value.includes('.gif') || 
                                 attr.value.includes('.webp'))) {
                                images.add(attr.value);
                            }
                        }
                    }
                    return Array.from(images);
                }
                return getDataImages();
            """)
            self.log_message(f"Found {len(data_images)} images in data attributes", "info")
            
            # Store all image sources
            self.image_sources = []
            
            # Process direct img tags
            for img in images:
                try:
                    src = img.get_attribute('src')
                    srcset = img.get_attribute('srcset')
                    data_src = img.get_attribute('data-src')
                    data_original = img.get_attribute('data-original')
                    
                    if src:
                        self.log_message(f"Found image with src: {src}", "info")
                        if not src.startswith(('http://', 'https://', 'data:')):
                            src = urljoin(url, src)
                        self.image_sources.append(src)
                    
                    if srcset:
                        self.log_message(f"Found srcset: {srcset}", "info")
                        for srcset_url in srcset.split(','):
                            url_part = srcset_url.strip().split(' ')[0]
                            if not url_part.startswith(('http://', 'https://', 'data:')):
                                url_part = urljoin(url, url_part)
                            self.image_sources.append(url_part)
                    
                    if data_src:
                        self.log_message(f"Found data-src: {data_src}", "info")
                        if not data_src.startswith(('http://', 'https://', 'data:')):
                            data_src = urljoin(url, data_src)
                        self.image_sources.append(data_src)
                    
                    if data_original:
                        self.log_message(f"Found data-original: {data_original}", "info")
                        if not data_original.startswith(('http://', 'https://', 'data:')):
                            data_original = urljoin(url, data_original)
                        self.image_sources.append(data_original)
                        
                except Exception as e:
                    self.log_message(f"Error processing image element: {str(e)}", "error")
            
            # Process background images
            for bg in background_elements:
                try:
                    url_match = re.search(r'url\(["\']?(.*?)["\']?\)', bg)
                    if url_match:
                        bg_url = url_match.group(1)
                        self.log_message(f"Found background image: {bg_url}", "info")
                        if not bg_url.startswith(('http://', 'https://', 'data:')):
                            bg_url = urljoin(url, bg_url)
                        self.image_sources.append(bg_url)
                except Exception as e:
                    self.log_message(f"Error processing background image: {str(e)}", "error")
            
            # Process picture elements
            for picture in picture_elements:
                try:
                    sources = picture.find_elements(By.TAG_NAME, 'source')
                    for source in sources:
                        srcset = source.get_attribute('srcset')
                        if srcset:
                            self.log_message(f"Found picture source: {srcset}", "info")
                            for srcset_url in srcset.split(','):
                                url_part = srcset_url.strip().split(' ')[0]
                                if not url_part.startswith(('http://', 'https://', 'data:')):
                                    url_part = urljoin(url, url_part)
                                self.image_sources.append(url_part)
                except Exception as e:
                    self.log_message(f"Error processing picture element: {str(e)}", "error")
            
            # Process data images
            for data_img in data_images:
                try:
                    if not data_img.startswith(('http://', 'https://', 'data:')):
                        data_img = urljoin(url, data_img)
                    self.image_sources.append(data_img)
                except Exception as e:
                    self.log_message(f"Error processing data image: {str(e)}", "error")
            
            # Remove duplicates while preserving order
            self.image_sources = list(dict.fromkeys(self.image_sources))
            
            if not self.image_sources:
                self.log_message("No images found on the page", "error")
                driver.quit()
                return
            
            self.log_message(f"Successfully found {len(self.image_sources)} unique image sources", "success")
            
            # Log some sample URLs for debugging
            if len(self.image_sources) > 0:
                self.log_message("Sample image sources:", "info")
                for i, src in enumerate(self.image_sources[:5]):
                    self.log_message(f"  {i+1}. {src}", "info")
                if len(self.image_sources) > 5:
                    self.log_message(f"  ... and {len(self.image_sources) - 5} more", "info")
            
            # Enable the Start Download button if images were found
            if self.image_sources:
                self.root.after(0, lambda: self.start_button.config(state='normal'))
            
            # Save page source for debugging if needed
            debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, 'page_source.html'), 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            self.log_message(f"Saved page source to debug/page_source.html for inspection", "info")
            
            driver.quit()
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_message(error_msg, "error")
            self.root.after(0, lambda: self.status_label.config(text="Error occurred while scanning"))
    
    def log_message(self, message, message_type="info"):
        """Add a message to the console with the specified type (info, error, or success)"""
        self.console.configure(state='normal')  # Make widget editable
        self.console.insert(tk.END, f"{message}\n", message_type)
        self.console.see(tk.END)  # Scroll to the end
        self.console.configure(state='normal')  # Keep it normal to allow text selection

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageScraperApp(root)
    root.mainloop()
