"""
Input helper functions for better terminal navigation.
Provides retry, back button, and validation capabilities.
"""

from typing import Optional, Callable, Any, List
import os


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_input_with_back(prompt: str, allow_back: bool = True) -> Optional[str]:
    """
    Get user input with option to go back.
    
    Args:
        prompt: Input prompt to display
        allow_back: Whether to allow 'b' or 'back' to return None
    
    Returns:
        User input or None if user wants to go back
    """
    if allow_back:
        print(f"\n(Type 'b' or 'back' to go back)")
    
    user_input = input(f"{prompt}: ").strip()
    
    if allow_back and user_input.lower() in ['b', 'back']:
        return None
    
    return user_input


def get_validated_input(
    prompt: str,
    validator: Callable[[str], bool],
    error_message: str = "Invalid input. Please try again.",
    allow_back: bool = True,
    allow_retry: bool = True
) -> Optional[str]:
    """
    Get user input with validation and retry capability.
    
    Args:
        prompt: Input prompt
        validator: Function that returns True if input is valid
        error_message: Message to show on invalid input
        allow_back: Allow going back
        allow_retry: Allow retry on invalid input
    
    Returns:
        Validated input or None if user goes back
    """
    while True:
        user_input = get_input_with_back(prompt, allow_back)
        
        if user_input is None:
            return None
        
        if validator(user_input):
            return user_input
        
        print(f"\n[ERROR] {error_message}")
        
        if not allow_retry:
            return None
        
        retry = input("\nTry again? (y/n): ").strip().lower()
        if retry != 'y':
            return None


def get_choice(
    prompt: str,
    options: dict,
    allow_back: bool = True,
    show_options: bool = True
) -> Optional[str]:
    """
    Get user choice from a dictionary of options.
    
    Args:
        prompt: Prompt to display
        options: Dictionary of valid choices {key: description}
        allow_back: Allow going back
        show_options: Whether to display options
    
    Returns:
        Selected key or None
    """
    if show_options:
        print("\n" + "-"*70)
        for key, desc in options.items():
            print(f"{key}. {desc}")
        print("-"*70)
    
    while True:
        choice = get_input_with_back(prompt, allow_back)
        
        if choice is None:
            return None
        
        if choice in options:
            return choice
        
        print(f"\n[ERROR] Invalid choice. Please select from: {', '.join(options.keys())}")


def get_multi_choice(
    prompt: str,
    options: dict,
    min_selections: int = 1,
    max_selections: Optional[int] = None,
    allow_back: bool = True
) -> Optional[List[str]]:
    """
    Get multiple selections from user.
    
    Args:
        prompt: Prompt to display
        options: Dictionary of valid choices
        min_selections: Minimum number of selections required
        max_selections: Maximum selections allowed (None = unlimited)
        allow_back: Allow going back
    
    Returns:
        List of selected keys or None
    """
    print("\n" + "-"*70)
    for key, desc in options.items():
        print(f"{key}. {desc}")
    print("-"*70)
    print(f"\nSelect {min_selections} or more items (comma-separated, e.g., 1,2,3)")
    
    while True:
        user_input = get_input_with_back(prompt, allow_back)
        
        if user_input is None:
            return None
        
        # Parse selections
        selections = [s.strip() for s in user_input.split(',')]
        
        # Validate
        invalid = [s for s in selections if s not in options]
        if invalid:
            print(f"\n[ERROR] Invalid choices: {', '.join(invalid)}")
            continue
        
        # Remove duplicates
        selections = list(dict.fromkeys(selections))
        
        # Check count
        if len(selections) < min_selections:
            print(f"\n[ERROR] Please select at least {min_selections} item(s)")
            continue
        
        if max_selections and len(selections) > max_selections:
            print(f"\n[ERROR] Please select no more than {max_selections} item(s)")
            continue
        
        return selections


def get_number(
    prompt: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    default: Optional[float] = None,
    allow_back: bool = True
) -> Optional[float]:
    """
    Get numeric input with validation.
    
    Args:
        prompt: Input prompt
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default: Default value if user presses Enter
        allow_back: Allow going back
    
    Returns:
        Number or None
    """
    full_prompt = prompt
    if default is not None:
        full_prompt += f" (default: {default})"
    
    while True:
        user_input = get_input_with_back(full_prompt, allow_back)
        
        if user_input is None:
            return None
        
        # Check for default
        if user_input == "" and default is not None:
            return default
        
        # Try to convert to number
        try:
            value = float(user_input)
            
            # Validate range
            if min_value is not None and value < min_value:
                print(f"\n[ERROR] Value must be >= {min_value}")
                continue
            
            if max_value is not None and value > max_value:
                print(f"\n[ERROR] Value must be <= {max_value}")
                continue
            
            return value
            
        except ValueError:
            print(f"\n[ERROR] Please enter a valid number")


def get_date(
    prompt: str,
    allow_empty: bool = False,
    default_message: str = "latest",
    allow_back: bool = True
) -> Optional[str]:
    """
    Get date input in YYYY-MM-DD format.
    
    Args:
        prompt: Input prompt
        allow_empty: Allow empty input (return None)
        default_message: Message to show for empty input
        allow_back: Allow going back
    
    Returns:
        Date string or None
    """
    from core.utils import validate_date_format
    
    full_prompt = prompt
    if allow_empty:
        full_prompt += f" (press Enter for {default_message})"
    
    while True:
        user_input = get_input_with_back(full_prompt, allow_back)
        
        if user_input is None:
            return None
        
        if user_input == "" and allow_empty:
            return None
        
        if validate_date_format(user_input):
            return user_input
        
        print(f"\n[ERROR] Invalid date format. Please use YYYY-MM-DD")


def confirm_action(prompt: str = "Continue?", default: bool = True) -> bool:
    """
    Get yes/no confirmation from user.
    
    Args:
        prompt: Confirmation prompt
        default: Default value if user presses Enter
    
    Returns:
        True for yes, False for no
    """
    options = "Y/n" if default else "y/N"
    user_input = input(f"\n{prompt} ({options}): ").strip().lower()
    
    if user_input == "":
        return default
    
    return user_input in ['y', 'yes']


def pause(message: str = "Press Enter to continue..."):
    """Pause and wait for user to press Enter"""
    input(f"\n{message}")


def print_success(message: str):
    """Print success message"""
    print(f"\n[SUCCESS] {message}")


def print_error(message: str):
    """Print error message"""
    print(f"\n[ERROR] {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"\n[WARNING] {message}")


def print_info(message: str):
    """Print info message"""
    print(f"\n[INFO] {message}")


def print_section_header(title: str, width: int = 70):
    """Print a section header"""
    print("\n" + "="*width)
    print(title.center(width))
    print("="*width)


def print_subsection_header(title: str, width: int = 70):
    """Print a subsection header"""
    print("\n" + "-"*width)
    print(title)
    print("-"*width)