# lab_congress_submission.py
# LAB submission: Congressional Plain Language Translator (Option C)
# Pairs with LAB_congress.md and lab_congress_submission.md

# This script is the reference implementation for the Plain Language Translator
# agent described in lab_congress_submission.md. It:
#   1. Loads three real-style legislative excerpts at different complexity levels
#   2. Sends each through the agent system prompt to Ollama Cloud
#   3. Saves a screenshot-ready transcript to output/lab_congress_translations.md
#   4. Renders the architecture Mermaid diagram to a PNG via mermaid.ink

# 0. SETUP ###################################

## 0.1 Load Packages #################################

# pip install requests python-dotenv
import base64
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

## 0.2 Configuration #################################

# Load credentials from the repo-root .env (OLLAMA_API_KEY for Ollama Cloud)
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# Ollama Cloud is the default provider for this course;
# fall back to a local Ollama instance if no API key is set.
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com" if OLLAMA_API_KEY else "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b" if OLLAMA_API_KEY else "gemma3:latest")

# Output folder for screenshot-ready artifacts
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

## 0.3 System Prompt (matches lab_congress_submission.md verbatim) ##########

SYSTEM_PROMPT = """ROLE
You are the Plain Language Translator, a read-only AI assistant for U.S.
congressional staff and constituents. You translate retrieved legislative or
regulatory text into clear, accessible English at a specified reading level.
You never modify, store, or send documents elsewhere.

INPUTS YOU WILL RECEIVE
- source_text: the exact passage to translate (already retrieved by the system)
- target_reading_level: integer grade level, default 8
- audience_hint: optional (e.g., "constituent letter", "junior staffer brief")
- source_citation: e.g., "5 U.S.C. \u00a7 552(b)(7)" or "40 CFR 60.40c"

HARD RULES
1. Translate ONLY source_text. Do not import outside facts, statistics, case
   law, or definitions that are not in source_text or in your retrieval context.
2. Never invent, paraphrase, or "clean up" a citation. Quote section numbers
   exactly as they appear, or omit them.
3. Preserve every numbered provision. If you collapse subparts for readability,
   list which subparts were collapsed in COVERAGE NOTES.
4. Preserve terms of art (e.g., "discovery", "preemption", "rulemaking",
   "stay", "remand"). On first use, give a one-clause plain gloss in
   parentheses; do not replace the term.
5. When a phrase has no plain-language equivalent without distortion, KEEP the
   original phrase and emit a [NUANCE WARNING: ...] explaining what is at risk
   if it is simplified.
6. Match the target reading level by sentence length and word choice, not by
   removing meaning. Aim within \u00b11 grade level of the target.
7. If source_text is empty, ambiguous, or appears to be outside your
   permissioned retrieval scope, output the REFUSAL block instead of guessing.

OUTPUT FORMAT (use these exact headers, in this order)
ORIGINAL
> <verbatim block quote of source_text, including its citation if provided>

PLAIN LANGUAGE TRANSLATION
<your translation at the target reading level>

NUANCE WARNINGS
- [NUANCE WARNING: <term-or-clause>] <one sentence on what nuance is at risk>
(or "None." if the translation is faithful end-to-end)

COVERAGE NOTES
- Subparts collapsed: <list, or "None">
- Cross-references kept verbatim: <list, or "None">

QUALITY SELF-CHECK
- Reading level (estimated grade): <integer>
- Confidence in faithfulness: <High / Medium / Low>
- Recommended next step: <e.g., "Cleared for constituent reply",
  "Refer to Legislative Counsel before publishing",
  "Re-retrieve: source text appears truncated">

REFUSAL BLOCK (use ONLY when rule 7 triggers)
REFUSAL
- Reason: <"empty retrieval" | "outside clearance" | "ambiguous source">
- Recommended next step: <e.g., "Request escalation to Senior Counsel",
  "Re-run query against the public statute index">"""

# 1. SAMPLE LEGISLATIVE EXCERPTS ###################################

# Three excerpts of increasing density. Each is a real-style passage drawn from
# (or paraphrased very close to) a publicly available statute or regulation.
# Citations point to where a real version lives, but the text below is the
# version actually translated.

SAMPLES = [
    {
        "id": "s1_foia_exemption",
        "title": "FOIA law-enforcement exemption",
        "citation": "5 U.S.C. \u00a7 552(b)(7)",
        "audience": "constituent letter",
        "reading_level": 8,
        "text": (
            "This section does not apply to matters that are records or "
            "information compiled for law enforcement purposes, but only to "
            "the extent that the production of such law enforcement records "
            "or information (A) could reasonably be expected to interfere "
            "with enforcement proceedings, (B) would deprive a person of a "
            "right to a fair trial or an impartial adjudication, "
            "(C) could reasonably be expected to constitute an unwarranted "
            "invasion of personal privacy, (D) could reasonably be expected "
            "to disclose the identity of a confidential source, "
            "(E) would disclose techniques and procedures for law enforcement "
            "investigations or prosecutions, or would disclose guidelines for "
            "law enforcement investigations or prosecutions if such "
            "disclosure could reasonably be expected to risk circumvention "
            "of the law, or (F) could reasonably be expected to endanger the "
            "life or physical safety of any individual."
        ),
    },
    {
        "id": "s2_sba_small_business",
        "title": "SBA size-standard rulemaking authority",
        "citation": "15 U.S.C. \u00a7 632(a)(2)(A)",
        "audience": "junior staffer brief",
        "reading_level": 10,
        "text": (
            "In addition to the criteria specified in paragraph (1), the "
            "Administrator may specify detailed definitions or standards by "
            "which a business concern may be determined to be a small "
            "business concern for the purposes of this chapter or any other "
            "Act. Unless specifically authorized by statute, no Federal "
            "department or agency may prescribe a size standard for "
            "categorizing a business concern as a small business concern, "
            "unless such proposed size standard (i) is proposed after an "
            "opportunity for public notice and comment, (ii) provides for "
            "determining the size of a business concern on the basis of the "
            "number of employees, the dollar volume of business, the net "
            "worth, the net income, a combination thereof, or other "
            "appropriate factors, and (iii) is approved by the Administrator."
        ),
    },
    {
        "id": "s3_clean_air_nsps",
        "title": "Clean Air Act new source performance standard",
        "citation": "40 CFR 60.40c (excerpt, simplified)",
        "audience": "constituent letter",
        "reading_level": 8,
        "text": (
            "The provisions of this subpart are applicable to each steam "
            "generating unit for which construction, modification, or "
            "reconstruction is commenced after June 9, 1989 and that has a "
            "maximum design heat input capacity of 29 megawatts (100 million "
            "Btu per hour) or less, but greater than 2.9 megawatts (10 "
            "million Btu per hour). Affected facilities that also meet the "
            "applicability requirements under any other standard in subparts "
            "Da, Db, or Ea of this part are not subject to that other "
            "standard but remain subject to this subpart."
        ),
    },
]


# 2. AI HELPER ###################################

def query_ollama_chat(messages: list, model: str = OLLAMA_MODEL) -> str:
    """Send a chat to Ollama (local or Cloud) and return the assistant text."""
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }
    response = requests.post(url, headers=headers, json=body, timeout=180)
    response.raise_for_status()
    return response.json()["message"]["content"]


def build_user_prompt(sample: dict) -> str:
    """Format one sample into the structured input the system prompt expects."""
    return (
        f"target_reading_level: {sample['reading_level']}\n"
        f"audience_hint: {sample['audience']}\n"
        f"source_citation: {sample['citation']}\n"
        f"source_text:\n\"\"\"\n{sample['text']}\n\"\"\""
    )


# 3. RUN THREE TRANSLATIONS ###################################

print("=" * 70)
print("\U0001f4cb LAB: Congressional Plain Language Translator (Option C)")
print("=" * 70)
print(f"\u2601\ufe0f  Model: {OLLAMA_MODEL}  |  Host: {OLLAMA_HOST}")
print(f"\U0001f4c4 Samples to translate: {len(SAMPLES)}")
print()

translations = []
for i, sample in enumerate(SAMPLES, 1):
    print("-" * 70)
    print(f"\U0001f527 Sample {i}/{len(SAMPLES)} -- {sample['title']}")
    print(f"   \u2702\ufe0f  Citation: {sample['citation']}")
    print(f"   \U0001f4d0 Target grade level: {sample['reading_level']}")
    print(f"   \U0001f465 Audience: {sample['audience']}")
    print("-" * 70)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(sample)},
    ]
    response = query_ollama_chat(messages)
    translations.append({"sample": sample, "response": response})

    print()
    print(response)
    print()


# 4. RENDER THE MERMAID ARCHITECTURE DIAGRAM TO PNG ##########################

# We use mermaid.ink (a public Mermaid rendering service) so the lab can be
# reproduced without installing the mermaid-cli toolchain.
MERMAID_DIAGRAM = """flowchart TD
    A[Document Ingest<br/>statutes, internal memos,<br/>constituent letters] --> B[Chunker + Embedder<br/>nomic-embed-text]
    B --> C[(Vector DB<br/>Postgres + pgvector)]

    USER[Staffer or constituent<br/>JWT carries clearance:<br/>public / staff / senior] --> D{Access Control<br/>Postgres RLS<br/>by clearance level}
    C --> D

    D -->|allowed chunks| E[Plain Language Translator<br/>Ollama Cloud<br/>read-only: no write tools,<br/>no outbound calls]
    D -->|denied| REF[Refusal block:<br/>outside clearance]

    E --> F[Staff Interface<br/>shows ORIGINAL,<br/>PLAIN LANGUAGE TRANSLATION,<br/>NUANCE WARNINGS]"""


def render_mermaid_to_png(mermaid_src: str, out_path: Path) -> bool:
    """
    Use the mermaid.ink public service to render a Mermaid diagram to PNG.

    Returns True on success. We handle errors gracefully because this is a
    "nice to have" -- the markdown deliverable still renders the diagram
    natively in any Mermaid-aware viewer.
    """
    try:
        encoded = base64.urlsafe_b64encode(mermaid_src.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        out_path.write_bytes(response.content)
        return True
    except Exception as exc:
        print(f"\u26a0\ufe0f  Could not render Mermaid PNG: {exc}")
        return False


print("-" * 70)
print("\U0001f3a8 Rendering architecture diagram to PNG via mermaid.ink ...")
print("-" * 70)
diagram_path = OUT_DIR / "lab_congress_architecture.png"
diagram_ok = render_mermaid_to_png(MERMAID_DIAGRAM, diagram_path)
if diagram_ok:
    print(f"   \u2705 Saved: {diagram_path}  ({diagram_path.stat().st_size // 1024} KB)")
print()

# 5. SAVE A SCREENSHOT-READY TRANSCRIPT ###################################

transcript_path = OUT_DIR / "lab_congress_translations.md"
transcript_lines = [
    "# LAB Congress -- Plain Language Translator: Live Translations\n",
    f"- Model: `{OLLAMA_MODEL}`",
    f"- Host: `{OLLAMA_HOST}`",
    f"- Samples translated: {len(translations)}\n",
    "Each section below shows the structured user input the agent received and ",
    "the verbatim agent output. The system prompt is in ",
    "[`lab_congress_submission.md`](../lab_congress_submission.md).\n",
    "---\n",
]
for i, item in enumerate(translations, 1):
    sample = item["sample"]
    transcript_lines.extend([
        f"## Sample {i} -- {sample['title']}\n",
        f"- Citation: `{sample['citation']}`",
        f"- Target grade level: {sample['reading_level']}",
        f"- Audience hint: {sample['audience']}\n",
        "**Agent output:**\n",
        "```text",
        item["response"].rstrip(),
        "```\n",
        "---\n",
    ])
transcript_path.write_text("\n".join(transcript_lines), encoding="utf-8")

# 6. SUMMARY ###################################

print("=" * 70)
print("\U0001f4ca Summary")
print("=" * 70)
print(f"\U0001f4be Saved transcript: {transcript_path}")
if diagram_ok:
    print(f"\U0001f4be Saved diagram:    {diagram_path}")
for i, item in enumerate(translations, 1):
    sample = item["sample"]
    print(f"   \u2705 Sample {i} ({sample['id']}): {len(item['response'])} chars returned")
print()
print("Submission deliverable:")
print(f"   \U0001f4c4 lab_congress_submission.md     (system prompt + diagram + justification)")
print(f"   \U0001f4c4 {transcript_path.name}      (live demo transcript)")
if diagram_ok:
    print(f"   \U0001f5bc\ufe0f  {diagram_path.name}   (rendered architecture diagram)")
