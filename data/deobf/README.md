# data/deobf/ — Obfuscation entropy measurements

Output of `src/deobf/entropy.py` (Shannon entropy + jadx pattern matching) on 7 APKs. Each APK has a JSON file with full per-class scores; the summary table below is the sum-up.

## Summary across corpora

| APK | Origin | Non-framework classes | HIGH (≥ 0.7) | HIGH ratio | Mean composite | Mean jadx_obf_ratio |
|---|---|---:|---:|---:|---:|---:|
| UnCrackable-Level1 | MASTG (hand-crafted) | 6 | 3 | **50.0%** | 0.618 | 0.695 |
| UnCrackable-Level2 | MASTG (hand-crafted) | 5 | 2 | 40.0% | 0.529 | 0.507 |
| **NewPipe v0.27.6** | **real-world OSS** | **2,520** | **42** | **1.7%** | 0.120 | 0.080 |
| UnCrackable-Level3 | MASTG (hand-crafted) | 7 | 0 | 0.0% | 0.114 | 0.000 |
| r2pay-v1.0 | MASTG (hand-crafted) | 2 | 0 | 0.0% | 0.246 | 0.150 |
| SyncSyslog | PleOS | 4,555 | 18 | 0.4% | 0.053 | 0.015 |
| VehicleControl | PleOS | 2,704 | 6 | 0.2% | 0.051 | 0.003 |
| LLMModelProvider | PleOS | 112 | 0 | 0.0% | 0.034 | 0.010 |

### Corpus-level finding (R4 첫 측정 추가, 2026-05-08)

- **MASTG hand-crafted Crackmes** (UnCrackable-Level1 / Level2): high obfuscation density (40~50% HIGH) — Stage 0 LLM rename 의 upper-bound 측정용 (n=17, exact 100%).
- **NewPipe (real-world OSS, ProGuard 활성)**: HIGH 1.7% — hand-crafted MASTG 와 PleOS 사이의 **real-world baseline**. R4 의 첫 정량 데이터.
- **PleOS APKs**: HIGH 0.2~0.4% — semantic 클래스명 유지. 초기 계획서가 가정한 heavy obfuscation 시나리오와 정량적으로 다름.

→ 최종 Stage 0 정확도 해석은 hand-crafted MASTG 100%를 upper-bound로, NewPipe semantic plausibility를 real-world floor로 분리한다. ProGuard mapping 기반 exact accuracy 측정은 별도 확장 과제로 남긴다.

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
for d in UnCrackable-Level1 UnCrackable-Level2 UnCrackable-Level3 r2pay-v1.0 \
         VehicleControl SyncSyslog LLMModelProvider NewPipe; do
  python src/deobf/entropy.py "data/_local/decompiled/$d" \
      --out "data/deobf/${d}.json" \
      --md  "data/deobf/${d}.md" \
      --top 15
done
```
