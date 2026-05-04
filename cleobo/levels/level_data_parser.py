"""
Parser for loading level data from Lua files.
Converts Lua table syntax to Python dictionaries.
"""

import json
import re
from pathlib import Path

def parse_lua_level(lua_filepath):
    """
    Parse a Lua file and extract level data.
    Returns a dictionary with all level data keyed by level name (lvl1, lvl2, etc).
    """
    with open(lua_filepath, 'r') as f:
        content = f.read()
    
    levels = {}
    
    # Find all level definitions (local lvl1 = {...}, local lvl2 = {...}, etc)
    level_pattern = r'local\s+(\w+)\s*=\s*\{(.*?)\n\}'
    
    for match in re.finditer(level_pattern, content, re.DOTALL):
        level_name = match.group(1)
        level_content = match.group(2)
        
        # Parse the level data into a Python dict
        level_data = _parse_table(level_content)
        levels[level_name] = level_data
    
    return levels


def _parse_table(content):
    """
    Recursively parse Lua table content into Python dict.
    Handles basic types: numbers, strings, tables, and lists.
    Uses depth tracking to properly handle nested structures.
    """
    result = {}
    
    # Remove comments and excess whitespace
    content = re.sub(r'--.*?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s+', ' ', content)
    
    # Manually split by key-value pairs, respecting nesting
    i = 0
    while i < len(content):
        # Skip whitespace and commas
        while i < len(content) and content[i] in ' ,':
            i += 1
        if i >= len(content):
            break
        
        # Parse key name
        key_match = re.match(r'(\w+)\s*=', content[i:])
        if not key_match:
            break
        
        key = key_match.group(1)
        i += key_match.end()
        
        # Skip whitespace after =
        while i < len(content) and content[i] in ' ':
            i += 1
        
        # Parse value - can be a table, string, or number
        if i >= len(content):
            break
        
        if content[i] == '{':
            # It's a table/list - extract it with proper nesting
            depth = 0
            start = i
            while i < len(content):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            value = content[start:i]
            result[key] = _parse_table_or_list(value)
        elif content[i] == '"':
            # It's a string - extract until closing quote
            start = i + 1
            i += 1
            while i < len(content) and content[i] != '"':
                i += 1
            if i < len(content):
                i += 1  # Skip closing quote
            result[key] = content[start:i-1]
        else:
            # It's a number or identifier - extract until comma or closing brace
            start = i
            while i < len(content) and content[i] not in ',}':
                i += 1
            value = content[start:i].strip()
            try:
                if '.' in value:
                    result[key] = float(value)
                else:
                    result[key] = int(value)
            except ValueError:
                result[key] = value
    
    return result


def _parse_table_or_list(content):
    """
    Determine if content is a list of items (table) or a key-value table.
    
    Heuristic: If the content contains '=' signs at the top level, it's a key-value table.
    Otherwise, it's a list.
    """
    # Strip whitespace first
    content = content.strip()
    
    # Remove exactly one pair of outermost braces if present
    if content.startswith('{') and content.endswith('}'):
        content = content[1:-1]
    
    content = content.strip()
    
    if not content:
        return {}
    
    # Check if this is a key-value table by looking for '=' at top level
    depth = 0
    has_equals_at_top = False
    
    for char in content:
        if char in '{[':
            depth += 1
        elif char in '}]':
            depth -= 1
        elif char == '=' and depth == 0:
            has_equals_at_top = True
            break
    
    if has_equals_at_top:
        # It's a key-value table
        return _parse_key_value_table(content)
    else:
        # It's a list of items
        return _parse_list(content)



def _parse_list(content):
    """Parse a list of items/tables."""
    items = []
    
    # Content is already stripped of outer braces by _parse_table_or_list()
    # Don't strip again, or we'll lose the structure of nested tables
    
    # Split by top-level commas (not inside nested brackets)
    depth = 0
    current = []
    
    for char in content:
        if char in '{[':
            depth += 1
            current.append(char)
        elif char in '}]':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            item_str = ''.join(current).strip()
            if item_str:
                if item_str.startswith('{'):
                    items.append(_parse_table_or_list(item_str))
                else:
                    items.append(_parse_value(item_str))
            current = []
        else:
            current.append(char)
    
    if current:
        item_str = ''.join(current).strip()
        if item_str:
            if item_str.startswith('{'):
                items.append(_parse_table_or_list(item_str))
            else:
                items.append(_parse_value(item_str))
    
    return items



def _parse_key_value_table(content):
    """Parse a key-value table."""
    result = {}
    
    # Content is already stripped of outer braces by _parse_table_or_list()
    # Don't strip again
    
    # Split by top-level commas
    depth = 0
    current = []
    pairs = []
    
    for char in content:
        if char in '{[':
            depth += 1
            current.append(char)
        elif char in '}]':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            pair_str = ''.join(current).strip()
            if pair_str:
                pairs.append(pair_str)
            current = []
        else:
            current.append(char)
    
    if current:
        pair_str = ''.join(current).strip()
        if pair_str:
            pairs.append(pair_str)
    
    # Now parse each key-value pair
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            key = key.strip()
            value = value.strip()
            result[key] = _parse_value(value)
    
    return result


def _parse_value(value):
    """Parse a single value."""
    value = value.strip()
    
    if value.startswith('{'):
        return _parse_table_or_list(value)
    elif value.startswith('"'):
        return value.strip('"')
    else:
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value


# Alternative: Use mlua if available (more robust)
def load_level_data(level_name, world_name='green'):
    """
    Load level data from a Lua file.
    
    Args:
        level_name: Name of the level (e.g., 'lvl1', 'lvl2')
        world_name: Name of the world (e.g., 'green')
    
    Returns:
        Dictionary containing level data
    """
    lua_path = Path(__file__).parent.parent.parent / 'assets' / 'data' / 'levels' / f'{world_name}.lua'
    
    levels_data = parse_lua_level(str(lua_path))
    
    if level_name in levels_data:
        return levels_data[level_name]
    else:
        raise ValueError(f"Level '{level_name}' not found in {world_name}.lua")
