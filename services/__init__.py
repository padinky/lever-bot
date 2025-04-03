from services.browser_service import browse_with_proxy
from services.form_service import extract_form_fields, fill_form_fields, submit_application
from services.captcha_service import detect_and_solve_captcha, solve_hcaptcha
from services.ai_service import suggest_field_values, mock_suggest_field_values

__all__ = [
    'browse_with_proxy',
    'extract_form_fields',
    'fill_form_fields',
    'submit_application',
    'detect_and_solve_captcha',
    'solve_hcaptcha',
    'suggest_field_values',
    'mock_suggest_field_values'
]