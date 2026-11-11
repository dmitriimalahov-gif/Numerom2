"""Generate the selected conversational greeting into artifacts for review and video assembly."""
import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("render-author-conversation.py")), run_name="__main__")
