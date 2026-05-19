# Random-sample selection-bias baseline

_Measured: 2026-06-07 / random pool: 204 APKs (PleOS 207 minus 3 security-picked) / seed: 42_

## 본 학기 보안 가치 기반 PleOS 3 APK

| APK | Java files | Priority class | Priority % | Native lib |
|---|---:|---:|---:|---:|
| `ai.umos.vehiclecontrol` | 7,211 | **455** | 6.31% | 1 |
| `ai.pleos.sync.syslog` | 9,568 | **729** | 7.62% | 4 |
| `ai.pleos.llm.model.provider` | 3,463 | **89** | 2.57% | 0 |

## 무작위 3 APK (시드 42)

| APK | Java files | Priority class | Priority % | Native lib |
|---|---:|---:|---:|---:|
| `com.android.statementservice` | 879 | 39 | 4.44% | 0 |
| `android.car.usb.handler` | 14 | 6 | 42.86% | 0 |
| `ai.pleos.playground.vehiclebridge.servicemeta` | 1 | 0 | 0.0% | 0 |

## 비교 요약

| 측정 | 보안 가치 큰 3 APK 평균 | 무작위 3 APK 평균 | 비율 |
|---|---:|---:|---:|
| Priority class count | **424.33** | 15.0 | 28.29× |
| Priority class ratio | 5.5% | 15.77% | — |
| Native lib count | 1.67 | 0.0 | — |

## Selection bias 해석

- 보안 가치 기반 선정 3 APK (`vehiclecontrol`/`syslog`/`llm.model.provider`) 의 priority class count 평균 **424.33** 가 무작위 3 APK 평균 15.0 의 약 **28.29×** 수준.
- 즉 본 학기의 priority class 선정 (`stage 1` 진입 후보) 자체가 **선정 단계의 selection bias 를 가진다** — 본 학기 측정값 (Stage 1 P 85.7%, F1 0.923) 은 이 bias 가 반영된 corpus 결과.
- 단 priority class count 만으로는 final Stage 1 finding count 또는 정확도 차이가 직접 매칭되지 않는다. priority 가 많아도 모든 priority 가 finding 을 emit 하지 않을 수 있고, 적어도 finding 이 cleaner/more decisive 할 수 있다.
- **selection bias 측정의 한계**: Stage 1 LLM 분석을 무작위 3 APK 에 직접 적용하면 더 직접적 비교 가능하나, 프로젝트 시간 cost 로 priority class count 까지만 측정. 무작위 3 APK 의 Stage 1 P/R/F1 측정은 별도 확장 과제다.

## RQ1 implication

- 본 학기 `Stage 1 / Stage 3` 측정값은 **보안 가치 큰 priority subset 에서 측정된 값**. 무작위 PleOS APK sample 에서는 priority class density 가 더 낮아 finding 수 자체가 줄어들 가능성.
- 정량 측정값 자체는 영향이 클 수 있으나 (priority class 가 적으면 stage 1 finding 도 적음), Precision / FP rate 같은 normalised metric 은 priority class density 와 직접 비례하지 않을 수 있다.
- 최종 narrative 반영: 측정값은 **보안 가치 큰 corpus subset 한정** 임을 명시한다. 일반화 주장은 무작위 sample 추가 측정 후로 분리한다.
