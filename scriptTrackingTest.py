from pathlib import Path
from scriptTracking import create_tracked_script
def main():
    output_directory = Path("data/francePop")
    iteration_filepath = output_directory / "iteration1"

    create_tracked_script(iteration_filepath / "scriptUnmodified.py", iteration_filepath / "script1.py", 10)

main()