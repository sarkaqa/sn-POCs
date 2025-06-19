from colorama import Fore, Style, init
init(autoreset=True)

class ResultLogger:
    def __init__(self, filepath):
        self.filepath = filepath
        with open(self.filepath, "w") as file:
            file.write("")  # Clear existing log

    def _strip_ansi(self, text):
        import re
        ansi_escape = re.compile(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]')
        return ansi_escape.sub('', text)

    def log_line(self, line, color=None):
        colored_line = f"{color}{line}{Style.RESET_ALL}" if color else line
        print(colored_line)
        with open(self.filepath, "a") as file:
            file.write(colored_line + "\n")  # Retain ANSI colors

    def log_main_header(self, title):
        self.log_line("#" * 100)
        self.log_line(title.center(100))
        self.log_line("#" * 100)

    def log_section_header(self, title):
        self.log_line("*" * 100)
        self.log_line(title.center(100))
        self.log_line("*" * 100)

    def log_subsection(self, title):
        self.log_line("—" * 100)
        self.log_line(title.center(100))
        self.log_line("—" * 100)

    def log_colored_subsection(self, text, color):
        self.log_line("—" * 100)
        self.log_line(text.center(100), color=color)
        self.log_line("—" * 100)

