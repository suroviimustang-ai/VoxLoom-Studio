"""Commit text exports only after the complete replacement is on disk."""

import os
import tempfile
from pathlib import Path


def write_text_atomic(path, content):
    destination = Path(path)
    fd, temporary = tempfile.mkstemp(
        prefix=".voxloom-", suffix=".tmp", dir=destination.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
