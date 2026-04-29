# Fastest Non-Workshop Path for Your EHR Access-Risk Paper

## Better paper list

What the recent literature actually says is not “there are many strong recent EHR insider-threat papers.” It says something narrower and more useful: recent work is split across **three adjacent but still weakly integrated areas**—security auditing, audit-log workflow/context mining, and access-control frameworks. That fragmentation is exactly why your best shot is a **hybrid triage paper**, not a generic “ML for EHR anomaly detection” paper. citeturn4view1turn4view3turn7search2turn14search2turn9view0

### Core security and triage papers

**Evaluating the Effectiveness of Auditing Rules for Electronic Health Record Systems** — 2018, *AMIA Annual Symposium Proceedings*.  
Problem: hospitals already use hand-built high-risk auditing rules, but the paper asks whether those rules are actually effective at finding inappropriate access. Dataset: one week of data from a large EHR system, about **8 million accesses**. Method: evaluates individual rule flags, then ranks rules by their practical risk and by how often flagged accesses can still be “explained away” by clinical reasons. Evaluation: high-risk flag frequency and explainability rates. Key finding: simple rules fire more often than expected, but only **16%–43%** of flagged accesses can be explained away by five simple reasons, showing both signal and substantial ambiguity. Limitation: still a **post-hoc rule-evaluation** paper; no modern ML baseline, no review-budget metric, no reproducible data. Relation to your project: this is the **best justification for a rule-only baseline** and for why rule outputs need better triage. Cite as **core**. citeturn21search1turn22search1

**How to Cover up Anomalous Accesses to Electronic Health Records** — 2023, *USENIX Security 2023 prepublication / conference paper*.  
Problem: even if ML detectors catch illegitimate EHR accesses, can an insider evade them? Dataset: one year of real hospital access logs with **309,096 patients, 944,385 encounters, 11,591 users, and 26,992,636 accesses**; weekly graph splits average about **82,498 accesses**. Method: bipartite user-encounter graph anomaly detection with heuristics, matrix factorization, Node2Vec variants, and a graph autoencoder/GNN; then adversarial evasion and poisoning attacks against the detector. Evaluation: TPR, TNR, precision, AUC, plus attack success rate. Key finding: GNN-based detection works best among evaluated methods, but **evasion attacks can successfully disguise many target accesses**, while poisoning is harder in this dynamic setting. Limitation: illegitimate accesses are **simulated**, not adjudicated by compliance officers; the paper studies **robustness**, not operational audit triage. Relation to your project: this is the strongest recent empirical threat paper close to your topic, but it also exposes a weakness you can avoid—do not sell your model as “solving insider threat,” only as **triaging suspicious accesses under budget constraints**. Cite as **core**. citeturn12view0turn10view0

**Context-Based, Predictive Access Control to Electronic Health Records** — 2022, *Electronics*.  
Problem: how should an EHR decide access in emergency contexts, where static role rules are too rigid? Dataset: publicly available physiologic time-series for **4,000 patients**, reduced to **2,086** after preprocessing. Method: baseline ABAC plus LSTM forecasting of future patient vital signs, coupled with personalized fuzzy context handlers to estimate criticality and allow access. Evaluation: scenario-based comparisons among baseline ABAC, non-personalized, and personalized context handlers. Key finding: adding predicted physiological context improves dynamic emergency access decisions. Limitation: it is **not insider-threat detection**; it uses only a few patient metrics and focuses on emergency authorization rather than suspicious behavior monitoring. Relation to your project: useful as a **query-time / pre-decision** contrast paper, but not a baseline for suspicious access detection. Cite as **supporting**. citeturn4view4

### Context and audit-log mining papers that matter for feature design

**Context is Key: Using the Audit Log to Capture Contextual Factors Affecting Stroke Care Processes** — 2021, *AMIA Annual Symposium Proceedings 2020*.  
Problem: can audit logs measure contextual factors like provider busyness and team experience that affect care processes? Dataset: stroke thrombolysis process data; the accessible abstract does **not expose exact sample size**. Method: exploratory audit-log feature engineering around contextual care-process factors. Evaluation: correlations between contextual factors and stroke-care process measures. Key finding: audit logs can capture otherwise hard-to-measure workflow context. Limitation: not security-focused and not framed as anomaly detection. Relation to your project: very important for your **context feature engineering** story—role and time alone are too weak; busyness, co-activity, and workflow context are defensible additions. Cite as **core supporting**. citeturn28search0turn28search1

**Mining Tasks and Task Characteristics from Electronic Health Record Audit Logs with Unsupervised Machine Learning** — 2021, *JAMIA*.  
Problem: can raw audit logs be converted into meaningful task representations? Dataset: **33 neonatal intensive care unit nurses**, **57,234 sessions**, **81 tasks** from Vanderbilt NICU logs. Method: unsupervised learning on event sequences, with complexity metrics and process-mining validation. Evaluation: statistical comparison across task-complexity profiles, with expert-reviewed annotated workflows. Key finding: latent tasks and task complexity can be derived from audit logs, and performance-time differs significantly across task types. Limitation: workflow study, not security detection. Relation to your project: supports deriving **higher-level activity features** rather than using only raw event counts. Cite as **core supporting**. citeturn26search0turn26search1

**Team is Brain: Leveraging EHR Audit Log Data for New Insights into Acute Care Processes** — 2023, *JAMIA*.  
Problem: can team-level contextual factors from audit logs explain variation in acute-care process outcomes? Dataset: **3,052 acute ischemic stroke patients** who received tPA across **three Northern California health systems**. Method: Epic audit-log features for treatment-team busyness and prior shared team experience; multivariable analysis against door-to-needle time. Evaluation: outcome association modeling. Key finding: audit logs can measure contextual team factors at scale, and prior team experience is associated with better process outcomes. Limitation: not a security paper and not a ranking/triage study. Relation to your project: gives you a recent, credible justification for **team-experience and workload context features**. Cite as **core supporting**. citeturn27search3turn35search18

**Electronic Health Record Activity Changes Around New Decision Support Implementation: Monitoring Using Audit Logs and Topic Modeling** — 2025, *JAMIA Open*.  
Problem: how can one infer higher-level EHR activities from audit logs without hand-coding everything? Dataset: **3,445 encounters** around a new CDS intervention (**1,734 pre**, **1,711 post**). Method: topic modeling over audit-log events to infer activity patterns before and after CDS deployment. Evaluation: topic coherence and domain-expert labeling of activity topics. Key finding: latent-variable methods can transform micro-level audit events into interpretable higher-level activities. Limitation: not a security paper, and topics are still proxy constructs rather than ground-truth reasons for access. Relation to your project: strong support for **sequence/topic-derived features** and for adding a lightweight interpretability layer. Cite as **supporting**. citeturn36search0turn36search6

### Reproducibility, data modeling, and audit-log methodology papers

**Using Electronic Health Record Audit Log Data for Research: Insights from Early Efforts** — 2023, *JAMIA*.  
Problem: how should researchers think about audit-log data as a scientific data source? Dataset: not an empirical benchmark; perspective paper. Method: lessons learned from prior audit-log work. Evaluation: not applicable. Key finding: audit logs are rich, scalable signals of behavior and workflow, but multi-site progress needs transparent, validated, standardized measures. Limitation: no benchmark, no model, no security evaluation. Relation to your project: this is one of the best citations for why your paper should emphasize **reproducibility, explicit feature definitions, and benchmark construction**. Cite as **core supporting**. citeturn7search2turn7search3

**Guidance for Reporting Analyses of Metadata on Electronic Health Record Use** — 2024, *JAMIA*.  
Problem: metadata-based EHR studies suffer from weak standardization and inconsistent reporting. Dataset: none; guidance paper. Method: proposes reporting guidance covering common metadata types and aggregation into higher-level measures. Evaluation: not applicable. Key finding: reproducibility and clarity in metadata/audit-log research require structured reporting standards. Limitation: no security experiment or benchmark. Relation to your project: use this to justify a **clear feature dictionary**, log schema, and benchmark protocol section. Cite as **core supporting**. citeturn14search0turn14search2

**A Scalable and Extensible Logical Data Model of Electronic Health Record Audit Logs for Temporal Data Mining** — 2024, *JMIR Nursing*.  
Problem: raw audit logs are too messy for temporal ML unless modeled consistently. Dataset: conceptual/modeling paper rather than an empirical benchmark. Method: proposes the **RNteract** logical data model for nurse-EHR temporal interaction analysis. Evaluation: conceptual demonstration, not a detection benchmark. Key finding: audit-log ML benefits from normalized, extensible temporal schemas. Limitation: not a suspicious-access detection paper and not validated on a security task. Relation to your project: directly useful for how you structure **user, patient, encounter, event, session, and context tables** in your paper. Cite as **supporting**. citeturn15view0

### Reviews and surveys that help your framing

**Access Control Solutions in Electronic Health Record Systems: A Systematic Review** — 2024, *Informatics in Medicine Unlocked*.  
Problem: what kinds of access-control solutions exist in EHR systems? Dataset: systematic review of **20 qualified journal articles** under PRISMA. Method: grouped literature into identification, authentication, authorization, and accountability. Evaluation: review synthesis. Key finding: authorization dominates, accountability is sparse, and gaps remain in emergency access, patient consent, MFA, and accountability. Limitation: not anomaly-detection focused. Relation to your project: excellent for saying your work is **not another storage/access-control paper**; it lives in the underdeveloped **accountability/auditing** slice. Cite as **supporting**. citeturn4view1

**Reimagining Clinical AI: From Clickstreams to Clinical Insights with EHR Use Metadata** — 2025, *npj Health Systems*.  
Problem: argues that EHR use metadata, including audit logs, are underused for operational and clinical AI. Dataset: perspective paper, no single benchmark. Method: conceptual synthesis tying audit logs, event logs, and metadata to broader AI use cases. Key finding: EHR use metadata are growing as a rich behavioral signal, but current applications are fragmented. Limitation: broad perspective, not an insider-threat paper. Relation to your project: use it to justify that **behavioral metadata are a legitimate AI signal**, then pivot to security triage as the missing operational application. Cite as **supporting**. citeturn9view0turn27search15

**Emerging Anomaly Detection Techniques for Electronic Health Records: A Survey** — 2026, *Informatics in Biomedicine Unlocked*.  
Problem: survey of recent EHR anomaly-detection methods. Dataset: PRISMA-based review, not a benchmark paper. Method: reviews statistical, ML, DL, and hybrid approaches, and discusses challenges to implementation. Key finding: the field is moving toward ML/DL/hybrid models, but deployment remains hindered by data availability, low-frequency events, and practical implementation constraints. Limitation: broad EHR anomaly survey, not specifically EHR access-risk triage. Relation to your project: useful only as a **fresh survey citation**, not as a core technical baseline paper. Cite as **supporting**. citeturn4view3

### Synthetic data and benchmark-enabling papers

**A Multifaceted Benchmarking of Synthetic Electronic Health Record Generation Models** — 2022, *Nature Communications*.  
Problem: how should synthetic EHR generators be fairly evaluated? Dataset: synthetic-generation benchmarking using data from **two large academic medical centers**. Method: benchmark framework combining utility and privacy assessment across use cases. Evaluation: multifaceted utility/privacy metrics. Key finding: there is no universally best generator; privacy-utility tradeoffs are unavoidable and method choice is use-case dependent. Limitation: synthetic **clinical records**, not synthetic **audit logs**. Relation to your project: helps justify a **benchmarking mindset**, but you still need to build your own synthetic access-log generator. Cite as **supporting**. citeturn30search1turn30search7

**Synthea: An Approach, Method, and Software Mechanism for Generating Synthetic Patients and the Synthetic Electronic Health Care Record** — 2018, *JAMIA*.  
Problem: produce realistic but non-real synthetic EHRs for benchmarking and health-IT development. Dataset: openly generated synthetic patients simulating the **10 most frequent reasons for primary care encounters** and the **10 chronic conditions with highest morbidity** in the United States. Method: open-source synthetic patient population simulator. Evaluation: design and realism arguments rather than suspicious-access benchmarking. Limitation: no audit logs, no user-access behavior, no security labels. Relation to your project: best base layer for **patient/encounter generation**, but you still must generate the access logs yourself. Cite as **supporting**. citeturn31search1turn31search3turn31search6

### The attached blockchain paper

**EHR: Patient Electronic Health Records using Blockchain Security Framework** — 2023, *ICIDCA 2023*.  
Problem: proposes a blockchain-based EHR framework to improve secure and transparent access to records by authorized users. Available summaries emphasize blockchain-backed authorization, transparency, and a security framework for patient EHR access. Limitation: from the available abstract-level material, it is a **storage/integrity/access-control framework**, not an empirical audit-log anomaly-detection or risk-ranking paper; it does not appear to provide the kind of ML baseline, suspicious-access benchmark, or query-time triage evaluation your paper needs. Relation to your project: use it as **background contrast only**—it belongs in related work as “security architecture / tamper resistance / access authorization,” not as a core baseline. Cite as **background**. citeturn44search1turn44search2

## Comparison table

This table keeps only the papers that are most useful for your actual method design and experimental framing. Reviews and perspectives are used later for gap claims.

| Paper | Year | Dataset / source | Real vs synthetic | Features used | Model / method | Ranking / triage support? | Precision@k / workload metric? | Query-time prevention or post-hoc audit? | Reproducibility | Main limitation | Opportunity for your project |
|---|---:|---|---|---|---|---|---|---|---|---|---|
| Hedda et al. — auditing rules citeturn21search1turn22search1 | 2018 | 8M EHR accesses from one week in a large EHR system | Real, private | Rule flags, inferred clinical explanations | Rule evaluation and risk ranking | Partial | No | Post-hoc audit | Low | No ML baseline, private data, no budget-aware evaluation | Use as **rule-only** baseline |
| Context is Key citeturn28search0turn28search1 | 2021 | Stroke-care audit logs; exact size not exposed in accessible abstract | Real, private | Temporal, busyness, team/context | Exploratory feature analysis | No | No | Neither; context measurement study | Low | Not a security paper | Add context variables to security model |
| Mining Tasks… citeturn26search0turn26search1 | 2021 | 33 NICU nurses, 57,234 sessions, 81 tasks | Real, private | Event sequences, session structure | Unsupervised learning + process mining | No | No | Neither; workflow mining | Low | No suspicious-access labels | Learn higher-level task features |
| Predictive Access Control citeturn4view4 | 2022 | 4,000 patient files; 2,086 after preprocessing | Public clinical time series | Patient vitals, age, current/future criticality | LSTM + fuzzy context handlers + ABAC | No | No | **Query-time access decision** | Medium | About emergency authorization, not misuse | Use as contrast for pre-decision logic |
| Synthetic EHR benchmarking citeturn30search1turn30search7 | 2022 | Two large academic medical centers | Mixed real-to-synthetic benchmark | Clinical EHR variables | Utility/privacy benchmark framework | No | No | Neither | Medium | No audit logs or access-risk task | Borrow evaluation discipline for your synthetic benchmark |
| How to Cover Up… citeturn12view0turn10view0 | 2023 | 309,096 patients; 944,385 encounters; 11,591 users; 26,992,636 accesses | Real logs, simulated anomalies | Role, department, age, LOS, diagnosis, graph structure | GNN / graph autoencoder; adversarial evaluation | Partial score-based detection | No P@k or review metric | Post-hoc audit | Low–medium | Simulated malicious labels; no operational triage | Strongest recent security-near benchmark anchor |
| Team is Brain citeturn27search3turn35search18 | 2023 | 3,052 AIS patients across 3 health systems | Real, private | Team busyness, prior shared experience, time | Multivariable audit-log outcome modeling | No | No | Neither | Low | Not a security task | Add team-context features |
| RNteract citeturn15view0 | 2024 | Conceptual data model; no benchmark dataset | N/A | Temporal interaction entities, nurse/session/context/outcome schema | Logical data model for temporal mining | No | No | Neither | Medium | No suspicious-access experiment | Use as schema inspiration for log design |
| Topic modeling around CDS citeturn36search0turn36search6 | 2025 | 3,445 encounters around CDS implementation | Real, private | Event sequences, inferred topic/activity patterns | Topic modeling on audit events | Partial, but not security triage | No | Neither | Medium | Not a misuse-detection study | Add latent activity or topic features |
| Blockchain security framework citeturn44search1turn44search2 | 2023 | Framework/demo paper; no convincing benchmark exposed in accessible summaries | Unclear / demo-oriented | Authorization, blockchain integrity, access control | Blockchain framework | No | No | Query-time authorization perspective | Low | No audit-risk scoring or anomaly benchmark | Background contrast only |
| Your strongest target design | 2026 | Synthea-derived patients + synthetic access/query logs + optional local demo logs | Synthetic / reproducible | Role, time, user-patient relation, workflow, diagnosis, query/content keywords, note flags | RBAC + rules + ML hybrid risk ranking | **Yes** | **Yes** | **Query-time triage + post-hoc audit support** | **High if code/data released** | Needs careful benchmark design and honest claims | This is the non-workshop paper angle |

## Real gaps

These are not generic “more work is needed” gaps. They are the exact gaps that can become your contribution.

### Post-hoc audit dominates; query-time triage is still weak

The closest security-near recent paper explicitly states that illegitimate-access systems usually perform **post-hoc detection instead of runtime restriction** because healthcare needs broad emergency access. citeturn12view0 The 2022 predictive-access paper shows query-time access control is thinkable, but only in the narrow sense of patient criticality and emergency authorization, not suspicious-access triage. citeturn4view4 The 2024 systematic review also shows access-control literature is concentrated in authorization while accountability is comparatively thin. citeturn4view1

Why it matters: a paper that only says “we detect anomalies after access” is crowded and weak. A paper that says **“we triage access requests at query time under review constraints”** is much sharper.

Why you can address it quickly: you already have a rule engine, query logging, and UI. You only need to change the system output from **allow/block** to **risk score + reason + queue priority**.

### Recent papers rarely optimize for auditor workload

Hedda ranks rules by potential risk, which is closer to triage than most papers, but it still does not evaluate precision@k, recall@k, or review-budget tradeoffs. citeturn22search1 The 2023 adversarial-access paper evaluates detector quality with TPR/TNR/precision/AUC, not how many suspicious cases a compliance officer could catch under a fixed review budget. citeturn10view0 Recent audit-log workflow papers mine behavior and context, but not security queue prioritization. citeturn26search0turn27search3turn36search0

Why it matters: **budget-aware evaluation** is a better applied-conference contribution than trying to beat the literature on abstract anomaly detection.

Why you can address it quickly: add **precision@1%, precision@5%, recall@5%, and review workload reduction** to your evaluation and make them primary endpoints.

### Context signals are rich, but security papers underuse them

The recent audit-log literature shows that logs encode **busyness**, **team experience**, **tasks**, and **workflow topics**. citeturn28search1turn26search0turn27search3turn36search0 But recent security-near work is still dominated by roles, departments, diagnoses, graph structure, and hand-built rules. citeturn10view0turn22search1

Why it matters: this is the cleanest bridge between two currently separate literatures.

Why you can address it quickly: engineer a lightweight context layer using data you already can synthesize or log: **session time, recent patient-team contact, same-department frequency, encounter recency, shift alignment, burstiness, and user-patient novelty**.

### Reproducibility is weak because private logs and inconsistent measures dominate

The 2023 perspective on audit-log research and the 2024 reporting-guidance paper are basically warning labels for the whole area: definitions vary, validation is sparse, and standardized reporting is weak. citeturn7search2turn14search2 The 2024 RNteract paper exists because raw audit logs are too inconsistent for easy temporal ML. citeturn15view0 The 2025 perspective on EHR use metadata still frames the area as fragmented and underused. citeturn9view0

Why it matters: this is your best argument for a **reproducible benchmark paper**, not for “better ML” in the abstract.

Why you can address it quickly: publish a **synthetic benchmark generator**, explicit data dictionary, feature definitions, and evaluation recipe.

### Hybrid structured plus unstructured security signals are still rare

Recent audit-log papers infer tasks from event sequences and topics, and the broader metadata perspective pushes toward richer behavioral signals. citeturn26search0turn36search0turn9view0 But the recent security-near EHR access papers you can actually cite do **not** combine structured access patterns with **query text, note text, or note/query keywords** for risk triage. citeturn10view0turn22search1

Why it matters: this is a plausible, fast-added differentiator for your MongoDB/query-log side.

Why you can address it quickly: do **not** build a large NLP model. Add a defensible small feature set: sensitive-topic keyword flags, note-view-to-note-edit ratios, free-text search rarity, and suspicious query patterns.

### Access control and anomaly detection are still treated as separate systems

The 2024 systematic review shows authorization and accountability are often handled as different concerns. citeturn4view1 The 2022 predictive-access paper focuses on access decisions. citeturn4view4 The 2023 adversarial paper assumes a detector living beside permissive access. citeturn12view0 The blockchain paper lives in architecture/access-control space, not operational misuse detection. citeturn44search1turn44search2

Why it matters: combining **RBAC + rules + anomaly score + review prioritization** is more publishable than pretending any one layer is novel alone.

Why you can address it quickly: your implementation already spans these layers. The real work is to simplify the claim and evaluate the stack properly.

## My project versus the literature

Bluntly: if you write the current system as “a secure EHR system using Azure SQL, MongoDB, Streamlit, logging, rules, and ML,” it will read like a class project and probably lose.

What is **not** novel anymore:
- EHR audit logging.
- Role-aware access control.
- Rule-based suspicious-access flags.
- “We use ML for anomaly detection.”
- “We built a secure healthcare database.”
- Blockchain-backed EHR security frameworks. citeturn4view1turn12view0turn44search1turn44search2

What can still be novel enough:
- **A reproducible benchmark** for suspicious EHR access / privacy-risky queries.
- **Head-to-head comparison** of RBAC-only, rule-only, ML-only, and hybrid systems under the **same benchmark**.
- **Risk ranking under constrained review budgets**, using precision@k and workload reduction rather than generic accuracy.
- Modest but defensible use of **context + temporal + lightweight text/query signals** in a deployable pipeline. citeturn22search1turn10view0turn28search1turn26search0turn36search0

What you already have that helps:
- A real implementation, not just a model.
- Multiple data modalities: structured patient data + unstructured notes/query logs.
- A rule layer already in place.
- A UI, which matters for an applied venue if used only as a small demo figure, not as the main story.

Where you are weak right now:
- No clear **benchmark**.
- No fully specified **labels / risk injection protocol**.
- No standard **baseline suite**.
- No primary evaluation on **review-budget metrics**.
- ML is “being added,” which means as of now the key contribution is still incomplete.
- Likely no external validation and no real hospital audit-log ground truth.

What you must add to stop looking like a course project:
- A **single crisp problem**: query-time or near-query-time risk triage under reviewer budget constraints.
- A clean benchmark with explicit event-generation logic and labels.
- A baseline table with **RBAC-only / rules-only / ML-only / hybrid**.
- An ablation table.
- A short but honest threat model and limitation section.
- Reason codes or explainability outputs for reviewer actionability.

Is a full non-workshop conference paper realistic?  
Yes, **for the right tier and only with the right framing**. The best target is an applied informatics conference like **IEEE BHI 2026**, not a journal and not a top security conference. If you keep the contribution narrow and the benchmark clean, it is realistic. If you overclaim generalizable insider-threat detection from synthetic labels, it is not. citeturn40view0turn41search0

## Best paper directions

### Query-time EHR access-risk triage under constrained audit budgets

**Best title idea:**  
*Hybrid Query-Time Risk Triage for Suspicious EHR Access Under Constrained Audit Budgets*

**Research question:**  
Can a lightweight hybrid system combining RBAC, rule-based checks, and ML-based anomaly scoring improve **precision@k**, **recall@k**, and **review workload reduction** over RBAC-only, rule-only, and ML-only approaches?

**Exact contribution:**  
A reproducible benchmark plus a deployable hybrid risk-ranking pipeline for EHR access/query events.

**What you already have:**  
RBAC/rule engine, storage stack, logging, UI, partial ML infrastructure.

**What you need to add:**  
Temporal/context features, note/query keyword flags, ranking output, benchmark generator, baseline suite, reviewer-budget evaluation.

**Required experiments:**  
RBAC-only vs rule-only vs ML-only vs hybrid; p@k and workload reduction as primary metrics; ablations removing temporal, context, and text/query features.

**Baselines required:**  
Exactly those four. Optional fifth baseline for cohort-style privacy rules only.

**Main risk:**  
If your labels are synthetic and too easy, reviewers will see it immediately. You must inject **plausible ambiguous cases**, not cartoon attacks.

**Expected strength:**  
This is your **strongest non-workshop direction**.

### Reproducible synthetic benchmark for EHR access-risk detection and audit prioritization

**Best title idea:**  
*A Reproducible Synthetic Benchmark for EHR Access-Risk Detection and Audit Prioritization*

**Research question:**  
Can a synthetic but realistic benchmark support fair comparison of EHR access-risk triage methods when real audit logs are inaccessible?

**Exact contribution:**  
Synthetic patient records + synthetic access/query logs + labeled risk scenarios + evaluation protocol.

**What you already have:**  
The application stack and the ability to emit/access query logs.

**What you need to add:**  
A formal scenario generator, role roster, encounter templates, and benchmark release package.

**Required experiments:**  
Demonstrate benchmark realism, then compare the four baselines on it.

**Baselines required:**  
Same as above.

**Main risk:**  
If the benchmark becomes the whole paper, reviewers may ask why the method is simple. The fix is to present the benchmark and a **useful hybrid triage pipeline together**.

**Expected strength:**  
Good, but only if benchmark design is rigorous and transparent.

### From storage security to operational risk triage

**Best title idea:**  
*From EHR Access Control to Operational Risk Triage: A Lightweight Hybrid Framework for Suspicious Access Review*

**Research question:**  
What is gained by integrating access control, rule-based safeguards, and anomaly scoring in one operational auditing pipeline?

**Exact contribution:**  
A system paper with a narrower empirical story: instead of “novel ML,” the novelty is the integrated and explainable workflow for compliance review.

**What you already have:**  
Most of the system integration.

**What you need to add:**  
Strong actionability outputs: reasons, reviewer queue, and a few case studies.

**Required experiments:**  
Throughput/latency, baseline ranking quality, and reviewer-facing case examples.

**Baselines required:**  
RBAC, rules, ML, hybrid.

**Main risk:**  
If you lean too much into engineering, reviewers may ask where the science is.

**Expected strength:**  
Decent, but weaker than the first direction unless the evaluation is very crisp.

How the blockchain paper fits: it belongs **here only as related-work contrast**. It shows the difference between **architecture-centered security** (authorization, integrity, tamper resistance) and **operational misuse triage**, which is your actual topic. It should not be a core baseline. citeturn44search1turn44search2

## One-month roadmap

The calendar argument is simple: as of April 27, 2026, **IEEE BHI 2026 opens submissions on May 1 and the regular-paper round-1 deadline is June 12, 2026**. That gives you slightly more than six weeks, but you should behave as if you have **four hard weeks** and a short buffer for polish. citeturn40view0

### Week one

Lock the problem statement. It should become:

> We study **risk triage of suspicious EHR access/query events under limited reviewer capacity**, not generic HIPAA compliance, not generic secure storage, and not pure unsupervised anomaly detection.

At the same time, freeze the evaluation design:
- unit of analysis = a single access or query event;
- output = risk score and reason codes;
- primary metrics = precision@k, recall@k, workload reduction, PR-AUC;
- baselines = RBAC-only, rule-only, ML-only, hybrid.

Implementation tasks for the week:
- finalize event schema;
- add temporal/context features;
- add keyword-based text/query features;
- define risk scenarios and labels;
- choose one supervised model and one unsupervised model.

Best practical ML choice: **XGBoost or logistic regression** for labeled experiments, and **Isolation Forest** for unsupervised comparison. Do not use a fancy deep model unless you already have it stable. Your paper does not need “stronger AI”; it needs a cleaner experiment.

### Week two

Build the benchmark and run all baselines.

Use Synthea or equivalent synthetic patient generation for encounter/patient realism, then generate access logs from role and workflow templates. citeturn31search1turn31search6

Create the risky scenarios:
- curiosity access to a high-profile patient,
- cross-department “just browsing,”
- family/coworker access without clinical relation,
- after-hours repeated access,
- bursty access to many patients,
- rare or sensitive-topic note/query access,
- access after care relationship ended,
- role-context mismatch.

Then run:
- RBAC-only,
- rule-only,
- ML-only,
- hybrid.

If time remains, add:
- optional k-anonymity/cohort-query threshold baseline only for aggregate/query scenarios,
- calibration or latency measurement.

### Week three

Write with the results already fixed.

Produce four figures only:
- pipeline diagram,
- benchmark generation diagram,
- main baseline result table,
- review-budget curve or precision@k curve.

Produce two tables only:
- baseline comparison,
- ablation study.

Write the limitation section early:
- synthetic labels,
- no real hospital compliance adjudication,
- benchmark scenarios encode assumptions,
- claims limited to triage and audit support, not definitive prevention.

### Week four

Polish and submission prep.

Tighten the abstract and title around one contribution only. Remove every sentence about:
- “HIPAA-compliant architecture,”
- Azure/MongoDB technology novelty,
- generic blockchain security,
- broad claims of real-world deployment or hospital-scale generalizability.

If targeting **BHI**, spend the remaining buffer after week four on:
- language cleanup,
- figure quality,
- latent bugs in the experimental code,
- formatting for the double-blind review process. citeturn40view0

## Experiments and metrics

### Synthetic dataset generation strategy

If you do not have real adjudicated audit logs, the cleanest path is:

1. Generate synthetic patients and encounters with **Synthea**. citeturn31search1turn31search6  
2. Add synthetic staff users: physicians, nurses, residents, pharmacists, registrars, billing staff, compliance staff.  
3. Build care pathways and role-to-encounter relations using encounter type, department, and shift logic.  
4. Emit access/query events with timestamps, user, role, department, patient, encounter, note type, query type, and free-text keyword tags.  
5. Inject labeled suspicious events into otherwise plausible workflows.

This gives you structured patient/encounter realism without needing real PHI, while keeping the access-risk benchmark reproducible.

### Normal-behavior generation

Normal accesses should come from templates, not random sampling:
- ED users access ED patients during a limited visit window.
- Inpatient nurses repeatedly access assigned units and nearby shifts.
- Pharmacists access medication-relevant encounters.
- Billing staff access post-discharge administrative fields but not sensitive notes.
- Specialists access patients after consult/order/referral relations are generated.

The normal generator should include ambiguity:
- cross-covering clinician,
- float nurse,
- off-service resident,
- night-shift access,
- co-managed patient.

If you do not include ambiguity, the benchmark will be too easy and your hybrid will look artificially good.

### Risky scenario injection

Use at least these categories:
- **relationship mismatch**: no treatment/team/admin relation;
- **role mismatch**: user accesses data inconsistent with usual role;
- **temporal anomaly**: unusual time, unusual burst, too many patients in short time;
- **post-relationship access**: repeated viewing after discharge or handoff end;
- **sensitive-topic browsing**: flagged note/query keywords;
- **multi-patient sweep**: many patients with no coherent workflow;
- **celebrity or high-interest patient**: concentrated curiosity access.

Make labels binary for the main experiment, but store a finer **risk tier** label internally so you can later evaluate ranking quality more meaningfully.

### Train, validation, and test split

Use a **temporal split**, not random row splitting:
- train on earlier weeks,
- validate on the next week,
- test on later weeks.

If possible, also run a second test split with partially held-out users or departments to show the hybrid is not just memorizing identities.

### Baselines

The baseline suite should be exactly:

- **RBAC-only**  
  Allow or flag based on role-permission mismatch only.

- **Rule-only**  
  Hand-coded risk rules: after-hours, sensitive-topic access, no encounter relation, mass access, etc.

- **ML-only**  
  Either supervised classifier over labeled benchmark events or unsupervised anomaly detector over mostly normal data.

- **Hybrid**  
  Combined score from RBAC, rules, and ML, ideally with explicit reason codes.

- **Optional k-anonymity threshold**  
  Only if you include aggregate or cohort-style queries. If your task is event-level chart access, do not force this baseline.

### Primary metrics

Make these primary:
- **PR-AUC** because the class imbalance will be severe;
- **precision@1%, precision@5%, precision@10%**;
- **recall@1%, recall@5%, recall@10%**;
- **review workload reduction** at a fixed target recall;
- **F1** for a thresholded operating point.

Keep ROC-AUC, but do not make it the headline. A reviewer can dismiss a paper that is all ROC-AUC and no budget-aware metric.

### Ablations

At minimum:
- hybrid without temporal features,
- hybrid without role/context features,
- hybrid without note/query keyword features,
- hybrid without rule layer.

If you use a supervised model, also show feature importance or SHAP-style explanation examples for 3–5 representative flagged events.

### What result is strong enough

For a full applied conference paper, the hybrid should show something operationally meaningful, not just statistically nonzero.

A paper-shaped result would look like this:
- at a **5% review budget**, hybrid captures substantially more true risky events than rule-only and ML-only;
- hybrid improves **precision@k by ~10–15 points** over the best single-layer baseline;
- or hybrid delivers **25%–40% review workload reduction** at matched recall;
- plus ablations show context and query/text features actually matter.

If your gains are tiny, the paper becomes narrative-only and weak.

## Venue targets and final recommendation

### Best immediate target

**IEEE BHI 2026** is the best immediate non-workshop target. It is explicitly centered on biomedical and health informatics, includes themes such as AI implementation, multimodal data fusion, explainable AI, and clinical translation, and uses a two-round double-blind review process. The 2026 call shows the submission system opens **May 1, 2026**, the regular-paper round-1 deadline is **June 12, 2026**, rebuttal/revision is due **September 11, 2026**, and final notification is **September 25, 2026**. Fit is strong because your strongest story is a **lightweight, clinically deployable informatics triage pipeline**, not pure cybersecurity theory. Risk level: **moderate to high**, but realistic. citeturn40view0

### Good venues, but not for this exact one-month sprint

**AMIA Annual Symposium 2026** is a good fit for applied informatics, but the manuscript submission deadline for 2026 was **March 10, 2026**, so it is already closed for the current cycle. It remains a good next-cycle option if BHI is missed or rejected. Risk: moderate. citeturn41search0turn41search3

**ACM-BCB 2026** is a real full-paper venue with health informatics scope, but its 2026 regular-paper abstract and full-paper deadlines were **March 1** and **March 8, 2026**, respectively, so it is also closed for this cycle. It is more method-heavy and somewhat less ideal for a compliance-triage story than BHI. Risk: moderate-high. citeturn37search2turn37search6

**IEEE ICHI 2026** is a legitimate healthcare informatics conference and a reasonable fit in principle, but its 2026 submission cycle is already over as well. It is not your fastest path now. Risk: moderate. citeturn43search2turn43search5turn43search6

**IEEE BIBM** is broader biomedical informatics and can take health-informatics papers, but it is less naturally aligned with reviewer concerns around operational auditing and clinical deployment. For 2026, the conference dates are posted, but the full-paper deadline was not yet visible in the source I checked; the 2025 full-paper deadline was **August 3, 2025**, which suggests a later annual schedule than BHI. Treat it as a watchlist venue, not the primary plan. citeturn42search0turn42search1

### Final recommendation

The fastest credible non-workshop submission path is:

- **Target IEEE BHI 2026.**
- **Do not** write the paper as a secure database, HIPAA, or blockchain paper.
- **Do not** claim novel anomaly detection in general.
- **Do** write it as a **reproducible hybrid risk-triage benchmark and pipeline for suspicious EHR access/query events under constrained review budgets**.

What to implement:
- benchmark generator,
- four baselines,
- context + temporal + keyword features,
- risk ranking,
- review-budget metrics,
- ablations,
- reviewer reason codes.

What to remove:
- most architecture detail beyond one paragraph,
- blockchain from core contribution,
- database technology as a novelty claim,
- generic discussion of HIPAA compliance.

What to stop talking about:
- “our system is HIPAA compliant,”
- “we prevent insider threats,”
- “we built a secure EHR platform,”
- “we use blockchain for security” as if it helps your anomaly paper.

What story to tell:
- hospitals log everything but cannot review everything;
- existing work separates access control, audit rules, and behavioral analytics;
- recent audit-log studies show rich context is extractable, but recent security studies still evaluate mostly post-hoc detection;
- your contribution is a **reproducible benchmark and hybrid triage system** that improves **who gets reviewed first**.

Minimum result table before you start writing:
- rows: RBAC-only, Rule-only, ML-only, Hybrid;
- columns: PR-AUC, F1, Precision@1%, Recall@1%, Precision@5%, Recall@5%, Workload reduction at target recall;
- plus one ablation table.

If you can produce that table cleanly, with honest synthetic-label limitations and a focused story, you have a real shot at a non-workshop applied conference paper. If you cannot produce that table, do not write yet.