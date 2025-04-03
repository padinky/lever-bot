"""
Data models for form elements and their properties.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Option:
    """Represents a selectable option in a form field."""
    option_label: str
    option_value: str

@dataclass
class FormField:
    """Represents a form field with its properties."""
    label: str
    input_type: str
    input_name: str
    options: List[Option] = field(default_factory=list)
    
    @property
    def is_text_input(self) -> bool:
        """Check if the field is a text input."""
        return self.input_type in ['input_text', 'input_email', 'textarea']
    
    @property
    def is_selection(self) -> bool:
        """Check if the field is a selection type (select, radio, checkbox)."""
        return self.input_type in ['select', 'input_radio', 'input_checkbox']
    
    @property
    def is_file_input(self) -> bool:
        """Check if the field is a file input."""
        return self.input_type == 'input_file'
    
    @property
    def escaped_name(self) -> str:
        """Return the input name with escaped brackets for CSS selectors."""
        return self.input_name.replace('[', '\\[').replace(']', '\\]')
    
    def get_first_option_value(self) -> Optional[str]:
        """Get the first option value if options exist."""
        return self.options[0].option_value if self.options else None