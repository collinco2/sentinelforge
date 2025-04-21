import pytest
import json  # Added import for json.dumps
from sentinelforge.enrichment.nlp_summarizer import NLPSummarizer


class DummyPipeline:
    def __call__(self, text, max_length, min_length, do_sample):
        # Basic check to ensure parameters are passed (optional)
        assert isinstance(text, str)
        assert isinstance(max_length, int)
        assert isinstance(min_length, int)
        assert isinstance(do_sample, bool)
        return [{"summary_text": "SHORT SUMMARY"}]


@pytest.fixture(autouse=True)
def patch_transformers_pipeline(monkeypatch):
    # intercept the transformers.pipeline import in our module
    import sentinelforge.enrichment.nlp_summarizer as mod

    monkeypatch.setattr(mod, "pipeline", lambda *args, **kwargs: DummyPipeline())
    return


def test_summarize_returns_text(tmp_path):
    # write a minimal config
    cfg = {
        "model": "dummy-model",
        "max_length": 50,
        "min_length": 10,
        "do_sample": False,
    }
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps(cfg))

    summarizer = NLPSummarizer(config_path=cfg_file)
    summary = summarizer.summarize("some long input text")
    assert summary == "SHORT SUMMARY"


# Add a test for the error handling path
def test_summarize_handles_exception(tmp_path, monkeypatch):
    cfg = {
        "model": "dummy-model",
        "max_length": 50,
        "min_length": 10,
        "do_sample": False,
    }
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps(cfg))

    # Make the dummy pipeline raise an exception
    def raise_exception(*args, **kwargs):
        raise Exception("Summarization failed")

    monkeypatch.setattr(DummyPipeline, "__call__", raise_exception)

    summarizer = NLPSummarizer(config_path=cfg_file)
    summary = summarizer.summarize("some long input text")
    assert summary == ""  # Expect empty string on error
