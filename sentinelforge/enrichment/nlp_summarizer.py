import json
from pathlib import Path
from transformers import pipeline


class NLPSummarizer:
    def __init__(
        self, config_path: Path = Path("sentinelforge/config/nlp_summarizer.json")
    ):
        cfg = json.loads(config_path.read_text())
        self._summarizer = pipeline(
            "summarization",
            model=cfg["model"],
        )
        self.max_length = cfg["max_length"]
        self.min_length = cfg["min_length"]
        self.do_sample = cfg["do_sample"]

    def summarize(self, text: str) -> str:
        """
        Generate a short summary for a given text.
        """
        try:
            result = self._summarizer(
                text,
                max_length=self.max_length,
                min_length=self.min_length,
                do_sample=self.do_sample,
            )
            return result[0]["summary_text"].strip()
        except Exception:
            # TODO: Add logging here
            # swallow errors for now and return empty string
            return ""
