# data/deobf/ — Obfuscation entropy measurements

Output of `src/deobf/entropy.py` (Shannon entropy + jadx pattern matching) on 7 APKs. Each APK has a JSON file with full per-class scores; the summary table below is the sum-up.

## Summary across corpora

| APK | Origin | Non-framework classes | HIGH (≥ 0.7) | HIGH ratio | Mean composite | Mean jadx_obf_ratio |
|---|---|---:|---:|---:|---:|---:|
| UnCrackable-Level1 | MASTG | 6 | 3 | **50.0%** | 0.618 | 0.695 |
| UnCrackable-Level2 | MASTG | 5 | 2 | 40.0% | 0.529 | 0.507 |
| UnCrackable-Level3 | MASTG | 7 | 0 | 0.0% | 0.114 | 0.000 |
| r2pay-v1.0 | MASTG | 2 | 0 | 0.0% | 0.246 | 0.150 |
| VehicleControl | PleOS | 2,704 | 6 | 0.2% | 0.051 | 0.003 |
| SyncSyslog | PleOS | 4,555 | 18 | 0.4% | 0.053 | 0.015 |
| LLMModelProvider | PleOS | 112 | 0 | 0.0% | 0.034 | 0.010 |

### Corpus-level finding

- **MASTG hand-crafted Crackmes** (UnCrackable-Level1 / Level2): high obfuscation density (40~50% HIGH) — used for upper-bound deobfuscation accuracy measurement (n=17, exact 100%).
- **PleOS APKs**: HIGH ratio 0.2~0.4% — semantically meaningful class names retained. The original PPT plan assumed heavy obfuscation; the measurement contradicts that assumption.

## Files

| File | Content |
|---|---|
| `<APK>.json` | Full per-class entropy + scores. Source of truth (deterministic, machine-readable). |
| `UnCrackable-Level1_renames.json` | LLM rename results — 4 classes / 7 methods (Stage 0). |
| `UnCrackable-Level2_renames.json` | LLM rename results — 2 classes / 4 methods (Stage 0). |
| `UnCrackable-Level1_renames_groundtruth.json` | Manual ground-truth labels for Stage 0 accuracy measurement (n=17). |

(The `<APK>.md` per-APK summaries that `entropy.py` produces are gitignored — they duplicate the JSON. Use `python src/deobf/entropy.py` to regenerate them locally.)

## Reproduce

```bash
for d in UnCrackable-Level1 UnCrackable-Level2 UnCrackable-Level3 r2pay-v1.0 VehicleControl SyncSyslog LLMModelProvider; do
  python src/deobf/entropy.py "data/decompiled/$d" \
      --out "data/deobf/${d}.json" \
      --md  "data/deobf/${d}.md" \
      --top 15
done
```
