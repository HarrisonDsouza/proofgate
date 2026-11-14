# Tools, plugins, libraries: what we used, what to install, what to skip

> **Team note (combined plan):** where this file differs from `project-docs/COMBINED-PLAN.md`, the combined plan wins (roles, UI stack, timeline, tools, ElevenLabs). Simulated figures in this file are not results; never quote them.

## Used to build this repo and its data (today)
| Tool | What it did |
|---|---|
| Web search + page fetch | KFF, ProPublica and Becker's figures; MongoDB, Voyage and ElevenLabs docs; plugin repos |
| GitHub API (from Sukhman's Mac, since cms.gov / kff.org are blocked) | Found public mirrors of the CMS ICD-10-CM and HCPCS code files |
| curl on the Mac bridge | Downloaded the code files into `~/Documents/shiftline-hackathon/proofgate-data/raw/` |
| pandas | Parsed the fixed-width CMS order file, cleaned HCPCS, built specialty subsets |
| numpy, scipy | CUSUM simulation, Learn Then Test binomial p-values, Wilson/McNemar/bootstrap |
| pytest + Hypothesis | Property tests for G1–G8 and dwell crediting |
| ruff | Lint |
| FastAPI, PyMongo | The single-process service |
| prometheus-client, LangSmith wrapper | Observability |

Tried and blocked (so not used): direct downloads from cms.gov, data.cms.gov, kff.org, the NLM Clinical Tables API,
Docker (no daemon for a local MongoDB test). Apify (on the Mac) could fetch blocked pages via its cloud browser, but
it costs credits and the cited figures were already confirmed by fetch.

## Install for the build (in this order)
| Tool | Use | Verdict |
|---|---|---|
| **MongoDB Agent Skills** | Claude Code learns MongoDB best practice | Install first |
| **MongoDB MCP Server** (`--readOnly`) | Inspect the sandbox: counts, indexes, explain | Install first |
| **ponytail** ([DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) | Coding agent writes less code | Every build session |
| **hallmark** ([Nutlope/hallmark](https://github.com/Nutlope/hallmark)) | Non-generic UI direction | Start of the Angular build |
| **impeccable** ([pbakaus/impeccable](https://github.com/pbakaus/impeccable)) | Audit and polish each screen | Before the freeze |
| ui-ux-pro-max ([nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)) | Palette and type in minutes | Optional |
| graphify ([Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)) | Repo knowledge graph | Optional, after 14:00 |
| last30days ([mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)) | One run on "prior authorization AI denials" + one on "human in the loop rubber stamp" | Pitch talking points only |
| Scrapling ([D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling)) | Public pages our fetch can't reach | Low priority |
| Onyx | Whole AI search platform | Skip |
| ElevenLabs | PRD's spoken attestation (C4) is decoration | Skip |
| Voyage AI | Only for S7 clause vector search | Only if S7 is reached |

Install each from its own README; verify licences before copying code.
