from rich.console import Console

# The idea here is to have one global instance of "console" (i.e. a singleton)
# This way, we can write to the same console from anywhere in the program
console = Console()
