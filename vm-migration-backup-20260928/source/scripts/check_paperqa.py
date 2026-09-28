"""Import/config compatibility only; deliberately does not call a model."""
from root_paper_lab import server
from paperqa import Docs, Settings
import inspect

settings = Settings(llm="test-model", summary_llm="test-model", embedding="test-embedding")
assert "settings" in inspect.signature(Docs.aadd).parameters
assert "settings" in inspect.signature(Docs.aquery).parameters
print("PaperQA import/settings/API signatures: passed; model execution: not run")
