# AI Assigner -- Activity Submission

- Model: `gpt-oss:120b`
- Host: `https://ollama.com`

## Stage 1 -- Assignment Table and Logic

**Assignment Table**

| Staff Member | Client 1 | Client 2 | Rationale (1 sentence) |
|-------------|----------|----------|------------------------|
| Alex Chen | Client B – Atlas Financial Group | Client K – Summit Retail Group | Alex’s regulatory‑compliance background and love of clear, organized deliverables match Atlas, while his detail‑orientation and methodical style suit Summit’s data‑driven cost‑reduction work. |
| Brianna Okafor | Client A – Riverdale Community Health Clinic | Client E – Greenway Transit Authority | Brianna’s nonprofit/public‑sector expertise and strong stakeholder‑engagement skills fit the collaborative, committee‑driven health clinic and the politically sensitive transit agency. |
| Carla Mendez | Client D – Nexagen Pharmaceuticals | Client L – Vance Biomedical Research Institute | Carla’s healthcare‑focused, data‑heavy expertise is a perfect fit for Nexagen’s KPI dashboard and Vance’s grant‑reporting/data‑tracking system. |
| Dana Park | Client F – Solstice Consumer Goods | Client H – Harbor City Government (Parks Dept.) | Dana’s marketing/consumer‑research background and creative flair suit Solstice’s brand‑positioning study; her ability to handle smaller, well‑defined tasks makes the public‑engagement report for the parks department manageable. |
| Elliot Vasquez | Client G – Meridian Capital Partners | Client C – BrightPath Schools (Charter Network) | Elliot’s partner‑level strategy and relationship‑management experience align with Meridian’s high‑stakes org assessment, and his organizational‑change skill set can drive BrightPath’s rapid‑growth org‑design despite the client’s fast‑moving nature (fit is moderate). |
| Fiona Marsh | Client J – The Holloway Foundation | Client I – ClearView Diagnostics | Fiona’s journalistic writing talent and comfort with deliverable‑heavy projects make her ideal for the polished memo for the foundation and the technical FDA‑submission drafting for the healthcare‑tech startup. |

**Flagged Weak Fits**  
- **Elliot – Client C (BrightPath Schools):** The charter network’s fast‑moving, loosely defined schedule is less aligned with Elliot’s preference for high‑visibility, well‑structured engagements.  
- **Dana – Client H (Harbor City Government):** The municipal project involves senior public officials and extensive stakeholder coordination, which may stretch Dana’s junior experience; she will need close support from senior staff.

---

**Overall Assignment Logic**

I matched each staff member’s core expertise, experience level, and preferred working style to the two clients where those attributes are most needed, ensuring every client is covered exactly once. Senior consultants with strong regulatory or data‑analytics backgrounds (Alex, Carla) were paired with highly organized, technically demanding clients. Brianna’s nonprofit and stakeholder‑engagement strengths were directed to the two public‑sector projects that value collaborative facilitation. Elliot’s partner‑level strategic and relationship skills were reserved for the high‑visibility, fast‑paced engagements, while Fiona’s writing excellence was assigned to the two deliverable‑heavy, communication‑focused assignments. Finally, Dana’s creative, marketing‑oriented skill set was used for the more tactical, well‑scoped market‑research and public‑engagement tasks, acknowledging that the municipal report may be a stretch for her junior level. This distribution respects the rule that each staff member receives exactly two clients and each client receives exactly one staff member, while highlighting the few assignments where fit is less than ideal.

---

## Stage 2 -- Stress Test: Dana Park -> H – Harbor City Government (Parks Dept.)

**Follow-up prompt:** I'm not sure about the assignment of Dana Park to H – Harbor City Government (Parks Dept.). Can you reconsider this pairing and either defend it or suggest an alternative?

**Why Dana Park can still be a good fit for H – Harbor City Government (Parks Dept.)**

1. **Scope & Complexity** – The parks‑department engagement is a **well‑defined, phased study** that culminates in a single, formal 10‑year capital‑planning report.  The deliverable is concrete (a written report) and the research‑and‑analysis work can be broken into bite‑size work‑streams (e.g., community‑survey design, stakeholder‑mapping, cost‑modeling).  That matches Dana’s strength on **smaller, well‑scoped tasks**.

2. **Creative / Communications Angle** – The public‑engagement component (focus groups, visual “park‑vision” concepts, outreach‑materials) benefits from Dana’s **marketing and consumer‑research background**.  She can design the surveys, craft the outreach messaging, and produce the graphics that make the final report compelling—exactly the type of creative work she enjoys.

3. **Mentoring Structure** – Because Dana is junior, we can **pair her with a senior “shadow”** (e.g., Carla Mendez or Brianna Okafor) who will attend the higher‑level stakeholder meetings and review drafts.  This gives Dana the exposure she needs while ensuring the city’s senior officials feel confident the work is overseen by an experienced consultant.

4. **Risk Management** – The project’s **long timeline** (several months) reduces the pressure of rapid‑turnaround that might overwhelm a junior consultant.  It also provides ample time for Dana to ask questions, iterate, and receive feedback before each deliverable is submitted.

Taken together, the combination of a clearly bounded deliverable, a creative public‑engagement sub‑task, and a built‑in senior mentorship makes the Harbor City assignment **feasible and development‑positive** for Dana.

---

### Alternative Re‑assignment (if you prefer a senior‑level lead)

If you would rather have a more senior consultant own the municipal engagement, we can **swap the Harbor City assignment with Brianna Okafor’s Client A (Riverdale Community Health Clinic)** and give Dana the clinic instead.  The rationale for that swap would be:

| Staff | New Client | Reason |
|-------|------------|--------|
| **Brianna Okafor** | **Client H – Harbor City Government (Parks Dept.)** | Brianna’s public‑sector expertise and strong stakeholder‑engagement skills are a natural fit for the multi‑agency, community‑focused parks study. |
| **Dana Park** | **Client A – Riverdale Community Health Clinic** | The clinic’s strategic‑planning process is modest in scope, with a clear deliverable (written strategic plan) and a collaborative but slow‑moving decision‑making body—well suited to Dana’s ability to handle defined tasks while learning facilitation under senior guidance. |

All other pairings would stay exactly as originally proposed, preserving the “two‑clients‑per‑staff” and “one‑client‑per‑staff” constraints.

---

**Bottom line:**  
- **Defend**: Dana can successfully lead the Harbor City engagement with senior mentorship, leveraging her creative, research‑driven skill set.  
- **Alternative**: If you prefer a senior lead, simply exchange Dana’s assignment with Brianna’s, keeping the overall staffing matrix balanced and still meeting every client’s needs.

---

## Stage 3 -- Reflection

The AI weighted explicit cues most heavily -- domain keywords (healthcare, nonprofit, finance/regulatory), seniority labels, and stated communication style -- and used the named relationship between Elliot and Meridian Capital as a hard tiebreaker. What it tended to miss was seniority-versus-difficulty balance: with only six staff and twelve clients, the toughest leftover engagement (Summit Retail's skeptical stakeholders) ends up on the most junior consultant, and the model accepts that trade-off rather than questioning the constraint. I would trust this output as a starting point because it explicitly flags weak fits and explains the rationale, but I would not deploy it without a managing-partner pass to rebalance high-risk clients onto more senior staff or pair the junior consultant with a senior backup.
