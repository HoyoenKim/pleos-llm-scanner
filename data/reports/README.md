# data/reports/

Report outputs are grouped by disclosure level.

| Path | Tracked? | Role |
|---|---|---|
| `aggregate/` | yes | Public-safe aggregate measurements and tables |
| `external/` | yes | Reports for public vulnerable corpora |
| `public/` | yes | Masked PleOS public copies |
| `local/` | no | Full local-only stage outputs such as unmasked Stage 3 |
| `per_apk_local/` | no | Unmasked per-APK PleOS reports |
| `runtime_local/` | no | Runtime PoC summaries and raw-adjacent report outputs |
| `native_local/` | no | Native deep-dive outputs and raw summaries |
| `rag_local/` | no | RAG ablation and model-judgment packages |

Use `aggregate/` and `public/` for presentation/report citations unless a
specific local-only evidence review has been completed.
