from pathlib import Path

class Policy:
    def __init__(self, path: str = "docs/skill.md"):
        self.path = Path(path)
        self.rules = self.path.read_text(encoding="utf-8")

    def system_prompt(self) -> str:
        return self.rules
