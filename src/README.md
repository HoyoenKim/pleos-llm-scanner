# src/

Deterministic code only. LLM analysis itself happens in Codex/Claude Code
sessions using the prompt files in `configs/prompts/`.

| Path | Role |
|---|---|
| `evaluation/` | Precision/recall/F1, bootstrap CI, stage ablation |
| `deobf/` | Obfuscation entropy and identifier-score measurement |
| `mapping/` | AAOS/MASVS mapping and TARA artifact generation |
| `rag/` | Local Chroma index, retrieval, and RAG ablation helpers |
| `dynamic/` | Deterministic static-to-dynamic state machine and Frida hooks |
| `native/` | Native `.so` string/pattern scanner |
| `viz/` | Chart generation |

Expected invocation is from the repository root, for example:

```bash
python src/evaluation/eval.py --labels data/ground_truth/combined_labels.json --reports 'data/reports/**/*.json'
python src/mapping/aaos_map.py
python src/viz/plot_metrics.py
```
