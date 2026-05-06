# 일반화 가능성 평가 — QNX / Linux IVI 으로의 확장

_작성일: 2026-04-30_

본 문서는 본 학기에 PleOS (Android 14 + AAOS 변형) 환경에서 검증한 정적 분석
파이프라인이 **QNX / Linux 기반 IVI** 같은 다른 차량용 OS로 일반화 가능한지를
평가한다. 평가는 (1) 도구 / (2) 키워드 카테고리 / (3) AAOS 매핑 / (4) TARA 자산의
4축으로 진행한다.

## 1. 본 파이프라인의 OS-종속 부분과 OS-독립 부분

| 컴포넌트 | OS-독립 | OS-종속 (Android/AAOS) | 비고 |
|---|---|---|---|
| `scripts/decompile.sh` | ✗ | jadx (Java/Kotlin → DEX/APK 전용) | QNX/Linux는 ELF |
| `src/deobf/entropy.py` | ✓ | — | 식별자 entropy는 OS-독립 |
| `configs/prompts/stage1_detect.md` | 부분 | 일부 Android API 언급 | 룰 기반 보강 가능 |
| `configs/prompts/stage_b_deobfuscate.md` | ✓ | — | 이름 복원은 OS-독립 |
| `src/eval.py` / `src/ablation.py` | ✓ | — | GT 라벨 스키마만 동일 |
| `configs/keywords.yaml` | 부분 | Android-specific 패턴 (`android:exported`, `Context.getSystemService`) | 카테고리는 보편 |
| `configs/aaos_mapping.yaml` | ✗ | AAOS 섹션 번호 | OS별 가이드라인으로 swap 필요 |
| `src/tara_generate.py` | ✓ | — | ISO/SAE 21434는 OS-독립 |
| `src/aaos_map.py` | 부분 | — | mapping yaml만 swap |
| `src/viz/plot_metrics.py` | ✓ | — | 차트 |

**결론**: 약 60~70%는 OS-독립. OS 전환 시 swap이 필요한 부분은 (a) 디컴파일 도구
체인, (b) 키워드 룰셋, (c) 매핑 yaml.

## 2. QNX 환경으로의 일반화 가능성

### 2.1 QNX IVI의 보안 모델 차이

| 항목 | Android (PleOS) | QNX |
|---|---|---|
| 바이너리 형식 | DEX/APK (Java/Kotlin) | ELF (C/C++ 주력, 일부 Java/Qt) |
| 권한 모델 | UID + Manifest permission | POSIX user/group + RBAC + adaptive policies |
| IPC 모델 | Intent / ContentProvider / Binder | QNX message passing (channels) |
| 자격증명 저장 | Android Keystore | (구현 체) HSM / TEE / 파일 |
| 통신 보안 | TLS / Certificate Pinning | TLS / 인증서 / DDS 보안 (자율주행 stack) |
| 가이드라인 | AAOS Security | QNX Security Reference Manual |

### 2.2 어떤 부분이 그대로 활용 가능한가

- **카테고리 추상화** — `keywords.yaml`의 6 카테고리 (crypto / network /
  permission / intent / hardcoded / reflection_dynamic) 중 4개는 OS-독립:
  crypto, network, hardcoded, reflection_dynamic. permission / intent는 OS별
  치환.
- **TARA 흐름** — 자산 식별 → 위협 시나리오 → 영향도 → 공격가능성 → 위험은
  ISO/SAE 21434 기반이라 OS 무관. `src/tara_generate.py` 그대로 가능.
- **이름 복원 / 난독화 측정** — Shannon entropy + LLM 이름 복원은 식별자가 토큰화
  될 수만 있으면 OS-독립. C++ symbol mangling (`_ZN5...`) 도 동일 패턴 적용 가능.
- **Multi-stage 검증 흐름** — Stage 1 키워드 → Stage 2 caller 분석 → Stage 3
  앙상블은 모든 정적 분석에 보편적.

### 2.3 OS 전환 시 swap 비용

| 작업 | 예상 작업량 | 비고 |
|---|---|---|
| 디컴파일러 → Ghidra/IDA Pro로 변경 | 2~3일 | C/C++ ELF 처리 |
| QNX-specific 키워드 룰셋 | 1주 | message passing API, security policy syntax |
| QNX Security Reference Manual 매핑 yaml | 3~5일 | 본 학기 AAOS yaml 형식 그대로 swap |
| TARA 자산 카탈로그 수정 | 2일 | QNX는 process-level isolation 더 강함 → 자산 단위 변경 |
| 키워드 카테고리 신규 추가 | 1주 | DDS 보안, mixed-criticality 격리 등 |
| 합계 | **2~3주** | 본 학기 환경 셋업 1주에 비교 |

### 2.4 일반화 시 잃는 부분

- **AAOS-specific finding** — `lmp-1` (PromptsContentProvider exported)는
  Android Compose / Hilt / ContentProvider 모델에 강하게 의존. QNX에서는 동일
  finding을 만들 수 없음.
- **Compose Nav deep-link audit** — vc-3/4 의 4중 차단 분석은 Android Compose
  Navigation 구조 특화. QNX UI framework (Qt/HMI) 는 다른 axis 필요.

**그러나 보편 finding은 그대로 작동**:
- hardcoded credential (ssl-5, ucl1-1) — KDF passphrase는 OS 무관
- plaintext network (ssl-6) — gRPC / TCP / DDS 모두 적용
- weak crypto (ucl1-2) — AES/DES/MD5 알고리즘 식별은 OS 무관
- 차량 syslog 평문 (ssl-3) — IVI 도메인 보편

## 3. Linux IVI (예: GENIVI / Automotive Grade Linux)으로의 일반화

### 3.1 AGL과의 상대적 거리

AGL은 PleOS와 더 가깝다:
- 둘 다 Linux kernel + 사용자 공간 앱 모델
- AGL은 systemd + smack + cgroup 기반 보안 — Android의 SELinux와 유사 컨셉
- Java/Kotlin 대신 C++ / Qt / HTML5 위주

### 3.2 swap 작업량

| 작업 | 예상 작업량 |
|---|---|
| 디컴파일러 → 소스 직접 분석 (오픈소스 위주) | 1주 |
| AGL-specific 키워드 룰셋 | 3~5일 |
| AGL Security Best Practices 매핑 yaml | 3일 |
| Process / IPC 모델 (DBus, AFB) 카테고리 추가 | 1주 |
| 합계 | **2~3주** |

### 3.3 일반화 시 부각되는 finding

- **DBus 인터페이스 export** — `<allow send_destination=...>` policy 설정 = 본 학기
  intent exported의 AGL 등가물.
- **AFB (Application Framework Binder) 권한** = Android permission의 등가물.

## 4. 본 파이프라인의 일반화 평가 종합

| 차원 | 일반화 가능성 | 근거 |
|---|---|---|
| 분석 방법론 (Multi-stage + 앙상블) | **High** | 룰 + LLM 흐름은 OS 무관 |
| 평가 프레임워크 (P/R/F1 + Ablation) | **High** | GT 라벨 스키마만 동일하면 됨 |
| TARA 통합 흐름 | **High** | ISO/SAE 21434 기반 |
| 키워드 카테고리 | **Medium** | 6 카테고리 중 4개 OS-독립, 2개 swap |
| 가이드라인 매핑 yaml | **Medium** | 형식 동일, 내용 swap |
| 디컴파일 도구 체인 | **Low** | jadx → Ghidra/IDA로 전체 swap |
| AAOS-specific finding (Compose Nav, ContentProvider) | **Low** | Android-only, 외삽 불가 |

**총평**: 본 파이프라인의 **Phase A-D 흐름과 측정 프레임워크**는 OS 변경에 강건하며,
swap 작업량은 2-3주로 추정. 단, Android-specific finding은 그대로 옮기지 못하고
OS별 등가물을 별도 라벨링해야 함.

## 5. 일반화 PoC 권고 (Future Work)

본 학기 학적 위에서 일반화 PoC를 한다면:

1. **AGL이 가장 적합** — Linux 기반이라 환경 셋업 친숙, 오픈소스 corpus 풍부.
2. **시작 코퍼스**: AGL meta-agl recipe에서 sample app 1개 + Linux IVI common
   vuln dataset (CVE 매핑).
3. **재사용 가능 부품 우선순위**:
   - `src/eval.py` + `src/ablation.py` (그대로)
   - `src/tara_generate.py` (asset key swap만)
   - `configs/keywords.yaml` (4 카테고리 그대로 + 2 swap)
   - `configs/aaos_mapping.yaml` → `configs/agl_mapping.yaml` (형식 그대로)
4. **새로 만들 부품**: `scripts/decompile.sh` 대신 `scripts/extract_elf.sh`,
   AGL-specific stage1 prompt.

본 학기 측정값 (P 77.8% → 100%, F1 0.875 → 0.952)이 AGL에서 어떤 수치로 떨어지는지
정량 비교해야 일반화의 비용/효과가 결정됨 — Future Work.

## 6. 본 학기 결론

본 학기 산출물은:
- **방법론으로서**: OS-independent — 다른 IVI로 옮길 수 있음 (2-3주 swap 비용).
- **결과 데이터로서**: PleOS-specific — 직접 외삽 X, OS별 GT 라벨링 필요.
- **TARA 산출물로서**: 형식과 흐름은 일반화, 자산 카탈로그는 IVI 도메인 공통적.

PPT 12주차 "일반화 평가" 항목의 deliverable은 본 문서로 충족. 실제 수치 측정은
Future Work.
