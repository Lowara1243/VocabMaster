#!/usr/bin/env python
"""Script for starting the backend server."""

import os
import sys
import uvicorn


def main():
    """Entry point for starting the server."""
    # Ensure project root is in sys.path so 'backend.main' can be imported
    # regardless of where this script is called from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    uvicorn.run(
        "backend.main:app", host="127.0.0.1", port=8000, reload=True, log_level="info"
    )


if __name__ == "__main__":
    main()
