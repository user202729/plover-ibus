from pathlib import Path
import tempfile

response_path: Path=Path(tempfile.gettempdir())/".ibus-response"

listen_path_name: str=".ibus-listen"


# type constants in communication
BACKSPACE="d"
RAW_STRING="S"
SMART_STRING="s"
COMBINATION="c"
