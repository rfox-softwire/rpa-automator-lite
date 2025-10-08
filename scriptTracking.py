from pathlib import Path

def create_tracked_script(original_script_path, output_script_path):
    with open(original_script_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    tracking_code = """import sys
import traceback
import os
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

def setup_tracking():
    script_dir = Path(__file__).parent
    output_file = script_dir / 'output.txt'
    error_file = script_dir / 'errorMessage.txt'
    
    output = StringIO()
    error_output = StringIO()
    
    sys.stdout = output
    sys.stderr = error_output
    
    return output, error_output, output_file, error_file

def save_outputs(output, error_output, output_file, error_file, error=None):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== STDOUT ===")
        f.write(output.getvalue())
        f.write("=== STDERR ===")
        f.write(error_output.getvalue())
    
    if error:
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Error: {str(error)}")
            f.write("=== STDOUT ===")
            f.write(output.getvalue())
            f.write("=== STDERR ===")
            f.write(error_output.getvalue())
            f.write("=== TRACEBACK ===")
            f.write(traceback.format_exc())

output, error_output, output_file, error_file = setup_tracking()

"""

    modified_content = tracking_code + "\n" + original_content

    modified_content += """

if __name__ == "__main__":
    try:
        # Call the original script's main function if it exists
        if 'main' in locals() and callable(main):
            main()
        save_outputs(output, error_output, output_file, error_file)
    except Exception as e:
        save_outputs(output, error_output, output_file, error_file, e)
        raise  # Re-raise the exception after saving the error
"""
    print(modified_content)
    print(output_script_path)
    with open(output_script_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)