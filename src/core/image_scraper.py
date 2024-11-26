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

class ImageScraper:
    def __init__(self, logger_callback=None):
        self.logger_callback = logger_callback or (lambda msg, level: print(f"[{level}] {msg}"))
        self.is_downloading = False
        self.image_sources = []
        
    def log(self, message, level="info"):
        if self.logger_callback:
            self.logger_callback(message, level)
        
    def get_headers(self, url):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': domain,
            'Origin': domain,
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
    def scan_webpage(self, url):
        driver = None
        try:
            self.log("Configuring Chrome WebDriver...", "info")
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Updated headless argument
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--blink-settings=imagesEnabled=true')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            user_agent = random.choice(self.get_headers(url)['User-Agent'])
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            try:
                self.log("Initializing Chrome WebDriver...", "info")
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                self.log(f"Error initializing Chrome WebDriver: {str(e)}", "error")
                raise Exception("Failed to initialize Chrome WebDriver. Please make sure Chrome browser is installed.")
            
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(5)
            
            self.log(f"Loading page: {url}", "info")
            driver.get(url)
            
            self.log("Waiting for page to load...", "info")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(1)
            
            self.log("Starting image scan...", "info")
            self.image_sources = set()  # Using set for faster duplicate checking
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            # Initial image scan
            initial_scan_script = """
                const images = new Set();
                
                // Basic images
                document.querySelectorAll('img').forEach(img => {
                    if (img.src) images.add(img.src);
                    if (img.dataset.src) images.add(img.dataset.src);
                });
                
                // Lazy-loaded images
                document.querySelectorAll('img[data-src], img[data-lazy-src], img[data-original]').forEach(img => {
                    const src = img.dataset.src || img.dataset.lazySrc || img.dataset.original;
                    if (src) images.add(src);
                });
                
                return Array.from(images);
            """
            
            initial_images = driver.execute_script(initial_scan_script)
            for src in initial_images:
                if src and not src.startswith('data:'):
                    if src.startswith('//'):
                        src = f'https:{src}'
                    elif src.startswith('/'):
                        src = f'{base_url}{src}'
                    elif not src.startswith(('http://', 'https://')):
                        src = f'{base_url}/{src}'
                    self.image_sources.add(src)
            
            self.log(f"Found {len(self.image_sources)} images initially", "info")
            
            # Scroll and scan script
            scroll_script = """
                const images = new Set();
                
                // Collect images function
                function collectImages() {
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src) images.add(img.src);
                        if (img.dataset.src) images.add(img.dataset.src);
                    });
                    
                    document.querySelectorAll('img[data-src], img[data-lazy-src], img[data-original]').forEach(img => {
                        const src = img.dataset.src || img.dataset.lazySrc || img.dataset.original;
                        if (src) images.add(src);
                    });
                    
                    return Array.from(images);
                }
                
                // Scroll and return results
                window.scrollTo(0, document.body.scrollHeight);
                return collectImages();
            """
            
            # Scroll and collect images
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            
            while scroll_count < 3:  # Maximum 3 scrolls
                scroll_count += 1
                
                # Execute scroll and collect images
                new_images = driver.execute_script(scroll_script)
                
                # Process found images
                for src in new_images:
                    if src and not src.startswith('data:'):
                        if src.startswith('//'):
                            src = f'https:{src}'
                        elif src.startswith('/'):
                            src = f'{base_url}{src}'
                        elif not src.startswith(('http://', 'https://')):
                            src = f'{base_url}/{src}'
                        self.image_sources.add(src)
                
                self.log(f"Found {len(self.image_sources)} images after scroll {scroll_count}", "info")
                
                # Check if we've reached the bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
                time.sleep(0.5)  # Brief pause between scrolls
            
            # Convert set back to list for consistent ordering
            self.image_sources = list(self.image_sources)
            
            count = len(self.image_sources)
            self.log(f"Found {count} unique images", "success" if count > 0 else "error")
            return count
            
        except Exception as e:
            self.log(f"Error scanning webpage: {str(e)}", "error")
            return 0
            
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.log(f"Error closing WebDriver: {str(e)}", "debug")

    def filter_image_sources(self, allowed_types):
        """Filter image sources based on allowed file types"""
        filtered_sources = []
        self.log(f"Starting filtering with {len(self.image_sources)} images", "info")
        self.log(f"Allowed types: {allowed_types}", "info")
        
        for src in self.image_sources:
            src_lower = src.lower()
            self.log(f"Checking image: {src}", "debug")
            
            if src_lower.startswith('//'):
                src_lower = 'https:' + src_lower
            
            base_url = src_lower.split('?')[0]
            
            is_allowed = False
            matched_type = None
            
            extensions = {
                'jpg': ['.jpg', '.jpeg'],
                'jpeg': ['.jpg', '.jpeg'],
                'png': ['.png'],
                'svg': ['.svg'],
                'webp': ['.webp']
            }
            
            for img_type in allowed_types:
                type_lower = img_type.lower()
                valid_extensions = extensions.get(type_lower, [f'.{type_lower}'])
                for ext in valid_extensions:
                    if base_url.endswith(ext):
                        is_allowed = True
                        matched_type = img_type
                        self.log(f"Matched extension {ext} in {base_url}", "debug")
                        break
                if is_allowed:
                    break
            
            if not is_allowed:
                for img_type in allowed_types:
                    type_lower = img_type.lower()
                    if type_lower in ['jpg', 'jpeg']:
                        if '/jpeg' in base_url or '/jpg' in base_url:
                            is_allowed = True
                            matched_type = 'JPG'
                            self.log(f"Matched content type jpg/jpeg in {base_url}", "debug")
                            break
                    elif f'/{type_lower}' in base_url:
                        is_allowed = True
                        matched_type = img_type
                        self.log(f"Matched content type {type_lower} in {base_url}", "debug")
                        break
            
            if is_allowed:
                filtered_sources.append(src)
                self.log(f"✓ Accepted ({matched_type}): {src}", "success")
            else:
                self.log(f"✗ Rejected: {src} (base URL: {base_url})", "debug")
        
        self.log(f"Filtering complete. Found {len(filtered_sources)} matching images", "info")
        return filtered_sources

    def download_images(self, save_location, allowed_types=None, progress_callback=None, min_size=0, max_size=float('inf')):
        """Download all filtered images to the specified location"""
        if not self.image_sources:
            self.log("No images to download", "error")
            return
            
        if allowed_types:
            self.image_sources = self.filter_image_sources(allowed_types)
            
        total_images = len(self.image_sources)
        if total_images == 0:
            self.log("No images match the selected file types", "error")
            return
            
        self.log(f"Starting download with {total_images} images", "info")
        self.is_downloading = True
        downloaded = 0
        failed = 0
        skipped = 0
        
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=1,  
            pool_block=False
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        domain_groups = {}
        for idx, url in enumerate(self.image_sources, 1):
            domain = urlparse(url if not url.startswith('//') else 'https:' + url).netloc
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append((idx, url))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for domain, urls in domain_groups.items():
                domain_futures = [
                    executor.submit(
                        self._download_single_image_with_retry, 
                        session, url, save_location, idx,
                        min_size=min_size,
                        max_size=max_size,
                        max_retries=3,  
                        initial_timeout=15  
                    )
                    for idx, url in urls
                ]
                futures.extend(domain_futures)
            
            for future in as_completed(futures):
                try:
                    result, status = future.result()
                    if result:
                        if status == "downloaded":
                            downloaded += 1
                        elif status == "skipped":
                            skipped += 1
                    else:
                        failed += 1
                        
                    if progress_callback:
                        progress = (downloaded + failed + skipped) * 100 // total_images
                        progress_callback(progress)
                        
                except Exception as e:
                    failed += 1
                    self.log(f"Unexpected error during download: {str(e)}", "error")
                    if progress_callback:
                        progress = (downloaded + failed + skipped) * 100 // total_images
                        progress_callback(progress)
        
        self.is_downloading = False
        if progress_callback:
            progress_callback(100)
        self.log(f"Download complete. Successfully downloaded: {downloaded}, Skipped (size filter): {skipped}, Failed: {failed}", "info")

    def _download_single_image_with_retry(self, session, img_url, save_location, idx, min_size=0, max_size=float('inf'), max_retries=3, initial_timeout=15):
        """Download a single image with optimized retry logic"""
        timeout = initial_timeout
        
        for attempt in range(max_retries):
            try:
                return self._download_single_image(session, img_url, save_location, idx, timeout, min_size, max_size)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                if attempt == max_retries - 1:
                    self.log(f"Failed to download image {idx} after {max_retries} attempts: {str(e)}", "error")
                    return False, None
                timeout = min(timeout * 2, 30)
                time.sleep(1)  # Add a small delay between retries
                continue
            except Exception as e:
                self.log(f"Error downloading image {idx}: {str(e)}", "error")
                return False, None

    def _download_single_image(self, session, img_url, save_location, idx, timeout, min_size=0, max_size=float('inf')):
        """Download a single image with the specified timeout"""
        try:
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
                
            # Remove query parameters from URL for filename but keep them for download
            download_url = img_url
            base_url = img_url.split('?')[0]
            
            # Clean up query parameters
            if '?h=undefined' in download_url or '?w=undefined' in download_url:
                download_url = base_url
            
            # Prepare headers
            headers = self.get_headers(img_url)
            
            # Add specific headers for SVG files
            if base_url.lower().endswith('.svg'):
                headers.update({
                    'Accept': 'image/svg+xml,image/*,*/*;q=0.8',
                    'Sec-Fetch-Dest': 'image',
                    'Sec-Fetch-Mode': 'cors',
                })
            
            # Create session with keep-alive
            session.headers.update(headers)
            
            # Make the request with a session
            response = session.get(
                download_url,
                timeout=timeout,
                stream=True,
                verify=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Determine extension based on content type
            content_type = response.headers.get('content-type', '').lower()
            self.log(f"Content-Type for image {idx}: {content_type}", "debug")
            
            if 'image/svg+xml' in content_type:
                extension = '.svg'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                extension = '.jpg'
            elif 'image/png' in content_type:
                extension = '.png'
            elif 'image/webp' in content_type:
                extension = '.jpg'  # Convert webp to jpg
            else:
                # Fallback to URL extension
                url_ext = os.path.splitext(base_url)[1].lower()
                if url_ext in ['.jpg', '.jpeg', '.png', '.svg']:
                    extension = url_ext
                else:
                    extension = '.jpg'
            
            # Generate filename
            filename = hashlib.md5(base_url.encode()).hexdigest()[:10] + extension
            filepath = os.path.join(save_location, filename)
            
            # Download with progress tracking
            with open(filepath, 'wb') as f:
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if not self.is_downloading:
                        return False, None
                    if chunk:
                        total_size += len(chunk)
                        if total_size > max_size:
                            os.remove(filepath)  # Clean up partial file
                            self.log(f"Skipping image {idx} - too large ({total_size} bytes)", "info")
                            return True, "skipped"
                        f.write(chunk)
                
                if total_size < min_size:
                    os.remove(filepath)  # Clean up file that's too small
                    self.log(f"Skipping image {idx} - too small ({total_size} bytes)", "info")
                    return True, "skipped"
                
                self.log(f"Successfully downloaded image {idx} ({total_size} bytes)", "success")
                return True, "downloaded"
            
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed for image {idx}: {str(e)}", "error")
            return False, None
        except Exception as e:
            self.log(f"Unexpected error downloading image {idx}: {str(e)}", "error")
            return False, None
