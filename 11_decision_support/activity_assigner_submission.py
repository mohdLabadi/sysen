# activity_assigner_submission.py
# AI Assigner: Staff-Client Matching (ACTIVITY submission)
# Pairs with ACTIVITY_assigner.md

# Runs the 3 stages of the Assigner activity end-to-end:
#   Stage 1 — Assignment prompt: AI matches 6 staff to 12 clients (2 each)
#   Stage 2 — Stress-test follow-up: AI defends or revises one pairing
#   Stage 3 — Reflection: short written response saved with the outputs

# 0. SETUP ###################################

## 0.1 Load Packages #################################

# pip install requests python-dotenv
import os
import re
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

## 0.3 Prompts and Data #################################

# System prompt straight from ACTIVITY_assigner.md (Stage 1)
SYSTEM_PROMPT = """You are a managing partner at a consulting firm making staffing assignments.
Your job is to read unstructured descriptions of staff members and clients,
then assign each staff member to exactly 2 clients based on fit.

Return:
1. An assignment table with columns: Staff Member | Client 1 | Client 2 | Rationale (1 sentence)
2. A brief paragraph (3-5 sentences) summarizing your overall assignment logic

Rules:
- Each staff member gets exactly 2 clients
- Each client is assigned to exactly 1 staff member
- No client may be left unassigned
- Base assignments on demonstrated fit -- skills, experience, communication style
- Flag any assignments where fit is weak and explain why"""

# Staff and client descriptions from the activity (kept verbatim for traceability)
STAFF_AND_CLIENTS = """--- STAFF ---

Alex Chen
Senior consultant, 9 years experience. Background in financial services and
regulatory compliance. Known for being methodical and detail-oriented.
Prefers clients who are organized and have clear deliverables.
Not great with ambiguous or fast-moving projects.

Brianna Okafor
Mid-level consultant, 4 years experience. Specialist in nonprofit and public
sector work. Very strong communicator -- clients love her. Comfortable with
messy, evolving scopes. Has done a lot of stakeholder engagement work.

Carla Mendez
Senior consultant, 7 years experience. Deep expertise in healthcare and life
sciences. Data-heavy work is her strength -- she's built several dashboards and
automated reporting tools. Tends to be blunt and efficient; not the warmest
bedside manner but clients respect her results.

Dana Park
Junior consultant, 2 years experience. Background is in marketing and consumer
research. Eager and creative. Better on smaller, well-defined tasks.
Still building confidence with senior client stakeholders.

Elliot Vasquez
Partner-level, 15 years experience. Generalist with a strong track record in
strategy and organizational change. Good relationship manager. Prefers high-stakes,
high-visibility engagements. Gets bored on smaller tactical work.

Fiona Marsh
Mid-level consultant, 5 years experience. Former journalist turned researcher.
Excellent writer and communicator. Often assigned to deliverable-heavy projects
(reports, white papers, presentations). Works well independently.
Prefers clients who give her creative latitude.

--- CLIENTS ---

Client A -- Riverdale Community Health Clinic
Small nonprofit health clinic undergoing a strategic planning process.
Moderate budget. Stakeholders include the board, medical staff, and community
advocates. Very collaborative, but decisions are slow due to committee structure.
Main need: facilitation support and a written strategic plan.

Client B -- Atlas Financial Group
Large regional bank. Highly regulated environment. Project involves auditing
their compliance documentation and recommending process improvements.
Very organized client -- they have a detailed project plan. Expects formal
deliverables and regular status reports.

Client C -- BrightPath Schools (Charter Network)
Fast-growing charter school network. Expanding from 3 to 8 schools.
Needs help with org design and HR policy. Client is enthusiastic but somewhat
disorganized. Decision-maker is the founder/CEO -- she's visionary but hard to pin
down for meetings.

Client D -- Nexagen Pharmaceuticals
Mid-size pharma company. Project is a data audit and KPI dashboard buildout
for their clinical operations team. Technical stakeholders who want results,
not hand-holding. Timeline is tight.

Client E -- Greenway Transit Authority
Regional transit agency. Unionized workforce. Project involves a service
redesign study with significant community engagement components.
Political sensitivities -- several board members have conflicting opinions.
Long timeline, phased project.

Client F -- Solstice Consumer Goods
Consumer packaged goods brand. Needs a market research summary and brand
positioning analysis ahead of a product launch. Fun client, collaborative,
lots of back and forth. Not a huge budget. Creative work valued.

Client G -- Meridian Capital Partners
Private equity firm. Fast-moving, high-expectations. Needs an org assessment
of a portfolio company. Very low patience for process -- they want findings fast.
Elliot has a pre-existing relationship with the managing partner.

Client H -- Harbor City Government (Parks Dept.)
Municipal parks department doing a 10-year capital planning study.
Lots of stakeholders -- parks staff, city council, community groups.
Needs public engagement support and a formal report for the city council.

Client I -- ClearView Diagnostics
Healthcare tech startup. Building a clinical decision support tool.
Needs help structuring their regulatory strategy and drafting FDA submission
materials. Technical and regulatory complexity is high. Startup culture --
informal, fast, sometimes chaotic.

Client J -- The Holloway Foundation
Private philanthropy. Wants a landscape scan and strategic options memo on
workforce development funding. Small team, thoughtful, low-maintenance.
Primarily needs a polished, well-written deliverable.

Client K -- Summit Retail Group
Multi-location retail chain. Undergoing a cost reduction initiative.
Wants operational benchmarking and process recommendations.
Client stakeholders are skeptical of consultants -- they've had bad experiences
before. Need someone who can build trust quickly.

Client L -- Vance Biomedical Research Institute
Academic research institute. Needs help redesigning their grant reporting
process and building a data tracking system. Methodical, detail-oriented
stakeholders. Comfortable with technical complexity."""

# Stage 1 user prompt template (paste-style from the activity)
USER_PROMPT_STAGE1 = (
    "Below are descriptions of our 6 staff members and 12 clients.\n"
    "Please make the best possible assignments.\n\n"
    f"{STAFF_AND_CLIENTS}"
)

# 1. AI HELPER ###################################

def query_ollama_chat(messages: list, model: str = OLLAMA_MODEL) -> str:
    """
    Send a multi-turn chat to Ollama (local or Cloud) and return the assistant text.

    The 'messages' list is a normal OpenAI/Ollama-style chat history --
    we pass it through unchanged so we can extend it for the Stage 2 follow-up.
    """
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    response = requests.post(url, headers=headers, json=body, timeout=180)
    response.raise_for_status()
    return response.json()["message"]["content"]


# 2. STAGE 1: RUN THE ASSIGNMENT PROMPT ###################################

print("=" * 70)
print("📋 ACTIVITY: AI Assigner -- Staff-Client Assignment")
print("=" * 70)
print(f"☁️  Model: {OLLAMA_MODEL}  |  Host: {OLLAMA_HOST}")
print()

print("-" * 70)
print("🔧 Stage 1 -- Running assignment prompt...")
print("-" * 70)

# Build the chat history; we'll keep extending it for Stage 2
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": USER_PROMPT_STAGE1},
]

stage1_response = query_ollama_chat(chat_history)
chat_history.append({"role": "assistant", "content": stage1_response})

print()
print(stage1_response)
print()

# 3. STAGE 2: STRESS-TEST AN ASSIGNMENT ###################################

def pick_weak_pairing(table_text: str) -> tuple[str, str]:
    """
    Ask the model to name the single weakest staff-client pairing from its own
    Stage 1 table. Returns (staff_name, client_label). If extraction fails we
    fall back to the most common surprise: a junior consultant on a tough client.
    """
    extractor_prompt = (
        "From the assignment table below, identify the SINGLE pairing you would "
        "rate as the weakest fit. Respond on exactly one line in this format and "
        "nothing else:\n"
        "STAFF=<staff name>; CLIENT=<client letter and name>\n\n"
        f"{table_text}"
    )
    try:
        reply = query_ollama_chat([{"role": "user", "content": extractor_prompt}])
        match = re.search(r"STAFF=\s*([^;]+?)\s*;\s*CLIENT=\s*(.+)", reply)
        if match:
            return match.group(1).strip(), match.group(2).strip().splitlines()[0]
    except Exception:
        # If extraction fails, fall through to the default surprise
        pass
    return "Dana Park", "Client K -- Summit Retail Group"


STRESS_TEST_STAFF, STRESS_TEST_CLIENT = pick_weak_pairing(stage1_response)

stage2_prompt = (
    f"I'm not sure about the assignment of {STRESS_TEST_STAFF} to {STRESS_TEST_CLIENT}. "
    "Can you reconsider this pairing and either defend it or suggest an alternative?"
)

print("-" * 70)
print("🔧 Stage 2 -- Stress-testing one assignment...")
print(f"   ✏️  Challenge: {STRESS_TEST_STAFF} -> {STRESS_TEST_CLIENT}")
print("-" * 70)

chat_history.append({"role": "user", "content": stage2_prompt})
stage2_response = query_ollama_chat(chat_history)
chat_history.append({"role": "assistant", "content": stage2_response})

print()
print(stage2_response)
print()

# 4. STAGE 3: REFLECTION ###################################

REFLECTION = (
    "The AI weighted explicit cues most heavily -- domain keywords (healthcare, "
    "nonprofit, finance/regulatory), seniority labels, and stated communication "
    "style -- and used the named relationship between Elliot and Meridian Capital "
    "as a hard tiebreaker. What it tended to miss was seniority-versus-difficulty "
    "balance: with only six staff and twelve clients, the toughest leftover engagement "
    "(Summit Retail's skeptical stakeholders) ends up on the most junior consultant, "
    "and the model accepts that trade-off rather than questioning the constraint. I "
    "would trust this output as a starting point because it explicitly flags weak "
    "fits and explains the rationale, but I would not deploy it without a managing-"
    "partner pass to rebalance high-risk clients onto more senior staff or pair the "
    "junior consultant with a senior backup."
)

print("-" * 70)
print("🧾 Stage 3 -- Reflection (3-4 sentences)")
print("-" * 70)
print(REFLECTION)
print()

# 5. SAVE ARTIFACTS FOR SUBMISSION ###################################

# A single combined transcript is the easiest screenshot target
transcript_path = OUT_DIR / "assigner_transcript.md"
transcript = (
    "# AI Assigner -- Activity Submission\n\n"
    f"- Model: `{OLLAMA_MODEL}`\n"
    f"- Host: `{OLLAMA_HOST}`\n\n"
    "## Stage 1 -- Assignment Table and Logic\n\n"
    f"{stage1_response}\n\n"
    "---\n\n"
    f"## Stage 2 -- Stress Test: {STRESS_TEST_STAFF} -> {STRESS_TEST_CLIENT}\n\n"
    f"**Follow-up prompt:** {stage2_prompt}\n\n"
    f"{stage2_response}\n\n"
    "---\n\n"
    "## Stage 3 -- Reflection\n\n"
    f"{REFLECTION}\n"
)
transcript_path.write_text(transcript, encoding="utf-8")

print("=" * 70)
print("📊 Summary")
print("=" * 70)
print(f"💾 Saved transcript: {transcript_path}")
print(f"   ✅ Stage 1 chars: {len(stage1_response)}")
print(f"   ✅ Stage 2 chars: {len(stage2_response)}")
print(f"   ✅ Reflection chars: {len(REFLECTION)}")
