#!/usr/bin/env python3

import re
import sys

COLOR_MATCH = "\033[1;33m"
COLOR_RESET = "\033[0m"

UUID_REGEX = re.compile(
    r'\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b',
    re.IGNORECASE
)

def uuid_grep():
    for line in sys.stdin:
        for uuid in UUID_REGEX.findall(line):
            print(f"{COLOR_MATCH}{uuid}{COLOR_RESET}")

if __name__ == "__main__":
    uuid_grep() 
