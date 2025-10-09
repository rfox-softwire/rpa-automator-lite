import logging
from pathlib import Path
from scriptGeneration import generateScript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_initial_prompt(instruction, success_criteria):
    prompt = (
        "You are a RPA assistant that generates a Python script based on a user's instruction "
        "for interactions with web applications using the Playwright package.\n\n"
        f"The user's instructions are: {instruction}\n\n"
        f"The resulting script should: {success_criteria}\n\n"
        "IMPORTANT: The script should follow these rules:\n"
        "1. Use asynchronous Playwright\n"
        "2. Do not use try/catch blocks\n"
        "3. The script should be self-contained with all necessary imports\n"
        "4. The script should be executable directly and not wrapped in a function\n"
        "5. Do not include any if __name__ == \"__main__\": blocks\n\n"
        "Only return the proposed python script."
    )
    return prompt

def clear_directory(directory: Path):
    if not directory.exists():
        return
        
    for item in directory.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            clear_directory(item)
    
    if directory.exists():
        directory.rmdir()

def main():
    bot_name = input("Enter name for bot: ")
    output_directory = Path(f"data/{bot_name}")
    clear_directory(output_directory)
    output_directory.mkdir(parents = True)

    iteration_filepath = output_directory / "iteration1"

    user_instruction = input("Enter your instruction: ")
    success_criteria = input("Enter success criteria for instructions: ")
    prompt = generate_initial_prompt(user_instruction, success_criteria)

    generateScript(iteration_filepath, user_instruction, success_criteria, prompt)

main()