import json

def convert_array_to_oset(input_data):
    """
    Convert array structure to o.set() format
    
    Args:
        input_data: List of [key, value] pairs or JSON string
    
    Returns:
        String with o.set() statements
    """
    # If input is a string, parse it as JSON
    if isinstance(input_data, str):
        try:
            data = json.loads(input_data)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return ""
    else:
        data = input_data
    
    output_lines = []
    
    # Process each [key, value] pair
    for item in data:
        if len(item) != 2:
            print(f"Warning: Skipping invalid item: {item}")
            continue
            
        key, value = item
        
        # Format the value as a JSON string with proper indentation
        value_str = json.dumps(value, separators=(', ', ': '))
        
        # Create the o.set() line
        output_lines.append(f'o.set("{key}", {value_str});')
    
    return '\n'.join(output_lines)

# Alternative: Read from file and convert
def convert_from_file(filename):
    """
    Read JSON array from file and convert to o.set() format
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return convert_array_to_oset(data)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return ""
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from file: {e}")
        return ""

# Alternative: Save output to file
def convert_and_save(input_data, output_filename):
    """
    Convert data and save to file
    """
    with open(output_filename, 'w+', encoding='utf-8') as f:
        f.write(input_data)
    print(f"Output saved to '{output_filename}'")

# Uncomment these lines to use file operations:
result = convert_from_file('data/input.json')
convert_and_save(result, 'data/output.js')
