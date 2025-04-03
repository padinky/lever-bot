"""
Utilities for simulating human-like behavior in browser interactions.
"""
import random
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)

async def human_like_delay(page: Page, min_delay: float = 0.5, max_delay: float = 2.0):
    """
    Add random delay and scrolling to mimic human behavior.
    
    Args:
        page: The Playwright page object
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
    """
    # Random delay between actions
    delay = random.uniform(min_delay, max_delay)
    await page.wait_for_timeout(delay * 1000)  # Convert to milliseconds
    
    # Random scrolling behavior (70% chance to scroll)
    # commented out since it is interrupting the debounce dropdowns to be appearing
    # if random.random() < 0.7:
    #     try:
    #         # Get page height
    #         page_height = await page.evaluate('document.documentElement.scrollHeight')
    #         viewport_height = await page.evaluate('window.innerHeight')
            
    #         # Random scroll positions
    #         scroll_positions = [
    #             random.randint(0, max(1, page_height - viewport_height)),
    #             random.randint(0, max(1, page_height - viewport_height))
    #         ]
            
    #         # for position in scroll_positions:
    #         #     await page.evaluate(f'window.scrollTo(0, {position})')
    #         #     await page.wait_for_timeout(random.randint(200, 800))
                
    #     except Exception as e:
    #         logger.error(f"Error during scrolling: {str(e)}")

async def human_like_typing(element, text, min_delay=50, max_delay=150):
    """
    Type text with random delays between keystrokes to simulate human typing.
    
    Args:
        element: The Playwright element to type into
        text: The text to type
        min_delay: Minimum delay between keystrokes in milliseconds
        max_delay: Maximum delay between keystrokes in milliseconds
    """
    await element.fill("")  # Clear the field first
    
    # Type each character with a random delay
    for char in text:
        delay = random.randint(min_delay, max_delay)
        await element.type(char, delay=delay)