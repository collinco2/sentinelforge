from pdfminer.high_level import extract_text
from pathlib import Path

FILES = {
    "/Users/Collins/Documents/Product Requirement Document (PRD).pdf": "docs/PRD.md",
    "/Users/Collins/Documents/Technical Research Paper.pdf": "docs/Technical-Research.md",
    "/Users/Collins/Documents/Stakeholder-Notes.pdf": "docs/Stakeholder-Notes.md",
}


def convert(src: str, dst: str) -> None:
    print(f"🔄  Converting {src} → {dst}")
    text = extract_text(src)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(text)
    print(f"✅  Wrote {dst} ({len(text):,} chars)")


if __name__ == "__main__":
    for pdf, md in FILES.items():
        try:
            convert(pdf, md)
        except Exception as exc:
            print(f"❌  Failed on {pdf}: {exc}")
