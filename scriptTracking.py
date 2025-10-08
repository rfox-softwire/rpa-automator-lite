from pathlib import Path

def create_tracked_script(original_script_path, output_script_path):
    with open(original_script_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    tracking_code = [
        'import sys',
        'import traceback',
        'import os',
        'from pathlib import Path',
        'from io import StringIO',
        'from contextlib import redirect_stdout, redirect_stderr',
        '',
        'def setup_tracking():',
        '    script_dir = Path(__file__).parent',
        '    output_file = script_dir / \'output.txt\'',
        '    error_file = script_dir / \'errorMessage.txt\'',
        '    output = StringIO()',
        '    error_output = StringIO()',
        '    sys.stdout = output',
        '    sys.stderr = error_output',
        '    return output, error_output, output_file, error_file',
        '',
        'def save_outputs(output, error_output, output_file, error_file, error=None):',
        '    with open(output_file, \'w\', encoding=\'utf-8\') as f:',
        '        f.write(output.getvalue())',
        '    with open(error_file, \'w\', encoding=\'utf-8\') as f:',
        '        f.write(f"Error: {str(error)}\\n")',
        '        f.write("\\n=== STDERR ===\\n")',
        '        f.write(error_output.getvalue())',
        '        f.write("\\n=== TRACEBACK ===\\n")',
        '        f.write(traceback.format_exc())',
        '',
        '# Setup tracking',
        'output, error_output, output_file, error_file = setup_tracking()',
        '',
        'try:',
        '    # Original script content starts here',
    ]

    for line in original_content.splitlines():
        tracking_code.append(f'    {line}' if line.strip() else '')
    
    tracking_code.extend([
        '',
        '    # Save outputs on success',
        '    save_outputs(output, error_output, output_file, error_file)',
        '',
        'except Exception as e:',
        '    # Save outputs on error',
        '    save_outputs(output, error_output, output_file, error_file, e)',
        '    raise  # Re-raise the exception after saving the error',
        ''
    ])

    with open(output_script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(tracking_code))