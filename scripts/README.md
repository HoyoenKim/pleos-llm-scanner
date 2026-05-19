# scripts/

Operational helpers and one-off research measurement scripts. Keep reusable
pipeline logic in `src/`; keep orchestration, data collection, and packaging here.

| Path | What Goes Here |
|---|---|
| `apk/` | APK extraction and JADX wrappers |
| `research/` | RQ measurement, corpus expansion, native inventory, RAG packaging |
| `runtime_poc/` | Runtime PoC harness build and evidence recording helpers |
| `presentation/` | Local deck/video helpers. Generated PPT/PDF stays ignored |
| `maintenance/` | Masking, report repair, and result-maintenance utilities |

Scripts assume they are run from the repository root unless their own help text
states otherwise.
