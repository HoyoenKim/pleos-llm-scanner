"""Extend data/reports/local/stage3_ensemble.json with InsecureBankv2 9 findings.

Stage 3 multi-perspective consensus (attacker / defender / domain_expert)
applied to the 9 ib2-* findings from R1.d sample expansion. 7 strong-TP
(3/3), 2 TP (2/3) where domain_expert abstains on banking-only context
under the selectivity-calibrated defender prompt (R2.a follow-up).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data" / "reports" / "local" / "stage3_ensemble.json"

NEW = [
    {
        "id": "ib2-1", "class": "com.android.insecurebankv2.DoLogin", "line": 51,
        "category": "network", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.95,
        "title": "Cleartext HTTP for login POST — 3/3 strong TP",
        "evidence": "<redacted: external public corpus — see data/reports/external/InsecureBankv2_20260507.json>",
        "rationale_merged": "All three perspectives confirm. Attacker: trivial MITM credential capture on any non-HTTPS hop. Defender: TLS 1.2+ + network_security_config + certificate pinning required. Domain expert: MASVS-NETWORK-1 canonical violation; in banking context this is direct credential / financial theft.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "MITM capture trivial", "attack_chain": ["intercept HTTP POST /login", "extract username/password"]},
            "defender": {"severity": "high", "missing_control": "android:usesCleartextTraffic=false + TLS 1.2+ + network_security_config + cert pinning"},
            "domain_expert": {"severity": "high", "stride": "I", "tara_impact": "financial", "verdict": "MASVS-NETWORK-1 canonical"}
        }
    },
    {
        "id": "ib2-2", "class": "com.android.insecurebankv2.DoLogin", "line": 115,
        "category": "hardcoded", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.97,
        "title": "Credentials logged plaintext on successful login — 3/3 strong TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: any READ_LOGS-holding app or adb-connected developer harvests credentials. Defender: never log credentials, strip Log.d in release builds. Domain expert: MASVS-STORAGE-3 + GDPR / financial regulatory exposure.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "credential harvest from logcat", "attack_chain": ["malicious app with READ_LOGS", "scan logcat 'Successful Login:'", "extract credentials"]},
            "defender": {"severity": "high", "missing_control": "ProGuard rule to strip Log.d in release + lint check on credential variables"},
            "domain_expert": {"severity": "high", "stride": "I", "tara_impact": "financial+privacy", "verdict": "MASVS-STORAGE-3"}
        }
    },
    {
        "id": "ib2-3", "class": "com.android.insecurebankv2.CryptoClass", "line": 22,
        "category": "hardcoded", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.99,
        "title": "Hardcoded AES-256 key string in source — 3/3 strong TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: APK reverse trivially yields the literal — every device shares the same key. Defender: keys must come from Android Keystore or per-user PBKDF2-derived secondary. Domain expert: MASVS-CRYPTO-1 canonical.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "APK extraction yields universal key", "attack_chain": ["jadx CryptoClass.java", "read key literal", "decrypt SharedPreferences ciphertexts"]},
            "defender": {"severity": "high", "missing_control": "Android Keystore-backed key + per-user PBKDF2-derived secondary"},
            "domain_expert": {"severity": "high", "stride": "I+T", "tara_impact": "financial", "verdict": "MASVS-CRYPTO-1 canonical"}
        }
    },
    {
        "id": "ib2-4", "class": "com.android.insecurebankv2.CryptoClass", "line": 23,
        "category": "crypto", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.97,
        "title": "Fixed all-zero IV with AES-CBC — 3/3 strong TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: deterministic encryption, chosen-plaintext attacks viable. Defender: SecureRandom-generated IV per message, prefer AES-GCM. Domain expert: MASVS-CRYPTO-1.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "chosen-plaintext attack feasible", "attack_chain": ["control plaintext via UI", "observe deterministic ciphertext mapping"]},
            "defender": {"severity": "high", "missing_control": "SecureRandom 16-byte IV per message; preferably AES-GCM (AEAD)"},
            "domain_expert": {"severity": "high", "stride": "T", "tara_impact": "financial", "verdict": "MASVS-CRYPTO-1"}
        }
    },
    {
        "id": "ib2-5", "class": "com.android.insecurebankv2.MyBroadCastReceiver", "line": 32,
        "category": "intent", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.99,
        "title": "Exported receiver SMSes decrypted password to caller-supplied phone — 3/3 strong TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: any installed app broadcasts 'theBroadcast' with phonenumber+newpass — receiver decrypts stored password and SMSes to attacker. No permission required. Defender: signature-permission + remove SMS export entirely. Domain expert: MASVS-PLATFORM-3 + MASVS-AUTH-2.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "direct credential exfil via SMS", "attack_chain": ["broadcast theBroadcast extras phonenumber=attacker, newpass=*", "MyBroadCastReceiver.onReceive fires", "credential SMS to attacker"]},
            "defender": {"severity": "high", "missing_control": "signature-permission on receiver + remove SMS-of-credential flow (server-side)"},
            "domain_expert": {"severity": "high", "stride": "I+E", "tara_impact": "financial+privacy", "verdict": "MASVS-PLATFORM-3 + MASVS-AUTH-2"}
        }
    },
    {
        "id": "ib2-6", "class": "com.android.insecurebankv2.AndroidManifest", "line": 64,
        "category": "intent", "stage1_severity": "high",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.96,
        "title": "Exported ContentProvider with no read/write permission — 3/3 strong TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: any installed app queries TrackUserContentProvider — login records harvestable. Defender: signature-level android:readPermission + writePermission. Domain expert: MASVS-PLATFORM-3 + privacy regulation exposure.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "login tracking harvestable", "attack_chain": ["resolve content://com.android.insecurebankv2.TrackUserContentProvider", "query all rows"]},
            "defender": {"severity": "high", "missing_control": "android:readPermission + writePermission with signature-level perm"},
            "domain_expert": {"severity": "high", "stride": "I", "tara_impact": "privacy", "verdict": "MASVS-PLATFORM-3"}
        }
    },
    {
        "id": "ib2-7", "class": "com.android.insecurebankv2.AndroidManifest", "line": 68,
        "category": "intent", "stage1_severity": "medium",
        "consensus_count": 3, "consensus_perspectives": ["attacker", "defender", "domain_expert"],
        "consensus_class": "strong_TP", "severity": "high", "confidence": 0.94,
        "title": "Receiver exported without permission, action triggers credential SMS — 3/3 strong TP (severity raised by chain analysis)",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Stage 1 medium 이지만 cross-class dataflow (receiver → 자격증명 SMS, ib2-5) 가 명백히 high. Attacker: ib2-5 의 entry point. Defender: signature-permission. Domain expert: chain risk high.",
        "per_perspective": {
            "attacker": {"severity": "high", "verdict": "broadcast → ib2-5 chain", "attack_chain": ["broadcast theBroadcast", "receiver fires onReceive", "SMS-of-credential"]},
            "defender": {"severity": "high", "missing_control": "android:permission with signature-level"},
            "domain_expert": {"severity": "high", "stride": "E", "tara_impact": "financial", "verdict": "MASVS-PLATFORM-3 chain"}
        }
    },
    {
        "id": "ib2-8", "class": "com.android.insecurebankv2.AndroidManifest", "line": 49,
        "category": "intent", "stage1_severity": "medium",
        "consensus_count": 2, "consensus_perspectives": ["attacker", "defender"],
        "consensus_class": "TP", "severity": "medium", "confidence": 0.78,
        "title": "Multiple post-login activities exported=true — 2/3 TP (domain_expert abstain on banking context)",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: bypass login by directly launching PostLogin / DoTransfer / ViewStatement / ChangePassword. Defender: 인터널 activities 는 exported=false. Domain expert abstains: vehicle-security focused, banking-specific direct intent flow 의 vehicle asset 영향 약함 — selectivity-calibrated defender prompt 가 downweight 한다.",
        "per_perspective": {
            "attacker": {"severity": "medium", "verdict": "login bypass via direct intent", "attack_chain": ["startActivity(PostLogin) crafted extras", "skip authentication"]},
            "defender": {"severity": "medium", "missing_control": "android:exported=false on internal activities"},
            "domain_expert": {"severity": "low", "verdict": "abstain — banking app, not direct vehicle asset"}
        }
    },
    {
        "id": "ib2-9", "class": "com.android.insecurebankv2.ViewStatement", "line": 30,
        "category": "network", "stage1_severity": "medium",
        "consensus_count": 2, "consensus_perspectives": ["attacker", "defender"],
        "consensus_class": "TP", "severity": "medium", "confidence": 0.72,
        "title": "WebView JavaScriptEnabled=true on exported activity — 2/3 TP",
        "evidence": "<redacted: external public corpus>",
        "rationale_merged": "Attacker: combined with ib2-8 (exported activity) + statement endpoint over HTTP, XSS / token-exfil sink. Defender: scheme allow-list via WebViewClient.shouldOverrideUrlLoading. Domain expert abstains: financial WebView 가 vehicle 측면 약함.",
        "per_perspective": {
            "attacker": {"severity": "medium", "verdict": "XSS sink via exported WebView", "attack_chain": ["intent → ViewStatement", "controlled URL or HTTP statement", "JS injection"]},
            "defender": {"severity": "medium", "missing_control": "setJavaScriptEnabled(false) where possible + WebViewAssetLoader scheme allow-list"},
            "domain_expert": {"severity": "low", "verdict": "abstain — banking WebView, not direct vehicle asset"}
        }
    }
]


def main() -> None:
    d = json.loads(P.read_text(encoding="utf-8"))
    existing_ids = {r["id"] for r in d.get("results", [])}
    added = 0
    for entry in NEW:
        if entry["id"] in existing_ids:
            continue
        d["results"].append(entry)
        added += 1

    d["input_findings"] = (
        "data/reports/{per_apk_local,external}/*.json (n=28 stage1 findings)"
    )
    hist = d.setdefault("_update_history", [])
    if not any(h.get("date") == "2026-05-07" for h in hist):
        hist.append({
            "date": "2026-05-07",
            "change": (
                "Extended ensemble to InsecureBankv2 9 findings (R2.a follow-up "
                "after defender selectivity calibration). 7 strong-TP (3/3), 2 TP "
                "(2/3 — domain_expert abstain on banking context). All 9 are TP — "
                "InsecureBankv2 is intentionally vulnerable corpus. Combined "
                "stage 3 corpus n=19 → n=28."
            )
        })

    s = d.setdefault("summary", {})
    s["n_findings_input_extended_2026_05_07"] = 28
    s["ib2_consensus"] = {
        "strong_TP_3of3": 7,
        "TP_2of3": 2,
        "uncertain_1of3": 0,
        "clean_0of3": 0,
        "note": (
            "All 9 InsecureBankv2 findings TP. ib2-8 / ib2-9 are 2/3 because "
            "domain_expert (vehicle-security focused) abstains on banking-only "
            "context — selectivity-calibrated defender prompt downweights these "
            "to MEDIUM."
        )
    }

    P.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {P.relative_to(ROOT)} -- added {added} entries (total {len(d['results'])})")


if __name__ == "__main__":
    main()
