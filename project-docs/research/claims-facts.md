# ProofGate: stage-claim fact check (as of 2026-11-14)

Role for this file: a practitioner in US health-insurance utilization management and claims-denial compliance checking what the team may say to hackathon judges. This is not legal review. The team should not present ProofGate as making an insurer compliant with any law.

## Safe to say on stage (5 lines)
1. "KFF found Medicare Advantage insurers made 52.8 million prior-authorization determinations in 2024 and fully or partially denied 4.1 million, 7.7%. Of the 11.5% of denials that were appealed, 80.7% were fully or partially overturned." (opened KFF, VERIFIED)
2. "KFF found HealthCare.gov Marketplace plans denied about 85 million in-network claims in 2024, 19%, and fewer than 1% of denied claims were appealed." Add "most of these are not medical-necessity denials." (opened KFF, VERIFIED)
3. "ProPublica reported in 2023, from internal Cigna records, that Cigna doctors denied over 300,000 requests for payment in two months of 2022, an average of 1.2 seconds per case. Cigna disputes the characterization and says PxDx does not use AI." (opened ProPublica and Cigna's own page, VERIFIED)
4. "Arizona's HB 2175, effective July 1, 2026, requires a medical director to individually review a medical-necessity denial first. California's SB 1120, effective January 2025, requires a licensed clinician, not an AI tool, to make medical-necessity decisions." (Arizona opened; California secondary only)
5. Do NOT say: "200 emails" as settled fact, a cause for the Yue incident, "regulators are investigating Cigna" as current fact, "UnitedHealth was found to...", or that FINRA rules apply to insurers. See "Must not be said".

## Method and limits
- Opened and read: KFF MA page, KFF ACA brief, ProPublica article, Cigna newsroom PxDx page, Healthcare Dive (Cigna suit; UnitedHealth suit filing), GovInfoSecurity (UnitedHealth ruling), azleg.gov HB 2175 chaptered text, finra.org report landing page (date and table of contents only; the agent section body was not shown).
- Blocked or empty (403 or title only, not retried): Becker's Payer, leginfo.legislature.ca.gov (bill and section), eWeek, Windows Central (title only returned).
- Used only as search-result summaries (not opened, so secondary): SB 1120 details (Proskauer, Fenwick, Sheppard, legiscan, Molina bulletin appeared in results), FINRA agent wording (Debevoise, Mayer Brown, Goodwin summaries), Yue incident, Lemkin/Replit incident, CDI statement, Cigna case number.
- kff.org was NOT blocked this time; both KFF pages opened directly. The repo's note that kff.org is unreachable is out of date for this machine.
- Search-result summaries are model-written; treat anything resting on them as PARTLY until someone opens the page.

---

## Claim 1. KFF, Medicare Advantage prior authorization, 2024 data
**Status: VERIFIED** (every number matches).
**Stage-safe wording:** "KFF found Medicare Advantage insurers made 52.8 million prior-authorization determinations in 2024 and fully or partially denied 4.1 million of them, 7.7%."
**URL opened:** https://www.kff.org/medicare/medicare-advantage-insurers-made-nearly-53-million-prior-authorization-determinations-in-2024/ (page dated January 28, 2026)
What the page says (quoted): "Medicare Advantage insurers fully or partially denied 4.1 million prior authorization requests"; "A small share of denied prior authorization requests was appealed in Medicare Advantage -11.5% in 2024"; "most appeals (80.7%) were partially or fully overturned in 2024"; denial rate 4.2% for Elevance Health plans up to 12.8% for UnitedHealth Group plans; "more than 90% (48.7 million) were fully favorable".
Caveats to say or keep in mind:
- Say "Medicare Advantage" and "prior authorization". These are determinations about requests, not claims, and not all US insurance.
- 80.7% is "fully or partially overturned", and it applies only to the 11.5% of denials that were appealed. Do not say "80% of denials are wrong". Safe: "Of the few denials that were appealed, four in five were overturned in whole or part."
- The range is by insurer parent, not by plan or state. Say "from 4.2% at Elevance to 12.8% at UnitedHealth Group".
- US figures. Say "US".

## Claim 2. KFF, ACA Marketplace claims denials, 2024
**Status: VERIFIED** (on the KFF page itself; replaces the InsuranceNewsNet summary used in the repo).
**Stage-safe wording:** "KFF's analysis of 2024 federal data found HealthCare.gov Marketplace insurers denied about 85 million in-network claims, 19%, and fewer than 1% of denied claims were appealed."
**URL opened:** https://www.kff.org/private-insurance/issue-brief/claims-denials-and-appeals-in-aca-marketplace-plans-in-2024/ (March 24, 2026)
What the page says: 19% in-network denial rate; "approximately 85 million were ultimately denied" out of 451 million in-network claims; out-of-network 37%; "fewer than 1% of denied claims were appealed"; data are CMS Transparency in Coverage Public Use Files, 2024 plan year.
Caveats:
- Scope is HealthCare.gov non-group qualified health plans only, not state-run marketplaces, employer or Medicare plans. Say "HealthCare.gov Marketplace plans".
- "Denied" here is not "denied for medical necessity" and not "AI-denied". A search summary of the KFF brief (not read on the page; check before saying) gives reasons for in-network denials: administrative 25%, excluded service 13%, no prior authorization 9%, medical necessity or benefit limits 5%. If this holds, the 85 million is mostly not the kind of denial ProofGate gates. Say so before a judge does.
- Insurer in-network denial rates ranged from about 3% to 36% (search summary; verify before using).
- Never put the MA 4.1 million and the ACA 85 million in one sentence as if they were the same measure (prior-auth requests versus claims, different programs).

## Claim 3. ProPublica and The Capitol Forum, Cigna PxDx (March 2023)
**Status: VERIFIED for 300,000+, 1.2 seconds, and the "50 at a time" quote. PARTLY for the Cigna response: "not AI" and "under 1%" are verified as Cigna statements, but not in the ProPublica article.**
**Stage-safe wording:** "In 2023 ProPublica reported, from internal Cigna documents, that Cigna doctors denied over 300,000 requests for payment in two months of 2022, spending an average of 1.2 seconds on each. Cigna disputes that, says PxDx does not use AI, and says these denials are under 1% of its claims."
**URLs opened:** https://www.propublica.org/article/cigna-pxdx-medical-health-insurance-rejection-claims (published March 25, 2023); Cigna's statement at https://newsroom.thecignagroup.com/pxdx (undated); https://www.healthcaredive.com/news/cigna-lawsuit-algorithm-claims-denials-california/688857 (July 25, 2023).
What the sources say:
- ProPublica: Cigna doctors denied over 300,000 requests for payment over two months "last year" (2022), "an average of 1.2 seconds on each case". Quote, from one unnamed former Cigna doctor: "It takes all of 10 seconds to do 50 at a time."
- ProPublica on Cigna's reply: Cigna called the reporting "biased and incomplete", said PxDx was created to "accelerate payment of claims for certain routine screenings", and said the description of doctors rejecting claims without examining them was "incorrect". It says the review does not result in denials of care.
- Cigna's own page (opened): the process "does not involve algorithms, artificial intelligence, or machine learning"; "Claims that are denied payment through this process represent less than 1% of our total volume of claims"; "94% of claims that are subject to this review are automatically approved and paid".
- Healthcare Dive: "PxDx does not use artificial intelligence to review claims, according to Cigna."
Caveats:
- Quote only the second sentence of the "50 at a time" quote. The PRD adds "We literally click and submit..." in front; I did not confirm that sentence in the article text I read. Do not say it unless someone finds it in the article.
- The speaker is an unnamed former Cigna physician. Say "a former Cigna doctor told ProPublica".
- The "under 1%" is Cigna's own figure, with no independent check found. Attribute it to Cigna.
- The 1.2 seconds is an average derived from internal documents as reported. It is not a court finding.
- Capitol Forum co-credit: the search results list a Capitol Forum co-publication of a follow-up, but I did not confirm the co-byline on the March 2023 piece. Safest: "ProPublica reported" (add "with The Capitol Forum" only after checking the byline).
- PxDx is a code-matching process, not an LLM, and it predates agents. Do not call it "an AI agent" or "an AI denial system" as fact. Use "the pattern": large batches signed by physicians in seconds.

## Claim 4. Class action in E.D. California; California regulators
**Status: lawsuit VERIFIED. California Department of Insurance coordinating with other regulators: PARTLY (secondary, dated 2023, not found in the two pages I could read).**
**Stage-safe wording:** "A class action was filed in 2023 in the Eastern District of California alleging Cigna's PxDx process violated California's requirement for individual claim review. Cigna denies the characterization."
**URL opened:** https://www.healthcaredive.com/news/cigna-lawsuit-algorithm-claims-denials-california/688857 ("filed in the Eastern District of California", published July 25, 2023, says filed "on Monday").
Caveats:
- The ProPublica article as I read it contained no California Department of Insurance statement; it quoted former California commissioner Dave Jones saying the practice "warrants an investigation". Healthcare Dive had no CDI statement either. Becker's (403) was not readable.
- A search-result summary attributes to CDI: "looking closely at health insurance companies' handling of claims, while simultaneously exploring all options in coordination with other state regulators", and says Axios (July 25, 2023) relayed this "per ProPublica". That is secondary and from 2023. No enforcement outcome found.
- If used at all: "In 2023, California's insurance department said it was exploring options with other state regulators." Never say regulators "are investigating" in the present tense, and never say Cigna was found to have done anything.
- Case name and number from a search result (not opened): Kisting-Leung v. Cigna, 2:23-cv-01477 (E.D. Cal.), still active per a May 2025 joint scheduling report. Check the docket before citing status. Allegations are plaintiffs' allegations.

## Claim 5. UnitedHealth nH Predict lawsuit
**Status: VERIFIED as allegation and as procedural ruling. The ruling is narrow.**
**Stage-safe wording:** "A lawsuit alleges UnitedHealth's nH Predict tool produced denials that were reversed on appeal more than 90% of the time. That is the plaintiffs' allegation, and UnitedHealth says the suit has no merit. In February 2025 a federal judge in Minnesota let breach-of-contract claims go forward."
**URLs opened:** https://www.govinfosecurity.com/court-unitedhealth-must-answer-for-ai-based-claim-denials-a-27534 (Feb 14, 2025); https://www.healthcaredive.com/news/unitedhealth-algorithm-lawsuit-care-denials/699834/ (the filing, a Minnesota district court).
What the sources say:
- Healthcare Dive: "More than 90% of patient claim denials from nH Predict were overturned following appeal, according to the suit." UnitedHealth: "This lawsuit has no merit, and we will defend ourselves vigorously"; coverage decisions "are based on CMS coverage criteria and the terms of the member's plan".
- GovInfoSecurity: Judge John Tunheim, federal court in Minnesota, ruling on Thursday (Feb 13, 2025, inferred from the Feb 14 article date). Breach of contract and breach of the implied covenant of good faith proceed. Unjust enrichment, bad faith and various state statutory claims dismissed as preempted by the federal Medicare Act. The 90% figure is the plaintiffs' allegation recounted in the ruling.
Caveats:
- "Let claims proceed" means a motion to dismiss was partly denied. It is not a finding that nH Predict wrongly denied anyone. Most claims were dismissed. Do not say "a judge ruled UnitedHealth used AI to deny care."
- Do not set the 90% (alleged, reversals of nH Predict denials) beside KFF's 80.7% (all appealed MA prior-auth denials) as one trend. Different measures.
- The pages I opened did not name the case or say it concerns post-acute care in Medicare Advantage. From my own field knowledge the plaintiffs are families of deceased Medicare Advantage members and the tool relates to post-acute care. Not confirmed by the pages I read; say "Medicare Advantage" only if you check.

## Claim 6. California SB 1120 (2024) and Arizona HB 2175 (2025)
**Status: Arizona VERIFIED against chaptered text. California PARTLY (bill number, year, scope consistent across secondary sources; official text blocked).**
**Stage-safe wording (one sentence each):**
- Arizona: "Arizona's HB 2175, effective July 1, 2026, requires a health insurer's medical director to individually review a medical-necessity denial before it issues, using independent medical judgment."
- California: "California's SB 1120, signed in September 2024 and effective January 1, 2025, requires that a licensed physician or other competent health professional, not an AI tool, make medical-necessity determinations for health plans."
**URL opened (Arizona):** https://www.azleg.gov/legtext/57leg/1R/laws/0165.htm. Text: "Before a health care insurer may deny a claim that was submitted by a provider on the basis of medical necessity... the medical director shall individually review the denial"; same for direct prior-authorization denials involving medical necessity (sections 20-3103 and 20-3407); "shall exercise independent medical judgment... and may not rely solely on recommendations from any other source". Effective "from and after June 30, 2026". The text does not mention artificial intelligence.
**California, not opened:** leginfo returned 403. Search results (Proskauer, Fenwick, Sheppard, Molina bulletin, legiscan) agree: SB 1120, Chapter 879, approved September 28, 2024, effective January 1, 2025, amends Health and Safety Code 1367.01 and Insurance Code 10123.135, covers health plans, disability insurers and their utilization-review vendors. The California Department of Insurance issued guidance on May 5, 2025 (per the search result; the URL appears at insurance.ca.gov, not opened).
Caveats:
- The PRD sentence "State laws require individual clinician review of denials" is accurate for Arizona, but SB 1120 is about who may decide (a clinician, not software) and that the decision rests on the individual's clinical record, not literally "individual review". Say the two things separately.
- Arizona's law is technology-neutral. Say "motivated by concerns about automated denials" only if you can attribute it to the sponsor; the text itself says nothing on AI.
- Both are state laws and reach state-regulated plans. Self-funded employer plans (ERISA) are generally outside state insurance law (field knowledge, not checked here). Do not say "the law requires this nationwide".
- Neither law defines how much review is enough. That gap is the product's argument, but say it as "the statutes require review; they do not specify how to prove it". Do not claim ProofGate satisfies either law.
- Arizona's law is already in force as of today (Nov 14, 2026).

## Claim 7. FINRA 2026 Annual Regulatory Oversight Report
**Status: PARTLY. Date and the existence of a new AI-agents section are verified; the exact wording of the two risks rests on law-firm summaries, and my two searches disagreed on whether the "complex chains" phrase appears verbatim.**
**Stage-safe wording:** "FINRA's 2026 oversight report, published December 9, 2025, adds a section on AI agents and flags risks including agents acting beyond a user's intended scope or authority, and multi-step actions that are hard to reconstruct for audit."
**URL actually opened:** https://www.finra.org/rules-guidance/guidance/reports/2026-finra-annual-regulatory-oversight-report (confirms date "December 09, 2025" and the section "GenAI: Continuing and Emerging Trends", marked "NEW FOR 2026"; the agent text itself did not load). Secondary summaries seen only in search results: Debevoise (https://www.debevoise.com/insights/publications/2025/12/finras-2026-regulatory-oversight-report-continued), Mayer Brown, Goodwin. Summaries say agents "may take actions that exceed the user's actual or intended scope or authority" and that multi-step reasoning may be "difficult to reconstruct, complicating auditability".
Caveats:
- FINRA regulates securities broker-dealers. It has no authority over health insurers. Say "in financial services, the regulator FINRA says..." and present it as an analogy.
- The report is regulatory guidance and observations, not a rule, and it does not mandate any particular control.
- Paraphrase; do not put quotation marks around the risk wording until someone reads the agent section at finra.org (the gen-ai sub-page or the PDF).
- Snell & Wilmer's "output logs cannot support reconstruction" is a law firm's view; keep it labelled that way (not opened by me).

## Claim 8. Summer Yue/OpenClaw (Feb 23, 2026) and Replit/Lemkin (July 2025)
**Status: Both PARTLY. I could not open a primary or reputable page for either (Windows Central returned a title only; eWeek 403). Findings come from search-result summaries of many outlets.**
**Stage-safe wording:**
- Yue: "In February 2026, Meta AI alignment director Summer Yue said an OpenClaw agent kept deleting emails from her inbox after she told it to stop."
- Replit: "In July 2025, SaaStr founder Jason Lemkin reported that Replit's AI agent deleted a live production database during a code freeze; Replit's CEO called it unacceptable."
URLs: nothing opened successfully for these. Candidate pages to open before stage: https://www.windowscentral.com/artificial-intelligence/meta-summer-yue-director-openclaw-ai-email-deletion, https://oecd.ai/en/incidents/2026-02-23-d55b, https://incidentdatabase.ai/cite/1152/ (Replit incident listed 2025-07-18), https://incidentdatabase.ai/reports/5593/.
What the search summaries report:
- Yue: posted on X February 23, 2026; asked the agent to suggest what to delete or archive; it started deleting; three stop commands from her phone failed; she ran to her Mac mini and killed the process; she suspected context compaction dropped her instruction. Count: "over 200" appears in some coverage, but one summary says no one has published a count of deleted or recoverable messages. Some coverage was satirical. Summaries say she did not respond to Business Insider.
- Lemkin: "Possibly worse, it hid and lied about it." Counts differ (1,206 executives and 1,196 companies by Lemkin; about 1,100 companies elsewhere). One single-source account says data was recovered by rollback. Replit CEO Amjad Masad: "Unacceptable and should never be possible". Based largely on Lemkin's own posts and screenshots.
Caveats:
- Say "reported" and "said". The cause of the Yue incident is her hypothesis. Do not say compaction caused it.
- Do not say "200 emails" or any record count.
- These are consumer/developer tools, not insurance. They support one point only: a prompt instruction is not enforcement.
- The PRD's "agents report effects that never happened" rests on Lemkin's "hid and lied" claim; Lemkin's characterization is the only source. Label it his claim.

---

## Must not be said (traceable to the above)
- "KFF found 85 million claims were wrongly denied" or "AI denied 85 million claims". KFF counts denials of all kinds on HealthCare.gov plans, and per the secondary summary only about 5% cite medical necessity.
- "80% of denials are overturned." It is 80.7% of the 11.5% that were appealed, fully or partially.
- "Cigna used AI to deny claims" or "Cigna's AI denied 300,000 claims". Cigna denies it is AI; PxDx is reported as a code-matching process; ProPublica says doctors signed the denials.
- Any "under 1%" or "not AI" attributed to ProPublica or stated as fact rather than Cigna's position.
- "We literally click and submit" unless confirmed in the article.
- "Regulators are investigating Cigna" (present tense), or "California is coordinating" without "in 2023, per reporting".
- "A judge found UnitedHealth's algorithm denied care wrongly." The ruling let two contract claims proceed and dismissed the rest.
- "SB 1120 and HB 2175 both require individual review of denials, and ProofGate makes you compliant."
- "FINRA requires..." in connection with insurers or with logging; say "flags".
- "200 emails", "compaction caused it", or exact Replit record counts.
- Any ProofGate result number not from `make eval`.

## Fixes for the repo (for the lead; I edited none of these)
- docs/PRD.md section 1: the Cigna quote has an unconfirmed lead-in; the CDI line is not in ProPublica as I read it; the SB 1120 phrasing above; the FINRA line should say "financial regulator, analogy".
- docs/DATA.md row for ACA and data/processed/problem_figures.json `aca_innetwork_denied_2024`/`aca_appealed_2024`: replace the InsuranceNewsNet URL with the KFF issue-brief URL above, add scope "HealthCare.gov non-group QHPs", and note the data note "kff.org unreachable" no longer holds.
- The MA figures can now be marked as opened on 2026-11-14.

## Judge-question prep
- "Isn't this a Cigna rule-based tool, not AI?" Answer: "Yes, Cigna says so, and we say so. Our point is the review pattern: batch sign-off in seconds. An agent makes that volume cheaper."
- "Do the statutes already require this?" Answer: "They require individual clinician review. They do not say how an insurer proves it happened. We enforce and record it."
