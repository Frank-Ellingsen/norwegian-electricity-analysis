from .policy import Policy
from .context import ProjectContext
from .tools import Tools
from .llm import GeminiClient

class AnalystAgent:
    def __init__(self):
        self.policy = Policy()
        self.context = ProjectContext()
        self.tools = Tools()
        self.llm_client = GeminiClient()

    def chat(self, prompt: str) -> str:
        system = (
            self.policy.system_prompt()
            + "\n\n--- PROJECT CONTEXT ---\n"
            + self.context.as_text()
        )
        return self.llm_client.chat(system_prompt=system, user_prompt=prompt)
