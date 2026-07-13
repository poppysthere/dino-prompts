#!/usr/bin/env python3
"""Back-compat shim: the cow checker now lives in checker_word.py (shared by all word pages)."""
from checker_word import check, main  # noqa: F401

if __name__ == "__main__":
    main()
