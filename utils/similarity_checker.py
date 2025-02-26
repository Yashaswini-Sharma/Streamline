import pandas as pd
from difflib import SequenceMatcher
import json

def string_similarity(a, b):
    """Calculate basic string similarity."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_item_variations(item, model):
    """Get semantic variations of an item name."""
    try:
        prompt = f"""
        Generate 3-5 common alternative names or descriptions for '{item}' as a comma-separated list.
        Only return the list, nothing else.
        Example: if input is "laptop", return "notebook computer, portable computer, personal computer, pc"
        """
        response = model.generate_content(prompt)
        variations = [v.strip() for v in response.text.split(',')]
        return variations
    except Exception as e:
        print(f"Error generating variations: {e}")
        return [item]

def verify_item_against_goals(item_description, goals, model):
    """
    Compare an item against company goals.
    
    Args:
        item_description (str): The description of the item to check
        goals (list or pd.DataFrame): Company goals to check against
        model: The Gemini model instance
    """
    # Convert goals to list if it's a DataFrame
    goal_list = goals if isinstance(goals, list) else goals['Goals'].tolist()
    
    # Clean and normalize the item description
    item_description = str(item_description).lower().strip()
    
    # Get variations of the item description
    variations = get_item_variations(item_description, model)
    
    # Check against each goal
    for goal in goal_list:
        goal = str(goal).lower().strip()
        if goal in item_description or item_description in goal:
            return False, goal
        
        # Check variations
        for variation in variations:
            if variation.lower().strip() in goal or goal in variation.lower().strip():
                return False, goal
    
    return True, None
