"""Bundle the selected voice from the verified project queue; prepare-project-narration.py queues missing clips."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("export-number-voices.py")), run_name="__main__")
