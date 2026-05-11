# LAB Congress -- Plain Language Translator: Live Translations

- Model: `gpt-oss:120b`
- Host: `https://ollama.com`
- Samples translated: 3

Each section below shows the structured user input the agent received and 
the verbatim agent output. The system prompt is in 
[`lab_congress_submission.md`](../lab_congress_submission.md).

---

## Sample 1 -- FOIA law-enforcement exemption

- Citation: `5 U.S.C. § 552(b)(7)`
- Target grade level: 8
- Audience hint: constituent letter

**Agent output:**

```text
ORIGINAL
> """
> This section does not apply to matters that are records or information compiled for law enforcement purposes, but only to the extent that the production of such law enforcement records or information (A) could reasonably be expected to interfere with enforcement proceedings, (B) would deprive a person of a right to a fair trial or an impartial adjudication, (C) could reasonably be expected to constitute an unwarranted invasion of personal privacy, (D) could reasonably be expected to disclose the identity of a confidential source, (E) would disclose techniques and procedures for law enforcement investigations or prosecutions or would disclose guidelines for law enforcement investigations or prosecutions if such disclosure could reasonably be expected to risk circumvention of the law, or (F) could reasonably be expected to endanger the life or physical safety of any individual.
> """

PLAIN LANGUAGE TRANSLATION
This rule does not cover records or information that are put together for law‑enforcement (the police or other agencies that enforce the law) purposes, except when giving out those records could:

(A) likely interfere with ongoing law‑enforcement actions;

(B) likely take away a person’s right to a fair trial (a trial that is just) or an impartial adjudication (a neutral decision);

(C) likely be an unwarranted invasion of personal privacy (a privacy breach that is not justified);

(D) likely reveal the identity of a confidential source (someone who gave information under a promise of secrecy);

(E) likely disclose the techniques and procedures (methods and steps) that law‑enforcement uses in investigations or prosecutions, or the guidelines (rules) for those investigations, if such disclosure could reasonably be expected to help people get around the law;

(F) likely endanger the life or physical safety of any individual.

NUANCE WARNINGS
- None.

COVERAGE NOTES
- Subparts collapsed: None
- Cross-references kept verbatim: None

QUALITY SELF-CHECK
- Reading level (estimated grade): 8
- Confidence in faithfulness: High
- Recommended next step: Cleared for constituent reply
```

---

## Sample 2 -- SBA size-standard rulemaking authority

- Citation: `15 U.S.C. § 632(a)(2)(A)`
- Target grade level: 10
- Audience hint: junior staffer brief

**Agent output:**

```text
**ORIGINAL**  
> 
> In addition to the criteria specified in paragraph (1), the Administrator may specify detailed definitions or standards by which a business concern may be determined to be a small business concern for the purposes of this chapter or any other Act. Unless specifically authorized by statute, no Federal department or agency may prescribe a size standard for categorizing a business concern as a small business concern, unless such proposed size standard (i) is proposed after an opportunity for public notice and comment, (ii) provides for determining the size of a business concern on the basis of the number of employees, the dollar volume of business, the net worth, the net income, a combination thereof, or other appropriate factors, and (iii) is approved by the Administrator.  
> **15 U.S.C. § 632(a)(2)(A)**  

**PLAIN LANGUAGE TRANSLATION**  
In addition to the rules already listed in paragraph (1), the **Administrator** (the official who runs the program) can set detailed definitions or standards that decide whether a company counts as a **small business concern** (a business that meets the small‑business criteria) for this chapter or any other law.  

Except when a law specifically says otherwise, no federal department or agency can create a **size standard** (the rule that defines what qualifies as a small business) for labeling a company as a small business concern unless the following three conditions are met:  

1. The proposed size standard is released only after giving the public a chance to see the proposal and submit comments (**public notice and comment**).  
2. The standard explains how to measure a company’s size using one or more of these factors: the number of employees, the total sales dollars, the net worth, the net income, a mix of those, or other appropriate factors.  
3. The Administrator approves the proposed size standard.  

**NUANCE WARNINGS**  
- [NUANCE WARNING: “other appropriate factors”] Simplifying this phrase could miss the fact that agencies may consider additional, unspecified criteria that are legally permissible.  

**COVERAGE NOTES**  
- Subparts collapsed: None  
- Cross-references kept verbatim: paragraph (1), Administrator  

**QUALITY SELF‑CHECK**  
- Reading level (estimated grade): 10  
- Confidence in faithfulness: High  
- Recommended next step: Cleared for junior staffer brief
```

---

## Sample 3 -- Clean Air Act new source performance standard

- Citation: `40 CFR 60.40c (excerpt, simplified)`
- Target grade level: 8
- Audience hint: constituent letter

**Agent output:**

```text
ORIGINAL
> """
> The provisions of this subpart are applicable to each steam generating unit for which construction, modification, or reconstruction is commenced after June 9, 1989 and that has a maximum design heat input capacity of 29 megawatts (100 million Btu per hour) or less, but greater than 2.9 megawatts (10 million Btu per hour). Affected facilities that also meet the applicability requirements under any other standard in subparts Da, Db, or Ea of this part are not subject to that other standard but remain subject to this subpart.
> """
> Source citation: 40 CFR 60.40c

PLAIN LANGUAGE TRANSLATION
This part applies to each steam‑generating unit (a machine that makes steam) for which construction (building), modification (changing), or reconstruction (rebuilt) is started after June 9, 1989 and that has a maximum design heat input capacity (the highest amount of heat the unit is built to handle) of more than 2.9 megawatts (10 million Btu per hour) but not more than 29 megawatts (100 million Btu per hour). Facilities that also meet the applicability requirements (the conditions that make a rule apply) of any other standard (rule) in subparts Da, Db, or Ea are not required to follow that other standard, but they still must follow this subpart.

NUANCE WARNINGS
- [NUANCE WARNING: “maximum design heat input capacity”] Simplifying this phrase could hide the technical meaning that it refers to the design‑rated heat input, not actual operating output.

COVERAGE NOTES
- Subparts collapsed: None
- Cross-references kept verbatim: subparts Da, Db, Ea

QUALITY SELF-CHECK
- Reading level (estimated grade): 8
- Confidence in faithfulness: High
- Recommended next step: Cleared for constituent reply
```

---
