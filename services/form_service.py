"""
Services for extracting and filling form fields.
"""
import logging
import random
from playwright.async_api import Page

from models.form_models import FormField, Option
from utils.human_simulation import human_like_delay, human_like_typing
from config.settings import APPLICATION_FORM_SELECTOR, SUBMIT_BUTTON_SELECTOR, RESUME_PATH
from services.captcha_service import detect_and_solve_captcha

logger = logging.getLogger(__name__)

async def get_input_type(element) -> str:
    """
    Determine the input type of an element.
    
    Args:
        element: The Playwright element to check
        
    Returns:
        str: The determined input type
    """
    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
    
    if tag_name == 'textarea':
        return 'textarea'
    elif tag_name == 'select':
        return 'select'
    elif tag_name == 'input':
        input_type = await element.get_attribute('type') or 'text'
        return f'input_{input_type}'
    return 'unknown'

async def get_select_options(page, input_name: str) -> list[Option]:
    """
    Extract all options from a select element given its name attribute.
    
    Args:
        page: The Playwright page object
        input_name: The name attribute of the select element
        
    Returns:
        list[Option]: List of options in the select element
    """
    logger.info(f"Extracting options for select element: {input_name}")
    options: list[Option] = []
    
    # Query all option elements within the select
    select_options = await page.query_selector_all(f'select[name="{input_name}"] option')
    
    for option in select_options:
        # Skip the first option if it's a placeholder (value is usually empty)
        value = await option.get_attribute('value')
        if not value:
            continue
            
        label = await option.inner_text()
        options.append(Option(label.strip(), value.strip()))
        logger.debug(f"Found option - Label: {label}, Value: {value}")
    
    logger.info(f"Found {len(options)} options for {input_name}")
    return options

async def get_choice_options(page, input_name: str, input_type: str) -> list[Option]:
    """
    Extract all options from a group of radio buttons or checkboxes given their name attribute.
    
    Args:
        page: The Playwright page object
        input_name: The name attribute of the inputs
        input_type: The type of the inputs (radio or checkbox)
        
    Returns:
        list[Option]: List of options in the group
    """
    logger.info(f"Extracting options for {input_type} group: {input_name}")
    options: list[Option] = []
    
    # Escape special characters in the input name for the selector
    escaped_name = input_name.replace('[', '\\[').replace(']', '\\]')
    
    # Query all inputs with the given name and type
    inputs = await page.query_selector_all(f'input[type="{input_type}"][name="{escaped_name}"]')
    
    for input_el in inputs:
        value = await input_el.get_attribute('value')
        # Use the value as the label
        options.append(Option(value.strip(), value.strip()))
        logger.debug(f"Found {input_type} option - Label: {value}, Value: {value}")
    
    logger.info(f"Found {len(options)} options for {input_type} group {input_name}")
    return options

async def extract_form_fields(page) -> list[FormField]:
    """
    Extract all required form fields from the application form.
    
    Args:
        page: The Playwright page object
        
    Returns:
        list[FormField]: List of required form fields with their properties
    """
    logger.info("Extracting required form fields...")
    form_selector = APPLICATION_FORM_SELECTOR
    all_ul = await page.query_selector_all(f"{form_selector} ul")
    required_fields: list[FormField] = []
    
    for ul in all_ul:
        all_li = await ul.query_selector_all('li[class*="application-question"]')
        for li in all_li:
            # Get div with class="application-label"
            application_label_wrapper = await li.query_selector("div.application-label")
            required_field = await application_label_wrapper.query_selector("span.required")
            
            if required_field:
                label = await application_label_wrapper.inner_text()
                label = label.split('✱')[0].strip()
                
                # Detect the div.application-field under li
                application_field = await li.query_selector("div.application-field")
                if application_field:
                    # Get the input field under the application_field
                    input_field = await application_field.query_selector("input, textarea, select")
                    if input_field:
                        input_type = await get_input_type(input_field)
                        input_name = await input_field.get_attribute("name")

                        options = []
                        if input_type == 'select':
                            options = await get_select_options(page, input_name)
                        elif input_type in ['input_radio', 'input_checkbox']:
                            # Extract the actual input type (radio or checkbox)
                            actual_type = input_type.split('_')[1]
                            options = await get_choice_options(page, input_name, actual_type)
                            
                        required_fields.append(FormField(label, input_type, input_name, options))
                        truncated_label = (label[:20] + "...") if len(label) > 20 else label
                        logger.info(f"Required field found - Label: {truncated_label}, Type: {input_type}, Name: {input_name}")
    
    logger.info(f"Found {len(required_fields)} required fields in total")
    return required_fields

async def is_debounced_field(page, field):
    """
    Check if a field is a debounced field (has class 'location-input').
    
    Args:
        page: The Playwright page object
        field: The form field to check
        
    Returns:
        bool: True if the field is debounced, False otherwise
    """
    try:
        # Construct a selector that matches the field's name and has the class 'location-input'
        selector = f'input[name="{field.escaped_name}"].location-input'
        element = await page.query_selector(selector)
        return element is not None
    except Exception:
        return False

async def handle_debounced_field(page, field, value):
    """
    Special handling for debounced fields like location inputs.
    
    Args:
        page: The Playwright page object
        field: The form field to fill
        value: The value to enter
    """
    from services.captcha_service import solve_hcaptcha
    
    logger.info(f"Handling debounced field: {field.input_name} with value: {value}")
    
    try:
        # 1. First solve hCaptcha if needed
        logger.info("Pre-emptively solving hCaptcha for location search...")
        
        hcaptcha_input = await page.query_selector('#hcaptchaResponseInput')
        
        if hcaptcha_input:
            site_key = await page.evaluate('''
                () => {
                    const hcaptchaDiv = document.querySelector('div#h-captcha.h-captcha');
                    return hcaptchaDiv ? hcaptchaDiv.getAttribute('data-sitekey') : null;
                }
            ''')
            
            if site_key:
                logger.info(f"Found hCaptcha site key: {site_key}")
                captcha_solved = await solve_hcaptcha(page, site_key, page.url)
                
                if captcha_solved:
                    logger.info("Successfully pre-solved hCaptcha")
                    await page.wait_for_timeout(1000)
                else:
                    logger.warning("Failed to pre-solve hCaptcha")
        
        # 2. Get the location input field
        element_selector = f'input[name="{field.escaped_name}"]'
        element = await page.wait_for_selector(element_selector)
        
        if not element:
            logger.warning(f"Element not found for debounced field: {field.input_name}")
            return
        
        # 3. Fill the input field 
        await element.scroll_into_view_if_needed()
        await element.fill("")
        await human_like_typing(element, value)
        
        # 4. Wait a fixed time for the debounce (500ms plus buffer)
        await page.wait_for_timeout(700)
        
        # 5. Use basic JavaScript to trigger the search manually
        await page.evaluate('''
            () => {
                if (typeof debouncedGetLocationResultsByInput === 'function') {
                    debouncedGetLocationResultsByInput();
                }
            }
        ''')
        
        # 6. Wait for results to load
        await page.wait_for_timeout(1500)
        
        # 7. Check if any options are available and select the first one
        has_options = await page.evaluate('''
            () => {
                const options = document.querySelectorAll('.dropdown-location');
                return options.length > 0;
            }
        ''')
        
        if has_options:
            logger.info("Found dropdown options, selecting first one")
            
            # Use direct jQuery click as in original code
            success = await page.evaluate('''
                () => {
                    try {
                        $('.dropdown-location:first').mousedown();
                        return true;
                    } catch (e) {
                        console.error("Error clicking option:", e);
                        return false;
                    }
                }
            ''')
            
            if success:
                logger.info("Successfully selected location option")
            else:
                logger.warning("Failed to select location option")
        else:
            logger.info("No location options found, using raw input")
        
        # 8. Ensure we move to the next field
        await page.wait_for_timeout(500)
        await element.press("Tab")
        
    except Exception as e:
        logger.error(f"Error handling debounced field {field.input_name}: {str(e)}")
        # Just try to use the raw value and move on
        try:
            element = await page.query_selector(f'input[name="{field.escaped_name}"]')
            if element:
                await element.fill(value)
                await element.press("Tab")
        except Exception:
            pass
    """
    Special handling for debounced fields like location inputs with precise option selection.
    """
    from services.captcha_service import solve_hcaptcha

    # Define the search delay matching the JavaScript value
    SEARCH_DELAY = 500  # Milliseconds, matching the JS code
    
    logger.info(f"Handling debounced field: {field.input_name} with value: {value}")
    
    try:
        # Pre-emptively solve hCaptcha
        logger.info("Pre-emptively solving hCaptcha for location search...")
        
        hcaptcha_input = await page.query_selector('#hcaptchaResponseInput')
        
        if hcaptcha_input:
            logger.info("Found hCaptcha response input field, attempting to solve...")
            
            site_key = await page.evaluate('''
                () => {
                    const hcaptchaDiv = document.querySelector('div#h-captcha.h-captcha');
                    return hcaptchaDiv ? hcaptchaDiv.getAttribute('data-sitekey') : null;
                }
            ''')
            
            if site_key:
                logger.info(f"Found hCaptcha site key: {site_key}")
                captcha_solved = await solve_hcaptcha(page, site_key, page.url)
                
                if captcha_solved:
                    logger.info("Successfully pre-solved hCaptcha")
                    await page.wait_for_timeout(1000)
                else:
                    logger.warning("Failed to pre-solve hCaptcha")
        
        # Interact with location field
        element_selector = f'input[name="{field.escaped_name}"]'
        element = await page.wait_for_selector(element_selector)
        
        if not element:
            logger.warning(f"Element not found for debounced field: {field.input_name}")
            return
        
        await element.scroll_into_view_if_needed()
        
        # Clear and fill the field
        await element.fill("")
        await human_like_typing(element, value)
        
        # Wait for the debounce delay
        logger.info(f"Waiting for debounce delay ({SEARCH_DELAY}ms)...")
        await page.wait_for_timeout(800)  # Wait a bit longer than the actual delay to be safe
        
        # Wait for dropdown to become visible
        try:
            logger.info("Waiting for dropdown to appear...")
            dropdown_visible = await page.wait_for_function('''
                () => {
                    const container = document.querySelector('.dropdown-container');
                    return container && window.getComputedStyle(container).display !== 'none';
                }
            ''', timeout=6000)
            
            if dropdown_visible:
                logger.info("Dropdown appeared")
                
                # Wait for options to load (wait for AJAX completion)
                await page.wait_for_function('''
                    () => {
                        // Either options have loaded or the "no results" message is shown
                        return document.querySelectorAll('.dropdown-location').length > 0 || 
                               (document.querySelector('.dropdown-no-results') && 
                                window.getComputedStyle(document.querySelector('.dropdown-no-results')).display !== 'none');
                    }
                ''', timeout=5000)
                
                # Check if we have any options
                options_count = await page.evaluate('''
                    () => document.querySelectorAll('.dropdown-location').length
                ''')
                
                logger.info(f"Found {options_count} location options")
                
                if options_count > 0:
                    # Get the first option details
                    first_option = await page.evaluate('''
                        () => {
                            const option = document.querySelector('.dropdown-location');
                            if (option) {
                                return {
                                    id: option.id,
                                    text: option.textContent,
                                    index: option.id.split('-')[1]
                                };
                            }
                            return null;
                        }
                    ''')
                    
                    if first_option:
                        logger.info(f"First option: {first_option}")
                        
                        # Instead of clicking, which may be unreliable, execute the exact same actions 
                        # that the JavaScript event handler would do
                        await page.evaluate(f'''
                            () => {{
                                // Get the searchedLocations array (should be populated by now)
                                if (typeof searchedLocations !== 'undefined' && searchedLocations) {{
                                    // Hide dropdown
                                    $('.dropdown-container').css({{ display: 'none' }});
                                    
                                    // Set input value
                                    $('input.location-input').val('{first_option["text"]}');
                                    
                                    // Set hidden selected-location field
                                    const selectedIndex = {first_option["index"]};
                                    $('#selected-location').val(JSON.stringify(searchedLocations[selectedIndex]));
                                    
                                    // Empty dropdown
                                    $('.dropdown-results').empty();
                                    $('.dropdown-no-results').css({{ display: 'none' }});
                                    $('.dropdown-loading-results').css({{ display: 'none' }});
                                }}
                            }}
                        ''')
                        
                        logger.info("Successfully selected location using JavaScript handlers")
                    else:
                        logger.warning("Could not get details of the first option")
                else:
                    logger.warning("No options found in dropdown")
            else:
                logger.warning("Dropdown did not appear")
        
        except Exception as e:
            logger.error(f"Error handling dropdown: {str(e)}")
            # Fallback - just use the raw value
            await element.press("Tab")
            logger.info("Using raw input value as fallback")
        
    except Exception as e:
        logger.error(f"Error handling debounced field {field.input_name}: {str(e)}")

async def fill_form_fields(page: Page, required_fields: list[FormField], suggested_values: dict):
    """
    Fill form fields with suggested values.
    
    Args:
        page: The Playwright page object
        required_fields: List of form fields to fill
        suggested_values: Dictionary of field names to values
    """
    logger.info("Starting to fill form fields...")
    
    for field in required_fields:
        # Add human-like delay between fields
        await human_like_delay(page)
        
        # Handle file inputs
        if field.is_file_input:
            try:
                logger.info(f"Attempting to upload resume from: {RESUME_PATH}")
                
                # Escape special characters in the input name for the selector
                escaped_name = field.escaped_name
                file_input = await page.wait_for_selector(f'input[name="{escaped_name}"]')
                
                if file_input:
                    await file_input.set_input_files(RESUME_PATH)
                    logger.info(f"Successfully uploaded resume for field: {field.input_name}")
                    
                    # Wait for the resume parsing request to complete
                    try:
                        async with page.expect_response(
                            lambda response: 'parseResume' in response.url,
                            timeout=30000  # 30 seconds timeout
                        ) as response_info:
                            await response_info.value
                        logger.info("Resume parsing completed successfully")
                    except Exception as e:
                        logger.error(f"Error waiting for resume parsing: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error uploading resume for field {field.input_name}: {str(e)}")
            continue

        value = suggested_values.get(field.input_name)
        if not value:
            logger.warning(f"No suggested value found for field: {field.input_name}")
            continue

        logger.info(f"Filling field '{field.input_name}' with value: {value}")
        
        try:
            # Check if field is a debounced field (location input)
            if await is_debounced_field(page, field):
                logger.info(f"Detected debounced field: {field.input_name}")
                await handle_debounced_field(page, field, value)
                continue
            
            # Determine the appropriate selector based on field type
            element_selector = (
                f'textarea[name="{field.input_name}"]' if field.input_type == 'textarea'
                else f'select[name="{field.input_name}"]' if field.input_type == 'select'
                else f'input[name="{field.input_name}"]'
            )
            
            # Wait for the element to be available
            element = await page.wait_for_selector(element_selector)
            if not element:
                logger.warning(f"Element not found for field: {field.input_name}")
                continue

            # Scroll element into view before interacting
            await element.scroll_into_view_if_needed()
            
            # Check current value only for text inputs and textareas
            if field.is_text_input:
                current_value = await element.input_value()
                if current_value.strip():
                    logger.info(f"Field '{field.input_name}' already has value: {current_value}. Skipping...")
                    continue
            
            # Handle different input types
            if field.input_type == 'textarea':
                await human_like_typing(element, value)
            
            elif field.input_type == 'select':
                await page.select_option(f'select[name="{field.input_name}"]', value)
            
            elif field.input_type.startswith('input_'):
                input_type = field.input_type.split('_')[1]
                if input_type in ['radio', 'checkbox']:
                    escaped_name = field.escaped_name
                    await page.check(f'input[type="{input_type}"][name="{escaped_name}"][value="{value}"]')
                else:
                    # For text inputs, type more naturally with random delays
                    await human_like_typing(element, value)
            
        except Exception as e:
            logger.error(f"Error filling field {field.input_name}: {str(e)}")

    logger.info("Form filling completed.")

async def submit_application(page: Page):
    """
    Click the submit application button and handle any captchas.
    
    Args:
        page: The Playwright page object
    """
    logger.info("Attempting to submit application...")
    
    try:
        # Find and click the submit button
        submit_button = await page.wait_for_selector(SUBMIT_BUTTON_SELECTOR, timeout=5000)
        if submit_button:
            await submit_button.click()
            logger.info("Submit button clicked successfully")
            
            # Check for captcha and try to solve it
            await detect_and_solve_captcha(page)
            
            # Wait for submission to complete
            logger.info("Waiting for submission to complete (20 seconds)")
            await page.wait_for_timeout(20000)  # Wait for 20 seconds
            
            # Check for success indicators
            # This could be customized based on the specific confirmation patterns
            success_indicators = [
                "thank you",
                "application received",
                "application submitted",
                "confirmation"
            ]
            
            for indicator in success_indicators:
                has_indicator = await page.evaluate(f'''
                    document.body.innerText.toLowerCase().includes('{indicator}')
                ''')
                if has_indicator:
                    logger.info(f"Success indicator found: '{indicator}'")
                    logger.info("Application successfully submitted")
                    return True
            
            logger.warning("No success indicators found, submission status unclear")
            return False
            
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        return False