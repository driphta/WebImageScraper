import os
import requests
import hashlib
import random
import time
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from selenium.webdriver.chrome.service import Service

class ImageScraper:
    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback if log_callback else print
        self.progress_callback = progress_callback
        self.is_downloading = False
        self.driver = None
        self.image_urls = []  # Store image URLs
        self.filtered_urls = []  # Store filtered URLs
        self._last_scanned_url = None
        
    def log(self, message, level="info"):
        """Log a message using the callback if available"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(message)
            
    def update_progress(self, value):
        """Update progress using the callback if available"""
        if self.progress_callback:
            self.progress_callback(value)
            
    def validate_url(self, url):
        """Validate and normalize the URL"""
        try:
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Parse and validate URL
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL: No domain found")
            
            # Reconstruct URL to ensure proper format
            return parsed.geturl()
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")
            
    def scan_webpage(self, url):
        """Scan webpage for images"""
        if not url:
            return 0
            
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.log("Starting browser...", "info")
        
        # Configure Chrome options for better compatibility
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Start browser with optimized settings
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            self.log("Loading webpage...", "info")
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            self.log("Scanning for images...", "info")
            
            # Collect image URLs with multiple methods
            image_urls = set()
            
            # Method 1: Direct img tags
            selectors = [
                'img[src]',
                'img[data-src]',
                'img[data-lazy-src]',
                'source[srcset]',
                'img[srcset]',
                'picture source'
            ]
            
            elements = driver.find_elements(By.CSS_SELECTOR, ', '.join(selectors))
            for element in elements:
                try:
                    for attr in ['src', 'data-src', 'data-lazy-src', 'srcset']:
                        value = element.get_attribute(attr)
                        if value:
                            if attr == 'srcset':
                                # Handle srcset format
                                urls = [url.strip().split(' ')[0] for url in value.split(',')]
                                image_urls.update(url for url in urls if url.startswith(('http://', 'https://')))
                            else:
                                if value.startswith(('http://', 'https://')):
                                    image_urls.add(value)
                except:
                    continue
            
            # Method 2: Background images
            try:
                script = """
                    return Array.from(document.querySelectorAll('*')).map(el => {
                        const style = window.getComputedStyle(el);
                        const bg = style.backgroundImage;
                        if (bg && bg !== 'none') {
                            const matches = bg.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/g) || [];
                            return matches.map(m => m.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/)[1]);
                        }
                        return [];
                    }).flat();
                """
                bg_images = driver.execute_script(script)
                image_urls.update(url for url in bg_images if url.startswith(('http://', 'https://')))
            except:
                pass
            
            # Method 3: Scroll and scan
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 5
            
            while scroll_attempts < max_scrolls:
                # Scroll down
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Get new images
                elements = driver.find_elements(By.TAG_NAME, 'img')
                for element in elements:
                    try:
                        for attr in ['src', 'data-src', 'srcset']:
                            value = element.get_attribute(attr)
                            if value and value.startswith(('http://', 'https://')):
                                image_urls.add(value)
                    except:
                        continue
                
                # Check if we've reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
            
            # Store results
            self.image_urls = list(image_urls)
            total_images = len(self.image_urls)
            
            if total_images > 0:
                self.log(f"Successfully found {total_images} total images", "success")
            else:
                self.log("No images found on the webpage", "warning")
            
            return total_images
            
        except Exception as e:
            self.log(f"Error scanning webpage: {str(e)}", "error")
            return 0
        finally:
            try:
                driver.quit()
            except:
                pass
                
    def convert_webp_to_png(self, webp_path):
        """Convert WebP image to PNG format"""
        try:
            from PIL import Image
            import io
            
            # Read WebP file
            with Image.open(webp_path) as img:
                # Create PNG path
                png_path = os.path.splitext(webp_path)[0] + '.png'
                
                # Convert to RGB if necessary (for transparency)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                
                # Save as PNG
                img.save(png_path, 'PNG')
                
                # Remove original WebP file
                os.remove(webp_path)
                
                return png_path
        except Exception as e:
            self.log(f"Error converting WebP to PNG: {str(e)}", "error")
            return webp_path

    def download_image(self, img_url, save_location, min_size=0, max_size=float('inf')):
        """Download a single image with optimized handling"""
        try:
            # Custom headers to avoid blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            }
            
            # Get image with stream enabled
            response = requests.get(img_url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            
            # Check content type and size
            content_type = response.headers.get('Content-Type', '').lower()
            content_length = int(response.headers.get('Content-Length', 0))
            
            # Skip if not an image
            if not content_type.startswith('image/'):
                return False, "Not an image"
            
            # Skip if size filters don't match
            if content_length:
                if content_length < min_size:
                    return False, f"Too small ({content_length/1024:.1f}KB)"
                if content_length > max_size:
                    return False, f"Too large ({content_length/1024:.1f}KB)"
            
            # Determine file extension
            ext = None
            is_webp = False
            # First try content type
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                ext = '.jpg'
            elif 'image/png' in content_type:
                ext = '.png'
            elif 'image/webp' in content_type:
                ext = '.png'  # We'll convert WebP to PNG
                is_webp = True
            elif 'image/svg+xml' in content_type:
                ext = '.svg'
            
            # If no extension from content type, try URL
            if not ext:
                url_path = urlparse(img_url).path.lower()
                if url_path.endswith('.webp'):
                    ext = '.png'  # Convert WebP to PNG
                    is_webp = True
                elif url_path.endswith(('.jpg', '.jpeg', '.png', '.svg')):
                    ext = os.path.splitext(url_path)[1]
                else:
                    ext = '.jpg'  # Default to jpg
            
            # Generate unique filename
            timestamp = int(time.time() * 1000)
            random_num = random.randint(1000, 9999)
            filename = f"image_{timestamp}_{random_num}{'.webp' if is_webp else ext}"
            filepath = os.path.join(save_location, filename)
            
            # Download and save
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Convert WebP to PNG if needed
            if is_webp:
                filepath = self.convert_webp_to_png(filepath)
            
            # Verify file size after download
            actual_size = os.path.getsize(filepath)
            if min_size <= actual_size <= max_size:
                self.log(f"Downloaded: {os.path.basename(filepath)} ({actual_size/1024:.1f}KB)", "success")
                return True, filepath
            else:
                os.remove(filepath)
                return False, f"Size filter after download ({actual_size/1024:.1f}KB)"
            
        except requests.exceptions.RequestException as e:
            return False, f"Download error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def start_download(self, url, save_location, allowed_types=None, min_size=0, max_size=float('inf')):
        """Start downloading images with parallel processing"""
        try:
            self.is_downloading = True
            
            if not self.image_urls:
                self.log("No images found. Please scan the webpage first.", "error")
                return
            
            # Create save directory if needed
            os.makedirs(save_location, exist_ok=True)
            
            # Filter URLs by file type
            if allowed_types:
                allowed_types = set(ext.lower().strip('.') for ext in allowed_types)
                self.filtered_urls = []
                for img_url in self.image_urls:
                    # Check URL extension
                    url_path = urlparse(img_url).path.lower()
                    if any(url_path.endswith(f'.{ext}') for ext in allowed_types):
                        self.filtered_urls.append(img_url)
                    else:
                        # If no extension in URL, try to get content type
                        try:
                            response = requests.head(img_url, timeout=5, allow_redirects=True)
                            content_type = response.headers.get('Content-Type', '').lower()
                            if any(f'image/{ext}' in content_type for ext in allowed_types):
                                self.filtered_urls.append(img_url)
                        except:
                            continue
            else:
                self.filtered_urls = self.image_urls.copy()
            
            total_images = len(self.filtered_urls)
            if total_images == 0:
                self.log("No images match the selected file types", "warning")
                return
            
            self.log(f"Starting download of {total_images} images", "info")
            
            # Download images in parallel
            downloaded = failed = skipped = 0
            with ThreadPoolExecutor(max_workers=min(10, total_images)) as executor:
                future_to_url = {
                    executor.submit(
                        self.download_image, 
                        url, 
                        save_location,
                        min_size,
                        max_size
                    ): url for url in self.filtered_urls
                }
                
                for future in as_completed(future_to_url):
                    if not self.is_downloading:
                        break
                    
                    success, result = future.result()
                    if success:
                        downloaded += 1
                    elif "Size filter" in str(result):
                        skipped += 1
                        self.log(f"Skipped: {result}", "info")
                    else:
                        failed += 1
                        self.log(f"Failed: {result}", "error")
                    
                    # Update progress
                    progress = ((downloaded + failed + skipped) / total_images) * 100
                    self.update_progress(progress)
            
            # Final status
            self.log(f"Download complete: {downloaded} downloaded, {skipped} skipped, {failed} failed", "success")
            
        except Exception as e:
            self.log(f"Error during download: {str(e)}", "error")
        finally:
            self.is_downloading = False
