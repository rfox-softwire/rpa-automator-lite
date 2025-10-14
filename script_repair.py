from llm_client import LLMClient
import logging
from pathlib import Path
from script_generation import generate_script
from html_summary import summarise_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_iteration_files(iteration_dir):
    files_content = {
        'output': None,
        'instruction': None,
        'script': None,
        'error': None,
        'success_criteria': None,
        'html': [],
        'url': []
    }
    
    def read_if_exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    files_content['output'] = read_if_exists(iteration_dir / 'output.txt')
    files_content['instruction'] = read_if_exists(iteration_dir / 'instruction.txt')
    files_content['script'] = read_if_exists(iteration_dir / 'scriptUnmodified.py')
    files_content['error'] = read_if_exists(iteration_dir / 'errorMessage.txt')
    files_content['success_criteria'] = read_if_exists(iteration_dir / 'successCriteria.txt')
    
    page_count = 1
    entire_html = read_if_exists(iteration_dir / f'HTML-{page_count}.txt')
    while entire_html:
        html_summary = summarise_html(entire_html)
        with open(iteration_dir / f"htmlSummary-{page_count}.txt", "w", encoding="utf-8") as f:
            f.write(html_summary)
        files_content['html'].append(html_summary)
        files_content['url'].append(read_if_exists(iteration_dir / f'url-{page_count}.txt'))
        page_count += 1
        entire_html = read_if_exists(iteration_dir / f'HTML-{page_count}.txt')
    
    return files_content

def generate_repair_prompt(files_content):
    prompt = [
        "You are a RPA assistant that generates a Python script based on a user's instruction "
        "for interactions with web applications using the Playwright package.\n"
        f"The user's original instruction was: {files_content['instruction']}\n"
        f"The user's success criteria was: {files_content['success_criteria']}\n"
        f"Here's the original script that had the error:\n```python\n{files_content['script']}\n```\n\n"
    ]
    
    if files_content['error']:
        prompt.append(f"The user is trying to fix an error in their script. Here's the error that occurred:\n {files_content['error']}\n")
    else:
        prompt.append("The user is trying to fix an error in their script. The current script does not provide an error message\n")
    
    if files_content['output']:
        prompt.append(f"The script currently outputs:\n {files_content['output']}\n")
    else:
        prompt.append("The script does not currently output anything\n")

    for index, htmlSummary in enumerate(files_content['html']):
        prompt.append(f"Prior to failing its execution, {files_content['url'][index]} had the following summarised HTML content:\n{htmlSummary}\n")

    prompt.extend([
        "IMPORTANT: The script should follow these rules:\n"
        "1. Use asynchronous Playwright\n"
        "2. Do not use try/catch blocks\n"
        "3. The script should be self-contained with all necessary imports\n"
        "4. The script should be executable directly (remember that 'async with' outside async function is not allowed)\n"
        "5. Do not include any if __name__ == \"__main__\": blocks\n\n"
        "Please generate a corrected version of the script that fixes the error while maintaining the original functionality.\n",
        "Only return the proposed Python script."
    ])
    return "".join(prompt)

def main():
    bot_name = input("Enter name for bot: ")
    base_directory = Path(f"data/{bot_name}")

    base_path = Path(base_directory)
    latest_iteration_number = len([directories for directories in base_path.iterdir()])

    latest_iteration_directory = base_path / f"iteration{latest_iteration_number}"
    current_files = read_iteration_files(latest_iteration_directory)

    user_instruction = current_files["instruction"]
    success_criteria = current_files["success_criteria"]
    new_iteration_filepath = base_path / f"iteration{latest_iteration_number + 1}"

    prompt = generate_repair_prompt(current_files)

    generate_script(new_iteration_filepath, user_instruction, success_criteria, prompt)

main()