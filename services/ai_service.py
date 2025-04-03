"""
AI services for generating form field values.
"""
import logging
import json
import os
import openai
from typing import Dict, List

from config.settings import OPENAI_API_KEY, USER_METADATA_PATH
from models.form_models import FormField

logger = logging.getLogger(__name__)

def mock_suggest_field_values(required_fields: List[FormField]) -> Dict[str, str]:
    """
    Mock function to simulate suggest_field_values for testing purposes.
    
    Args:
        required_fields: List of form fields to suggest values for
        
    Returns:
        Dict[str, str]: Dictionary of field names to suggested values
    """
    logger.info("Using mock values for form fields")
    
    mock_values = {
        "opportunityLocationId": "5ea282ab-de75-4861-bd77-8a303a3ec812",
        "resume": "resume.pdf",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "5173014578",
        "cards[084c182c-cccc-44f0-af81-18f2c91cf7db][field0]": "Unspecified",
        "cards[084c182c-cccc-44f0-af81-18f2c91cf7db][field1]": "New York",
        "cards[084c182c-cccc-44f0-af81-18f2c91cf7db][field2]": "NY",
        "cards[084c182c-cccc-44f0-af81-18f2c91cf7db][field3]": "10013",
        "cards[1bcdc31d-7a20-4dca-ac48-d0f0e3ce518b][field0]": "Yes",
        "cards[c6532970-bc1e-40b5-8d79-af03eaa8e7c7][field0]": "No",
        "cards[899b8aae-97a5-4a12-a40a-55f894160cb9][field0]": "Yes",
        "cards[899b8aae-97a5-4a12-a40a-55f894160cb9][field1]": "Yes",
        "cards[899b8aae-97a5-4a12-a40a-55f894160cb9][field2]": "Yes",
        "cards[899b8aae-97a5-4a12-a40a-55f894160cb9][field3]": "Yes",
        "cards[7fc211fe-7cee-42db-9263-c17a9ccff9f3][field0]": "Yes",
        "cards[7fc211fe-7cee-42db-9263-c17a9ccff9f3][field1]": "No",
        "cards[7fc211fe-7cee-42db-9263-c17a9ccff9f3][field2]": "No",
        "cards[7fc211fe-7cee-42db-9263-c17a9ccff9f3][field3]": "No",
        "cards[7fc211fe-7cee-42db-9263-c17a9ccff9f3][field4]": "No"
    }

    return mock_values

def suggest_field_values(required_fields: list[FormField]) -> dict:
    api_key = OPENAI_API_KEY
    logging.info("Generating prompt to suggest field values...")
    try:
        with open(USER_METADATA_PATH, "r") as f:
            user_metadata = f.read().strip()
    except FileNotFoundError:
        print("⚠️ Error: 'user_metadata.txt' file not found.")
        return {}

    def generate_prompt(user_metadata: str, required_fields: list[FormField]) -> str:
        prompt = "You are an AI assistant that helps fill job application forms based on user metadata.\n\n"
        prompt += "Here is the user metadata:\n"
        prompt += user_metadata + "\n\n"
        prompt += "Based on the above metadata, suggest appropriate values for the following required fields:\n"

        for field in required_fields:
            prompt += f"- **Label:** {field.label}\n"
            prompt += f"  - **Type:** {field.input_type}\n"
            prompt += f"  - **Name:** {field.input_name}\n"
            if field.options:
                prompt += "  - **Options:**\n"
                for option in field.options:
                    prompt += f"    - **Label:** {option.option_label}, **Value:** {option.option_value}\n"

        prompt += (
            "\nPlease provide the suggested values in JSON format, like this:\n"
            "```json\n"
            "{\n"
            '  "opportunityLocationId": "5ea282ab-de75-4861-bd77-8a303a3ec812",\n'
            '  "resume": "resume.pdf",\n'
            '  "name": "John Doe",\n'
            '  "email": "johndoe@example.com",\n'
            '  "phone": "+1 234-567-8901",\n'
            '  "cards[084c182c-cccc-44f0-af81-18f2c91cf7db][field0]": "123 Main St, New York, NY"\n'
            "}\n"
            "```"
        )
        prompt += (
            "\nEnsure that all fields are filled using the following rules:\n"
            "- If the field is a **text** or **textarea**, fill it with `'Unspecified'` if no meaningful value is found.\n"
            "- If the field is a **select**, **radio**, or **checkbox**, choose the **first available option** from the list.\n"
            "- Do NOT leave any field empty.\n"
            "- Return the result as a JSON object **without any explanations or extra text**."
        )
        return prompt

    # Generate the prompt
    prompt = generate_prompt(user_metadata, required_fields)

    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)

    # Make API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )

    # Print the raw response for debugging
    logging.info("🔍 Raw OpenAI Response:")
    logging.info(response.choices[0].message.content)

    # Extract and parse JSON response
    suggested_values = response.choices[0].message.content.strip("```json").strip("```")
    try:
        return json.loads(suggested_values)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON Decode Error: {e}")
        return {}
