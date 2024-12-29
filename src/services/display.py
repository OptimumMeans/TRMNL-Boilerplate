from PIL import Image, ImageDraw, ImageFont
import io
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DisplayGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        try:
            self.font = ImageFont.truetype(font='arial.ttf', size=32)
        except Exception as e:
            logger.warning(f'Failed to load TrueType font: {e}')
            self.font = ImageFont.load_default()
        
        # Smaller font for status bar
        try:
            self.small_font = ImageFont.truetype(font='arial.ttf', size=16)
        except Exception as e:
            self.small_font = ImageFont.load_default()

    def create_display(self, data: Dict[str, Any]) -> Optional[bytes]:
        '''Create a display image for the TRMNL e-ink display.'''
        try:
            image = Image.new('1', (self.width, self.height), 1)
            draw = ImageDraw.Draw(image)
            
            if not data:
                return self.create_error_display('No data available')
            
            # Draw your content here
            self._draw_content(draw, data)
            self._draw_status_bar(draw, data)
            
            buffer = io.BytesIO()
            image.save(buffer, format='BMP')
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f'Error generating display: {str(e)}')
            return self.create_error_display(str(e))
    
    def create_error_display(self, error_message: str) -> bytes:
        '''Create an error display.'''
        image = Image.new('1', (self.width, self.height), 1)
        draw = ImageDraw.Draw(image)
        
        draw.text(
            (20, 20),
            'Error',
            font=self.font,
            fill=0
        )
        
        draw.text(
            (20, 50),
            error_message,
            font=self.font,
            fill=0
        )
        
        buffer = io.BytesIO()
        image.save(buffer, format='BMP')
        return buffer.getvalue()
    
    def _draw_content(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw the main content of the display.'''
        # Add padding
        padding = 40
        
        # Draw a border with padding
        draw.rectangle(
            [padding, padding, self.width-padding, self.height-padding],
            outline=0,
            width=2
        )
        
        # Draw "Hello TRMNL!" centered
        text = "Hello TRMNL!"
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2 - 40  # Move up a bit
        
        draw.text(
            (x, y),
            text,
            font=self.font,
            fill=0
        )
        
        # Add some example stats below
        example_text = "Example Plugin Display"
        bbox = draw.textbbox((0, 0), example_text, font=self.small_font)
        ex_width = bbox[2] - bbox[0]
        
        draw.text(
            ((self.width - ex_width) // 2, y + text_height + 20),
            example_text,
            font=self.small_font,
            fill=0
        )
    
    def _draw_status_bar(self, draw: ImageDraw, data: Dict[str, Any]) -> None:
        '''Draw a status bar at the bottom of the display.'''
        # Draw status bar slightly above bottom
        status_height = 30
        bar_y = self.height - status_height - 10
        
        draw.rectangle(
            [0, bar_y, self.width, bar_y + status_height],
            fill=0
        )
        
        # Format timestamp more nicely
        timestamp = data.get('timestamp', 'Unknown')
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except ValueError:
                pass
        
        status_text = f'Last Update: {timestamp}'
        draw.text(
            (10, bar_y + 5),
            status_text,
            font=self.small_font,
            fill=1
        )
