import sys
from rich.console import Console

# force_terminal=True prevents Rich from disabling output when it can't detect
# an interactive TTY (common in VSCode's integrated terminal on Windows)
console = Console(force_terminal=True, file=sys.stdout)
