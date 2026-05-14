# R2.c Codex multi-model cross-read

_Generated: 2026-05-14T14:26:46+09:00 / scope: `full47`_

## Bottom line

**multi-model 자체보다 prompt calibration과 evidence packaging이 더 중요함**.

The Claude Code baseline is preserved as a single-model multi-perspective result. This artifact adds a separate Codex 3-model cross-read layer and compares both against the same GT labels.

## Metrics

| System | TP | FP | TN | FN | Precision | Recall | F1 | Report rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Code consensus (>=2/3) | 37 | 0 | 9 | 1 | 1.000 | 0.974 | 0.987 | 78.7% |
| Codex gpt-5.3-codex | 25 | 0 | 9 | 13 | 1.000 | 0.658 | 0.794 | 53.2% |
| Codex gpt-5.4 | 28 | 0 | 9 | 10 | 1.000 | 0.737 | 0.849 | 59.6% |
| Codex gpt-5.5 | 34 | 0 | 9 | 4 | 1.000 | 0.895 | 0.944 | 72.3% |
| Codex 2/3 consensus | 29 | 0 | 9 | 9 | 1.000 | 0.763 | 0.866 | 61.7% |

## Claude vs Codex agreement

| Pair | Agreement | Cohen's kappa |
|---|---:|---:|
| claude_vs_codex_consensus | 39 (83.0%) | 0.607 |
| claude_vs_gpt-5.5 | 44 (93.6%) | 0.828 |
| claude_vs_gpt-5.4 | 38 (80.9%) | 0.570 |
| claude_vs_gpt-5.3-codex | 35 (74.5%) | 0.470 |

## Codex vote distribution

| Codex report votes | Findings |
|---:|---:|
| 0/3 | 13 |
| 1/3 | 5 |
| 2/3 | 5 |
| 3/3 | 24 |

## Discordance buckets

| Bucket | IDs |
|---|---|
| codex_suppressed_claude_fp | - |
| codex_recovered_claude_fn | - |
| codex_promoted_claude_filtered_fp | - |
| both_missed_gt_tp | vc-7 |
| both_reported_fp | - |
| codex_model_disagreement | ssl-3, ssl-5, ib2-8, ib2-9, usb-1, acc-1, acc-4, acc-5, amb-2, amb-3 |

## Per-finding table

| ID | APK | GT real | Claude report | Codex votes | Codex report |
|---|---|---:|---:|---:|---:|
| vc-1 | ai.umos.vehiclecontrol | False | False | 0/3 | False |
| vc-2 | ai.umos.vehiclecontrol | False | False | 0/3 | False |
| vc-3 | ai.umos.vehiclecontrol | False | False | 0/3 | False |
| vc-4 | ai.umos.vehiclecontrol | False | False | 0/3 | False |
| vc-5 | ai.umos.vehiclecontrol | True | True | 3/3 | True |
| vc-6 | ai.umos.vehiclecontrol | True | True | 3/3 | True |
| vc-7 | ai.umos.vehiclecontrol | True | False | 0/3 | False |
| ssl-1 | ai.pleos.sync.syslog | True | True | 3/3 | True |
| ssl-2 | ai.pleos.sync.syslog | True | True | 3/3 | True |
| ssl-3 | ai.pleos.sync.syslog | True | True | 1/3 | False |
| lmp-1 | ai.pleos.llm.model.provider | True | True | 3/3 | True |
| lmp-2 | ai.pleos.llm.model.provider | True | True | 3/3 | True |
| ssl-4 | ai.pleos.sync.syslog | True | True | 0/3 | False |
| ssl-5 | ai.pleos.sync.syslog | True | True | 2/3 | True |
| ssl-6 | ai.pleos.sync.syslog | True | True | 3/3 | True |
| ucl1-1 | UnCrackable-Level1 | True | True | 3/3 | True |
| ucl1-2 | UnCrackable-Level1 | True | True | 3/3 | True |
| ucl1-3 | UnCrackable-Level1 | True | True | 0/3 | False |
| ucl3-1 | UnCrackable-Level3 | True | True | 3/3 | True |
| ib2-1 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-2 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-3 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-4 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-5 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-6 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-7 | InsecureBankv2 | True | True | 3/3 | True |
| ib2-8 | InsecureBankv2 | True | True | 2/3 | True |
| ib2-9 | InsecureBankv2 | True | True | 2/3 | True |
| usb-1 | android.car.usb.handler | True | True | 2/3 | True |
| usb-2 | android.car.usb.handler | False | False | 0/3 | False |
| usb-3 | android.car.usb.handler | True | True | 3/3 | True |
| ss-1 | com.android.statementservice | False | False | 0/3 | False |
| acc-1 | ai.pleos.playground.account | True | True | 1/3 | False |
| acc-2 | ai.pleos.playground.account | True | True | 0/3 | False |
| acc-3 | ai.pleos.playground.account | True | True | 3/3 | True |
| acc-4 | ai.pleos.playground.account | True | True | 1/3 | False |
| acc-5 | ai.pleos.playground.account | True | True | 1/3 | False |
| am-1 | ai.umos.appmarket | True | True | 3/3 | True |
| am-2 | ai.umos.appmarket | True | True | 3/3 | True |
| am-3 | ai.umos.appmarket | True | True | 3/3 | True |
| am-4 | ai.umos.appmarket | False | False | 0/3 | False |
| amb-1 | ai.umos.ambientai | True | True | 3/3 | True |
| amb-2 | ai.umos.ambientai | True | True | 2/3 | True |
| amb-3 | ai.umos.ambientai | True | True | 1/3 | False |
| amb-4 | ai.umos.ambientai | False | False | 0/3 | False |
| amb-5 | ai.umos.ambientai | False | False | 0/3 | False |
| map-1 | ai.umos.maps.android.navigation.app | True | True | 3/3 | True |
