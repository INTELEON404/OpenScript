#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from typing import Dict, List, Optional, Tuple

# ANSI styling constants
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


# Mapping ASCII letters to Unicode homoglyphs
HOMOGLYPHS_MAP: Dict[str, List[str]] = {
    'a': ['à', 'á', 'â', 'ã', 'ä', 'å', 'ɑ', 'А', 'Α', 'Ꭺ', 'Ａ', '𝔄', '𝕬', '𝒜', '𝐀', '𝐴', '𝘈', '𝙰', '𝖠', '𝗔', '𝘼', '𝚨', '𝑨', 'ⓐ', 'Ⓐ', '🅐', '🅰', '𝔞', '𝖆', '𝒶', '𝗮', '𝘢'],
    'b': ['Ь', 'Ꮟ', 'Ƅ', 'ᖯ', '𝐛', '𝑏', '𝒃', '𝓫', '𝔟', '𝕓', '𝖇', '𝗯', '𝘣', '𝙗', '𝚋'],
    'c': ['ϲ', 'с', 'ƈ', 'ȼ', 'ḉ', 'ⲥ', '𝐜', '𝑐', '𝒄', '𝓬', '𝔠', '𝕔', '𝖈', '𝗰', '𝘤', '𝙘', '𝚌'],
    'd': ['ԁ', 'ժ', 'Ꮷ', '𝐝', '𝑑', '𝒅', '𝓭', '𝔡', '```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from typing import Dict, List, Optional, Tuple


class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


# PEP 8 constant naming
HOMOGLYPHS_MAP: Dict[str, List[str]] = {
    'a': ['à', 'á', 'â', 'ã', 'ä', 'å', 'ɑ', 'А', 'Α', 'Ꭺ', 'Ａ', '𝔄', '𝕬', '𝒜', '𝐀', '𝐴', '𝘈', '𝙰', '𝖠', '𝗔', '𝘼', '𝚨', '𝑨', 'ⓐ', 'Ⓐ', '🅐', '🅰', '𝔞', 'Here is the clean, refactored version of your script.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from typing import Dict, List, Optional, Tuple

class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


# PEP 8 constant naming
HOMOGLYPHS_MAP: Dict[str, List[str]] = {
    'a': ['à', 'á', 'â', 'ã', 'ä', 'å', 'ɑ', 'А', 'Α', 'Ꭺ', 'Ａ', '𝔄', '𝕬', '𝒜', '𝐀', '𝐴', '𝘈', '𝙰', '𝖠', '𝗔', '𝘼', '𝚨', '𝑨', 'ⓐ', 'Ⓐ', '🅐', '🅰', '𝔞', '```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from typing import Dict, List, Optional, Tuple


class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


HOMOGLYPHS_MAP: Dict[str, List[str]] = {
    'a': ['à', 'á', 'â', 'ã', 'ä', 'å', 'ɑ', 'А', 'Α', 'Ꭺ', 'Ａ', '𝔄', '𝕬', '𝒜', '𝐀', '𝐴', '𝘈', '𝙰', '𝖠', '𝗔', '𝘼', '𝚨', '𝑨', 'ⓐ', 'Ⓐ', '🅐', '🅰', '𝔞', '
