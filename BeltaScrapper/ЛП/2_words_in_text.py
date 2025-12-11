import os
import re
import sys
import chardet
import logging
from logger_config import get_logger

logger = get_logger(__name__)

def contains_both_words(filepath, word1, word2):
    """
    Check if the file content contains both word1 and word2 as whole words.
    Tries to handle encoding automatically.
    """
    try:
        # Detect encoding
        with open(filepath, 'rb') as f:
            raw_data = f.read(8192)  # Read first 8KB for detection
        encoding = chardet.detect(raw_data)['encoding']
        if encoding is None:
            encoding = 'utf-8'

        # Read full file with detected encoding
        with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()

        # Search for whole-word matches using regex word boundaries
        pattern1 = re.compile(rf'\b{re.escape(word1)}\b', re.IGNORECASE)
        pattern2 = re.compile(rf'\b{re.escape(word2)}\b', re.IGNORECASE)

        return bool(pattern1.search(content) and pattern2.search(content))

    except Exception:
        # Skip unreadable files
        return False

def main():
    root_folder = sys.argv[1] if len(sys.argv) > 1 else "."
    word1 = "Лукашенко"
    word2 = "Путин"

    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if contains_both_words(filepath, word1, word2):
                logger.info(os.path.abspath(filepath))

if __name__ == "__main__":
    main()