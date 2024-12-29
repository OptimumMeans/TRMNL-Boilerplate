from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import logging
import requests
import certifi
import traceback
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class DisplayGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        try:
            self.title_font = ImageFont.truetype(font='arial.ttf', size=24)
            self.heading_font = ImageFont.truetype(font='arial.ttf', size=20)
            self.body_font = ImageFont.truetype(font='arial.ttf', size=16)
            self.small_font = ImageFont.truetype(font='arial.ttf', size=12)
        except Exception as e:
            logger.warning(f'Failed to load TrueType font: {e}')
            self.title_font = ImageFont.load_default()
            self.heading_font = self.title_font
            self.body_font = self.title_font
            self.small_font = self.title_font

    def create_display(self, data: Dict[str, Any]) -> Optional[bytes]:
        '''Create FBI Most Wanted display for TRMNL e-ink display.'''
        try:
            if not data or 'wanted_list' not in data:
                return self.create_error_display('No FBI data available')
            
            image = Image.new('1', (self.width, self.height), 1)  # White background
            draw = ImageDraw.Draw(image)
            
            # Draw header
            self._draw_header(draw, data)
            
            # Draw most wanted person
            if data['wanted_list']:
                self._draw_wanted_person(draw, data['wanted_list'][0], image)
            
            # Draw status bar
            self._draw_status_bar(draw, data)
            
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f'Error generating FBI display: {str(e)}')
            logger.error(traceback.format_exc())
            return self.create_error_display(str(e))

    def _draw_header(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw FBI Most Wanted header.'''
        # Draw title
        draw.text(
            (20, 20),
            'FBI MOST WANTED',
            font=self.title_font,
            fill=0
        )
        
        # Draw total count
        draw.text(
            (20, 50),
            f"Total Wanted: {data.get('total_wanted', 0)}",
            font=self.body_font,
            fill=0
        )

    def _draw_wanted_person(self, draw: ImageDraw, person: Dict[str, Any], image: Image) -> None:
        '''Draw wanted person information with photo.'''
        # Set up dimensions for image placement
        image_width = 250  # Width for person's photo
        image_height = 300  # Max height for photo
        image_x = self.width - image_width - 20  # Position from right edge
        text_width = image_x - 40  # Available width for text
        
        # Draw name/title
        title_lines = self._wrap_text(person['title'], self.heading_font, text_width)
        current_y = 90
        for line in title_lines:
            draw.text(
                (20, current_y),
                line,
                font=self.heading_font,
                fill=0
            )
            current_y += 25

        # Try to fetch and display image
        if person['images']:
            logger.info(f"Attempting to fetch image from URL: {person['images']}")
            wanted_image = self._fetch_image(person['images'])
            
            if wanted_image:
                # Process the image
                wanted_image = wanted_image.convert('L')  # Convert to grayscale
                aspect_ratio = wanted_image.height / wanted_image.width
                target_height = min(image_height, int(image_width * aspect_ratio))
                wanted_image = wanted_image.resize((image_width, target_height))
                
                # Convert to 1-bit black and white with dithering
                wanted_image = wanted_image.convert('1', dither=Image.FLOYDSTEINBERG)
                
                # Paste image onto display
                image.paste(wanted_image, (image_x, 90))
                logger.info("Successfully processed and pasted image")
            else:
                # Create placeholder if image fetch failed
                self._draw_placeholder_image(image, image_x, image_width)

        # Draw status
        if person['status'] and person['status'].lower() != 'na':
            current_y += 10
            draw.text(
                (20, current_y),
                f"Status: {person['status']}",
                font=self.body_font,
                fill=0
            )
            current_y += 25

        # Draw reward text if available
        if person['reward_text']:
            current_y += 10
            reward_lines = self._wrap_text(person['reward_text'], self.body_font, text_width)
            for line in reward_lines[:2]:  # Limit to 2 lines
                draw.text((20, current_y), line, font=self.body_font, fill=0)
                current_y += 25

        # Draw description
        if person['description']:
            current_y += 10
            desc_lines = self._wrap_text(person['description'], self.small_font, text_width)
            for line in desc_lines[:8]:  # Limit to 8 lines
                draw.text((20, current_y), line, font=self.small_font, fill=0)
                current_y += 20

        # Draw details if available and there's space
        if person['details'] and current_y < (self.height - 100):
            current_y += 10
            # Strip HTML tags from details
            import re
            details_text = re.sub('<[^<]+?>', '', person['details'])
            details_lines = self._wrap_text(details_text, self.small_font, text_width)
            remaining_space = (self.height - 100) - current_y
            max_lines = remaining_space // 20
            for line in details_lines[:max_lines]:
                draw.text(
                    (20, current_y),
                    line,
                    font=self.small_font,
                    fill=0
                )
                current_y += 20

    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw status bar at bottom of display.'''
        status_height = 30
        bar_y = self.height - status_height - 10
        
        # Draw black background for status bar
        draw.rectangle(
            [0, bar_y, self.width, bar_y + status_height],
            fill=0
        )
        
        # Format timestamp
        timestamp = data.get('timestamp', 'Unknown')
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except ValueError:
                pass
        
        # Draw timestamp in white text
        status_text = f'Last Update: {timestamp}'
        draw.text(
            (10, bar_y + 5),
            status_text,
            font=self.small_font,
            fill=1  # White text on black background
        )

    def _draw_placeholder_image(self, image: Image, x: int, width: int) -> None:
        '''Draw a placeholder when image cannot be loaded.'''
        placeholder = Image.new('L', (width, 200), 255)
        draw = ImageDraw.Draw(placeholder)
        draw.text(
            (width//2 - 50, 80),
            "Image\nNot Available",
            font=self.body_font,
            fill=0,
            align='center'
        )
        image.paste(placeholder, (x, 90))

    def _fetch_image(self, url: str) -> Optional[Image.Image]:
        '''Fetch image using Selenium to bypass Cloudflare.'''
        try:
            # First try direct request with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://www.fbi.gov/',
                'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'image',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-origin',
            }

            session = requests.Session()
            # First visit main site to get cookies
            session.get('https://www.fbi.gov/', headers=headers, timeout=10)
            
            # Now try to get the image
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            
            # If direct request failed, try using selenium
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import base64
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36')
            
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            
            with webdriver.Chrome(service=service, options=chrome_options) as driver:
                logger.info(f"Fetching image with Selenium from URL: {url}")
                
                # Navigate to the image URL
                driver.get(url)
                
                # Wait for the image to load
                img_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )
                
                # Get the image as base64
                img_base64 = driver.execute_async_script("""
                    var canvas = document.createElement('canvas');
                    var context = canvas.getContext('2d');
                    var img = document.querySelector('img');
                    var done = arguments[0];
                    
                    function getBase64() {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        context.drawImage(img, 0, 0);
                        done(canvas.toDataURL('image/png').split(',')[1]);
                    }
                    
                    if (img.complete) {
                        getBase64();
                    } else {
                        img.addEventListener('load', getBase64);
                    }
                """)
                
                # Convert base64 to PIL Image
                img_data = base64.b64decode(img_base64)
                return Image.open(io.BytesIO(img_data))
                
        except Exception as e:
            logger.error(f"Error fetching image: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def create_error_display(self, error_message: str) -> bytes:
        '''Create error display.'''
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)
        
        # Draw error header
        draw.text(
            (20, 20),
            'FBI Most Wanted - Error',
            font=self.title_font,
            fill=0
        )
        
        # Draw error message
        error_lines = self._wrap_text(error_message, self.body_font, self.width - 40)
        current_y = 60
        for line in error_lines:
            draw.text(
                (20, current_y),
                line,
                font=self.body_font,
                fill=0
            )
            current_y += 25
        
        buffer = io.BytesIO()
        image.save(buffer, format='BMP')
        return buffer.getvalue()

    def _wrap_text(self, text: str, font: ImageFont, max_width: int) -> list[str]:
        '''Wrap text to fit within specified width.'''
        if not text:
            return []
            
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_width = font.getlength(' '.join(current_line))
            if line_width > max_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines