import json
from pathlib import Path
from transformers import pipeline
import logging
import warnings
import contextlib
import os

logger = logging.getLogger(__name__)


class NLPSummarizer:
    def __init__(
        self, config_path: Path = Path("sentinelforge/config/nlp_summarizer.json")
    ):
        cfg = json.loads(config_path.read_text())
        self._summarizer = pipeline("summarization", model=cfg["model"])
        self.max_length = cfg["max_length"]
        self.min_length = cfg["min_length"]
        self.do_sample = cfg["do_sample"]

    def summarize(self, text: str) -> str:
        """Generate a short summary for a given text."""
        try:
            # Tests expect the summarizer to always run
            text_length = len(text.split())
            dynamic_max_length = min(
                self.max_length, max(self.min_length, text_length // 2)
            )

            if dynamic_max_length <= self.min_length:
                dynamic_max_length = self.min_length + 1

            logger.debug(
                f"Summarizing text of length {text_length} with max_length={dynamic_max_length}"
            )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with open(os.devnull, "w") as f, contextlib.redirect_stderr(f):
                    result = self._summarizer(
                        text,
                        max_length=dynamic_max_length,
                        min_length=self.min_length,
                        do_sample=self.do_sample,
                    )

            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            return ""
