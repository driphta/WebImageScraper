# Web Image Scraper

A modern desktop application that allows you to download all images from a website by simply entering its URL. Built with Python and PyQt6, it features a clean interface and robust image downloading capabilities.

## Features

- Clean, modern PyQt6-based user interface
- Support for multiple image formats (JPG, PNG, SVG, WebP)
- Advanced image detection:
  - Regular `<img>` tags
  - Background images
  - Lazy-loaded images
  - Data-src attributes
- Intelligent scrolling to find dynamically loaded images
- Progress tracking with detailed status updates
- Customizable save location
- Robust error handling and retry mechanism
- Protected asset handling with proper headers
- Concurrent downloads for better performance

## Requirements

- Python 3.7 or higher
- Chrome/Chromium browser (for Selenium WebDriver)
- Required Python packages (install using `pip install -r requirements.txt`):
  - PyQt6
  - requests
  - selenium
  - webdriver_manager
  - Pillow

## Installation

1. Clone this repository:
```bash
git clone https://github.com/[your-username]/WebImageScraper.git
cd WebImageScraper
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application using the provided batch file:
```bash
run_scraper.bat
```
Or directly with Python:
```bash
python src/main.py
```

2. Enter a website URL in the "Website URL" field
3. Click "Browse" to select where you want to save the images
4. Click "Start Download" to begin the process
5. Monitor the progress and status messages in the application
6. When complete, you'll find all downloaded images in your selected folder

## How It Works

The application uses a combination of Selenium WebDriver and custom JavaScript to:
1. Load the webpage and wait for initial content
2. Scroll through the page to trigger lazy-loaded images
3. Extract image URLs using various selectors
4. Download images concurrently with proper headers and retry logic

## Notes

- Handles both regular and protected images (with proper headers)
- Supports relative and absolute URLs
- Maintains image quality and original formats
- Handles SVG files properly
- Includes retry mechanism for failed downloads
- Uses concurrent downloads for better performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
