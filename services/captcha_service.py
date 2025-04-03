"""
Services for detecting and solving captchas.
"""
import logging
import ssl
import aiohttp
from playwright.async_api import Page

from config.settings import SOLVECAPTCHA_API_KEY, HCAPTCHA_SELECTORS

logger = logging.getLogger(__name__)

async def detect_and_solve_captcha(page: Page):
    """
    Detect if a captcha is present and attempt to solve it.
    
    Args:
        page: The Playwright page object
        
    Returns:
        bool: True if captcha was solved, False otherwise
    """
    logger.info("Checking for captcha...")
    
    try:
        # Wait briefly for potential hCaptcha to appear
        for selector in HCAPTCHA_SELECTORS:
            try:
                # Wait for element with state: 'attached' instead of default 'visible'
                await page.wait_for_selector(
                    selector, 
                    state='attached',
                    timeout=10000
                )
                
                logger.info(f"Potential captcha element found with selector: {selector}")
                
                # Then check specifically for our element
                hcaptcha_exists = await page.evaluate('''
                    !!document.querySelector('div#h-captcha.h-captcha')
                ''')
                
                if hcaptcha_exists:
                    logger.info("hCaptcha detected, attempting to solve...")
                    # Extract the site key from the data-sitekey attribute
                    site_key = await page.evaluate('''
                        document.querySelector('div#h-captcha.h-captcha').getAttribute('data-sitekey')
                    ''')
                    
                    if site_key:
                        logger.info(f"Found hCaptcha site key: {site_key}")
                        return await solve_hcaptcha(page, site_key, page.url)
                    else:
                        logger.error("Could not find hCaptcha site key")
                        return False
            except Exception as e:
                # Continue checking other selectors if this one wasn't found
                logger.debug(f"Selector {selector} not found: {str(e)}")
                continue
                
        logger.info("No captcha detected")
        return True
            
    except Exception as e:
        logger.error(f"Error in captcha detection: {str(e)}")
        return False

async def solve_hcaptcha(page: Page, site_key: str, site_url: str) -> bool:
    """
    Solve hCaptcha using SolveCaptcha service.
    
    Args:
        page: The Playwright page object
        site_key: The site key for the hCaptcha
        site_url: The URL of the page containing the captcha
        
    Returns:
        bool: True if solved successfully, False otherwise
    """
    logger.info(f"Attempting to solve hCaptcha with site key: {site_key}")
    
    try:
        # Construct the API URL with query parameters
        base_url = "https://api.solvecaptcha.com/in.php"
        params = {
            "key": SOLVECAPTCHA_API_KEY,
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": site_url,
            "json": 1
        }
        
        # Create SSL context that ignores certificate verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Make the initial request
            async with session.get(base_url, params=params) as response:
                result = await response.json()
                logger.info(f"SolveCaptcha raw response: {result}")
                
                if result.get('status') == 1 and result.get('request'):
                    solution = result['request']
                    logger.info("Successfully got hCaptcha solution")

                    # Add a delay before proceeding
                    logger.info("Waiting 3 seconds before applying solution...")
                    await page.wait_for_timeout(3000)
                    
                    # Execute JS to set the hcaptcha response
                    await page.evaluate(f'''
                        (function() {{
                            console.log('Starting hCaptcha solution injection...');
                            
                            // Function to find and set input value
                            function setInputValue(selector, value) {{
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(el => {{
                                    console.log('Setting value for element:', el);
                                    el.value = value;
                                    // Trigger multiple types of events
                                    ['change', 'input'].forEach(eventType => {{
                                        el.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
                                    }});
                                }});
                                return elements.length > 0;
                            }}

                            // Try multiple selectors for hCaptcha response
                            const selectors = [
                                'textarea[name="h-captcha-response"]',
                                '[name="h-captcha-response"]',
                                '#h-captcha-response',
                                'input[name="g-recaptcha-response"]',
                                '[name="g-recaptcha-response"]',
                                '#g-recaptcha-response',
                                '.h-captcha-response',
                                '.g-recaptcha-response'
                            ];

                            let found = false;
                            selectors.forEach(selector => {{
                                if (setInputValue(selector, "{solution}")) {{
                                    console.log('Successfully set value for selector:', selector);
                                    found = true;
                                }}
                            }});

                            // Try to find and trigger hCaptcha widget
                            if (window.hcaptcha) {{
                                console.log('hCaptcha widget found, attempting to execute...');
                                try {{
                                    window.hcaptcha.execute();
                                    console.log('hCaptcha execute called successfully');
                                }} catch (e) {{
                                    console.log('Error executing hcaptcha:', e);
                                }}
                            }}

                            // Look for potential callback functions
                            const potentialCallbacks = [
                                'hcaptchaCallback',
                                'onHcaptchaSuccess',
                                'onVerify',
                                'onSuccess',
                                'onPass',
                                'callback',
                                'handleCaptchaResponse'
                            ];

                            potentialCallbacks.forEach(cbName => {{
                                if (typeof window[cbName] === 'function') {{
                                    console.log('Found callback:', cbName);
                                    try {{
                                        window[cbName]('{solution}');
                                        console.log('Successfully called callback:', cbName);
                                    }} catch (e) {{
                                        console.log('Error calling callback ' + cbName + ':', e);
                                    }}
                                }}
                            }});

                            // Try to find the hCaptcha iframe and interact with it
                            const hcaptchaIframe = document.querySelector('iframe[src*="hcaptcha.com"]');
                            if (hcaptchaIframe) {{
                                console.log('Found hCaptcha iframe, attempting to interact...');
                                try {{
                                    const iframeWindow = hcaptchaIframe.contentWindow;
                                    if (iframeWindow && iframeWindow.postMessage) {{
                                        iframeWindow.postMessage({{ 
                                            response: '{solution}',
                                            type: 'hcaptcha-response'
                                        }}, '*');
                                        console.log('Posted message to hCaptcha iframe');
                                    }}
                                }} catch (e) {{
                                    console.log('Error interacting with iframe:', e);
                                }}
                            }}

                            console.log('Injection process completed. Found elements:', found);
                            return found;
                        }})();
                    ''')

                    # Add a delay after setting the solution
                    await page.wait_for_timeout(2000)
                    
                    # If there's a useragent in the response, update the browser's user agent
                    if result.get('useragent'):
                        logger.info(f"Setting useragent from SolveCaptcha: {result['useragent']}")
                        await page.set_extra_http_headers({
                            'User-Agent': result['useragent']
                        })
                    
                    return True
                else:
                    logger.error(f"Unexpected SolveCaptcha result format: {result}")
                    return False
                
    except Exception as e:
        logger.error(f"Error solving hCaptcha: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Error response: {e.response}")
        return False