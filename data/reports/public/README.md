# data/reports/public/ — Masked public copies

본 디렉토리는 PleOS 자체 APK 의 per-APK 보고서 + Stage 3 ensemble 결과의 **마스킹 공개판**이다.
코드 인용 (evidence / fenced code block) 만 `<redacted: PleOS proprietary code>` 로 대체했고,
분석 메타데이터 (class FQCN, line, category, severity, rationale, AAOS / MASVS 매핑, attack chain,
missing control, vehicle asset, STRIDE, TARA impact 등) 는 그대로 유지된다.

- Original raw 보고서는 contractor IP 보호 정책에 따라 작성자 로컬에만 보관 (`data/reports/*.{json,md}`, gitignored).
- 본 public 사본은 `scripts/maintenance/mask_pleos_evidence.py` 로 결정론적 생성. 재실행 시 동일 결과.
- MASTG 외부 corpus 부분 (UnCrackable-Level1/3, r2pay) 은 공개 corpus 라 redact 없이 그대로 (Stage 3 ensemble 안 ucl1- / ucl3- 항목).

## 파일

- [`ai.umos.vehiclecontrol.md`](ai.umos.vehiclecontrol.md) + [`.json`](ai.umos.vehiclecontrol.json)
- [`ai.pleos.sync.syslog.md`](ai.pleos.sync.syslog.md) + [`.json`](ai.pleos.sync.syslog.json)
- [`ai.pleos.llm.model.provider.md`](ai.pleos.llm.model.provider.md) + [`.json`](ai.pleos.llm.model.provider.json)
- [`stage3_ensemble.md`](stage3_ensemble.md) + [`.json`](stage3_ensemble.json) — 공개판은 2026-04-29 초기 n=12 redacted snapshot. 현재 full n=47 Stage 3 결과는 `data/reports/local/stage3_ensemble.md/json` 로컬 전용본에 보관하며, R1.d.2~d.5 신규 corpus 공개는 별도 redaction review 후 진행.

## 재현

```bash
python scripts/maintenance/mask_pleos_evidence.py
```
