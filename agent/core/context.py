from pathlib import Path

class ProjectContext:
    def __init__(self, path: str = "docs/GEMINI.md"):
        self.path = Path(path)
        self.context = self.path.read_text(encoding="utf-8")

    def as_text(self) -> str:
        return self.context
