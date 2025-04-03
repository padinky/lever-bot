"""
Browser and page handling services.
"""
import logging
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from config.settings import TIMEOUT, APPLICATION_FORM_SELECTOR, HEADLESS
from services.form_service import extract_form_fields, fill_form_fields, submit_application
from services.ai_service import suggest_field_values

logger = logging.getLogger(__name__)

async def browse_with_proxy(proxy, url):
    """
    Launch browser with the given proxy and visit the specified URL.
    
    Args:
        proxy: Dictionary with proxy configuration (server, username, password)
        url: The URL to visit
        
    Raises:
        Exception: If there's an error during browser interaction
    """
    logger.info(f"Attempting to visit {url} using proxy: {proxy['server']}")
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=HEADLESS)
            
            # Create context with proxy
            context = await browser.new_context(
                proxy={
                    "server": proxy["server"],
                    "username": proxy["username"],
                    "password": proxy["password"],
                }
            )
            
            page = await context.new_page()

            # Block unnecessary resources
            await page.route("**/*", lambda route, request:
                route.abort() if request.resource_type in ["font", "image", "media"] else route.continue_())

            try:
                # Navigate to the URL
                response = await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
                
                # Check response status
                if response.status != 200:
                    logger.error(f"Received non-200 status code ({response.status}) for {url}")
                    raise Exception(f"HTTP {response.status} error accessing {url}")
                

                
                # Wait for the application form to be visible
                await page.wait_for_selector(APPLICATION_FORM_SELECTOR, timeout=TIMEOUT)
                logger.info(f"Successfully found {APPLICATION_FORM_SELECTOR} on {url}")
                
                # Extract form fields
                required_fields = await extract_form_fields(page)
                
                # Get suggested values for form fields
                # In production, replace with actual AI service call
                suggested_values = suggest_field_values(required_fields)
                
                # Log suggested values
                suggested_values_array = [{"key": k, "value": v} for k, v in suggested_values.items()]
                logger.info(f"Suggested values: {suggested_values_array}")

                # Fill the form fields
                await fill_form_fields(page, required_fields, suggested_values)
                
                # Submit the application
                await submit_application(page)
                
            except PlaywrightTimeoutError:
                logger.error(f"Timeout while trying to load {url} with proxy: {proxy}")
                raise  # raise error to try a different proxy
            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"Failed to use proxy {proxy}: {str(e)}")
        raise  # raise the exception to try the next proxy