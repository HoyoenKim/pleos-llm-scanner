#!/usr/bin/env python3
"""Scan PleOS/AAOS package metadata for Binder-service FN expansion candidates.

This script is intentionally read-only against the emulator. It does not bind to
services or invoke Binder transactions; it only parses package metadata exposed
by `dumpsys package`.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "data" / "reports"
RAW_DIR = REPORT_DIR / "_raw"
DATE = "20260518"

SURFACE_JSON = REPORT_DIR / f"vehicle_binder_surface_scan_{DATE}.json"
SURFACE_MD = REPORT_DIR / f"vehicle_binder_surface_scan_{DATE}.md"
RAW_DUMPSYS = RAW_DIR / f"vehicle_binder_surface_scan_{DATE}_dumpsys_package.txt"

KEYWORDS = (
    "VEHICLE",
    "CAR",
    "CONTROL",
    "BINDING",
    "MIRROR",
    "MIRRORS",
    "DOOR",
    "DOORS",
    "WINDOW",
    "WINDOWS",
    "SEAT",
    "SEATS",
    "CLIMATE",
    "DRIVE",
    "NAVI",
    "ROUTE",
    "CAP",
)

CONTROL_KEYWORDS = (
    "CONTROL",
    "SET_",
    "BINDING",
    "VEHICLE",
    "MIRROR",
    "DOOR",
    "WINDOW",
    "SEAT",
    "CLIMATE",
    "DRIVE",
)

PACKAGE_SEEDS = {
    "ai.pleos.playground.service.vehicle",
    "ai.pleos.playground.vehiclebridge.servicemeta",
    "ai.pleos.playground.service.cap",
    "ai.pleos.playground.service.navi",
    "ai.umos.vehiclecontrol",
}

PLEOS_PREFIXES = ("ai.pleos.", "ai.umos.")


@dataclass
class PermissionRecord:
    name: str
    source_package: str | None = None
    protection: str | None = None

    @property
    def is_weak(self) -> bool:
        protection = self.protection or ""
        return protection.startswith("normal") or protection.startswith("dangerous")

    @property
    def has_keyword(self) -> bool:
        upper = self.name.upper()
        return any(keyword in upper for keyword in KEYWORDS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_package": self.source_package,
            "protection": self.protection,
            "is_weak": self.is_weak,
            "has_keyword": self.has_keyword,
        }


@dataclass
class ResolverRecord:
    component_type: str
    action: str | None
    package: str
    component: str
    permission: str | None
    raw: str

    def to_dict(self, permissions: dict[str, PermissionRecord]) -> dict[str, Any]:
        perm = permissions.get(self.permission or "")
        return {
            "component_type": self.component_type,
            "action": self.action,
            "package": self.package,
            "component": self.component,
            "permission": self.permission,
            "permission_protection": perm.protection if perm else None,
            "permission_is_weak": perm.is_weak if perm else None,
            "raw": self.raw.strip(),
        }


@dataclass
class PackageRecord:
    name: str
    code_path: str | None = None
    version_name: str | None = None
    flags: str | None = None
    declared_permissions: list[PermissionRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "code_path": self.code_path,
            "version_name": self.version_name,
            "flags": self.flags,
            "declared_permissions": [p.to_dict() for p in self.declared_permissions],
        }


def run_adb(args: list[str], timeout: int = 120) -> str:
    completed = subprocess.run(
        ["adb", *args],
        cwd=ROOT.parent,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"adb {' '.join(args)} failed with {completed.returncode}: {completed.stderr}"
        )
    return completed.stdout


def has_keyword(value: str | None, keywords: tuple[str, ...] = KEYWORDS) -> bool:
    if not value:
        return False
    upper = value.upper()
    return any(keyword in upper for keyword in keywords)


def is_pleos_or_seed(package: str | None) -> bool:
    return bool(package and (package.startswith(PLEOS_PREFIXES) or package in PACKAGE_SEEDS))


def is_custom_weak_permission(permission: PermissionRecord | None) -> bool:
    if not permission or not permission.is_weak:
        return False
    if permission.name.startswith(("android.", "androidx.", "com.android.")):
        return False
    return permission.has_keyword or is_pleos_or_seed(permission.source_package)


def parse_permissions(lines: list[str]) -> dict[str, PermissionRecord]:
    records: dict[str, PermissionRecord] = {}
    current: PermissionRecord | None = None
    permission_re = re.compile(r"Permission \[(?P<name>[^\]]+)\]")
    source_re = re.compile(r"sourcePackage=(?P<source>\S+)")
    prot_re = re.compile(r"\bprot=(?P<prot>[^\s]+)")

    for line in lines:
        match = permission_re.search(line)
        if match:
            current = PermissionRecord(match.group("name"))
            records[current.name] = current
            continue
        if not current:
            continue
        source = source_re.search(line)
        if source:
            current.source_package = source.group("source")
        prot = prot_re.search(line)
        if prot:
            current.protection = prot.group("prot")

    return records


def parse_packages(lines: list[str]) -> dict[str, PackageRecord]:
    packages: dict[str, PackageRecord] = {}
    current: PackageRecord | None = None
    in_declared = False
    package_re = re.compile(r"^\s+Package \[(?P<name>[^\]]+)\]")
    declared_re = re.compile(r"^\s+(?P<name>\S+): prot=(?P<prot>\S+)")

    for line in lines:
        package_match = package_re.match(line)
        if package_match:
            current = PackageRecord(package_match.group("name"))
            packages[current.name] = current
            in_declared = False
            continue
        if not current:
            continue
        stripped = line.strip()
        if stripped.startswith("codePath="):
            current.code_path = stripped.split("=", 1)[1]
        elif stripped.startswith("versionName="):
            current.version_name = stripped.split("=", 1)[1]
        elif stripped.startswith("flags="):
            current.flags = stripped
        elif stripped == "declared permissions:":
            in_declared = True
        elif stripped.endswith("permissions:") and stripped != "declared permissions:":
            in_declared = False
        elif in_declared:
            declared = declared_re.match(line)
            if declared:
                current.declared_permissions.append(
                    PermissionRecord(
                        name=declared.group("name"),
                        source_package=current.name,
                        protection=declared.group("prot"),
                    )
                )

    return packages


def parse_resolver_records(lines: list[str]) -> list[ResolverRecord]:
    records: list[ResolverRecord] = []
    component_type: str | None = None
    action: str | None = None
    table_re = re.compile(r"^(?P<table>Receiver|Service|Activity) Resolver Table:")
    action_re = re.compile(r"^\s{6}(?P<action>[^:]+):\s*$")
    row_re = re.compile(
        r"^\s{8,}(?P<id>[0-9a-f]+)\s+"
        r"(?P<pkg>[A-Za-z0-9_.-]+)/(?P<component>\S+)"
        r"(?:\s+filter\s+\S+)?(?:\s+permission\s+(?P<permission>\S+))?\s*$"
    )

    for line in lines:
        table = table_re.match(line)
        if table:
            component_type = table.group("table").lower()
            action = None
            continue
        if component_type and re.match(r"^[A-Z][A-Za-z ]+:", line) and "Resolver Table" not in line:
            component_type = None
            action = None
            continue
        if not component_type:
            continue
        action_match = action_re.match(line)
        if action_match and not action_match.group("action").strip().startswith("Action"):
            action = action_match.group("action").strip()
            continue
        row = row_re.match(line)
        if row:
            records.append(
                ResolverRecord(
                    component_type=component_type,
                    action=action,
                    package=row.group("pkg"),
                    component=row.group("component"),
                    permission=row.group("permission"),
                    raw=line,
                )
            )

    return records


def parse_component_permissions(lines: list[str]) -> dict[str, str]:
    """Parse the late `Service permissions:` mapping in full dumpsys output."""
    permissions: dict[str, str] = {}
    in_section = False
    mapping_re = re.compile(r"^\s+(?P<component>[^:]+/[^:]+):\s+(?P<permission>\S+)\s*$")

    for line in lines:
        if line.strip() == "Service permissions:":
            in_section = True
            continue
        if in_section and line and not line.startswith(" "):
            break
        if not in_section:
            continue
        match = mapping_re.match(line)
        if match:
            permissions[match.group("component").strip()] = match.group("permission").strip()

    return permissions


def enrich_resolver_permissions(
    resolver_records: list[ResolverRecord], component_permissions: dict[str, str]
) -> None:
    for record in resolver_records:
        if record.permission or record.component_type != "service":
            continue
        key = f"{record.package}/{record.component}"
        if key in component_permissions:
            record.permission = component_permissions[key]


def score_candidate(
    package: str,
    package_record: PackageRecord | None,
    weak_permissions: list[PermissionRecord],
    resolver_records: list[ResolverRecord],
    permissions: dict[str, PermissionRecord],
) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []

    if package in PACKAGE_SEEDS:
        score += 10
        reasons.append("seed package from FN-expansion plan")

    declared_weak = [p for p in weak_permissions if p.source_package == package]
    if declared_weak:
        score += min(20, 4 * len(declared_weak))
        reasons.append(f"declares {len(declared_weak)} weak vehicle/control-related permission(s)")

    service_records = [r for r in resolver_records if r.package == package and r.component_type == "service"]
    for record in service_records:
        perm = permissions.get(record.permission or "")
        text = " ".join(filter(None, [record.action, record.permission, record.component]))
        if is_custom_weak_permission(perm):
            score += 40
            reasons.append(f"service resolver protected by weak permission {record.permission}")
        elif record.permission is None and is_pleos_or_seed(record.package) and has_keyword(text):
            score += 8
            reasons.append("service resolver has vehicle/control keyword but no resolver permission")
        elif is_pleos_or_seed(record.package) and has_keyword(text):
            score += 8
            reasons.append("service resolver has vehicle/control keyword")

        if (
            record.permission
            and is_pleos_or_seed(record.package)
            and has_keyword(text, CONTROL_KEYWORDS)
        ):
            score += 20
            reasons.append("service/action/permission contains control or vehicle binding keyword")
        elif is_pleos_or_seed(record.package) and has_keyword(text):
            score += 5
            reasons.append("service/action/permission contains navigation/capability keyword")

    if package_record and package_record.flags and "PRIVILEGED" in package_record.flags:
        score += 5
        reasons.append("privileged system package exposes app boundary")

    if package == "ai.pleos.playground.service.vehicle":
        score += 30
        reasons.append("oracle FN seed: VehicleService normal binding permission")

    if any("signature" in (p.protection or "") for p in weak_permissions):
        reasons.append("has signature permissions too, but weak candidates are evaluated separately")

    if score >= 75:
        severity = "Critical"
    elif score >= 45:
        severity = "High"
    elif score >= 20:
        severity = "Medium"
    else:
        severity = "Low"

    dedup_reasons = list(dict.fromkeys(reasons))
    return score, severity, dedup_reasons


def build_surface_report() -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    devices = run_adb(["devices"], timeout=20)
    dumpsys = run_adb(["shell", "dumpsys", "package"], timeout=180)
    RAW_DUMPSYS.write_text(dumpsys, encoding="utf-8")

    lines = dumpsys.splitlines()
    permissions = parse_permissions(lines)
    packages = parse_packages(lines)
    resolvers = parse_resolver_records(lines)
    component_permissions = parse_component_permissions(lines)
    enrich_resolver_permissions(resolvers, component_permissions)

    weak_keyword_permissions = [
        permission
        for permission in permissions.values()
        if is_custom_weak_permission(permission)
    ]

    resolver_hits = []
    for record in resolvers:
        perm = permissions.get(record.permission or "")
        text = " ".join(filter(None, [record.package, record.component, record.action, record.permission]))
        if (
            is_custom_weak_permission(perm)
            or (
                record.component_type == "service"
                and is_pleos_or_seed(record.package)
                and has_keyword(text)
            )
        ):
            resolver_hits.append(record)

    packages_of_interest = set(PACKAGE_SEEDS)
    packages_of_interest.update(p.source_package for p in weak_keyword_permissions if p.source_package)
    packages_of_interest.update(record.package for record in resolver_hits)

    candidates = []
    for package in sorted(packages_of_interest):
        weak_for_pkg = [p for p in weak_keyword_permissions if p.source_package == package]
        resolver_for_pkg = [r for r in resolver_hits if r.package == package]
        score, severity, reasons = score_candidate(
            package,
            packages.get(package),
            weak_for_pkg,
            resolver_for_pkg,
            permissions,
        )
        candidates.append(
            {
                "package": package,
                "severity": severity,
                "risk_score": score,
                "reasons": reasons,
                "package_metadata": packages.get(package).to_dict() if package in packages else None,
                "weak_keyword_permissions": [p.to_dict() for p in weak_for_pkg],
                "resolver_hits": [r.to_dict(permissions) for r in resolver_for_pkg],
            }
        )

    candidates.sort(key=lambda item: (-item["risk_score"], item["package"]))

    oracle = next(
        (candidate for candidate in candidates if candidate["package"] == "ai.pleos.playground.service.vehicle"),
        None,
    )
    oracle_redetected = bool(
        oracle
        and any(
            hit["component_type"] == "service"
            and hit["permission"] == "ai.pleos.playground.service.vehicle.VEHICLE_BINDING"
            and hit["permission_protection"] == "normal"
            for hit in oracle["resolver_hits"]
        )
    )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "adb_devices": devices.strip(),
        "raw_dumpsys_path": str(RAW_DUMPSYS.relative_to(ROOT)),
        "packages_scanned": len(packages),
        "permissions_scanned": len(permissions),
        "resolver_records_scanned": len(resolvers),
        "service_permissions_scanned": len(component_permissions),
        "weak_keyword_permissions_count": len(weak_keyword_permissions),
        "resolver_hits_count": len(resolver_hits),
        "oracle_vehicle_service_redetected": oracle_redetected,
        "weak_keyword_permissions": [p.to_dict() for p in weak_keyword_permissions],
        "resolver_hits": [r.to_dict(permissions) for r in resolver_hits],
        "candidates": candidates,
        "stage2_rule_recommendations": [
            "Flag custom normal/dangerous permissions whose names imply vehicle, car, control, binding, navigation, or capability access.",
            "Flag bound services protected only by those weak custom permissions as Stage 2 high-priority evidence.",
            "Escalate candidates when the decompiled Binder/AIDL layer contains write/control methods such as setPropertyValue, set*, register callbacks with mutation paths, or vehicle property ids.",
            "Keep signature/signature|privileged permission gates as mitigating evidence unless a normal permission also opens the same control surface.",
        ],
    }


def write_markdown(report: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# Vehicle Binder FN Expansion — Surface Scan")
    lines.append("")
    lines.append(f"- Generated: `{report['generated_at']}`")
    lines.append(f"- Packages scanned: **{report['packages_scanned']}**")
    lines.append(f"- Permissions scanned: **{report['permissions_scanned']}**")
    lines.append(f"- Resolver records scanned: **{report['resolver_records_scanned']}**")
    lines.append(f"- Service permission mappings scanned: **{report['service_permissions_scanned']}**")
    lines.append(f"- Weak vehicle/control keyword permissions: **{report['weak_keyword_permissions_count']}**")
    lines.append(f"- Resolver hits: **{report['resolver_hits_count']}**")
    lines.append(f"- Oracle `VehicleService` FN re-detected: **{report['oracle_vehicle_service_redetected']}**")
    lines.append("")
    lines.append("## Top Candidates")
    lines.append("")
    lines.append("| Rank | Package | Severity | Score | Key reason | Service resolver evidence |")
    lines.append("|---:|---|---:|---:|---|---|")
    for index, candidate in enumerate(report["candidates"][:20], start=1):
        reasons = "; ".join(candidate["reasons"][:3]) or "-"
        service_hits = [
            hit
            for hit in candidate["resolver_hits"]
            if hit["component_type"] == "service"
        ]
        if service_hits:
            evidence = "<br>".join(
                f"`{hit['action']}` → `{candidate['package']}/{hit['component']}` "
                f"perm=`{hit['permission']}` prot=`{hit['permission_protection']}`"
                for hit in service_hits[:3]
            )
        else:
            evidence = "-"
        lines.append(
            f"| {index} | `{candidate['package']}` | {candidate['severity']} | "
            f"{candidate['risk_score']} | {reasons} | {evidence} |"
        )

    lines.append("")
    lines.append("## Weak Custom Permissions With Vehicle/Control Keywords")
    lines.append("")
    lines.append("| Permission | Source package | Protection |")
    lines.append("|---|---|---|")
    for permission in report["weak_keyword_permissions"][:120]:
        lines.append(
            f"| `{permission['name']}` | `{permission['source_package']}` | `{permission['protection']}` |"
        )

    lines.append("")
    lines.append("## Stage 2 Rule Additions")
    lines.append("")
    for rule in report["stage2_rule_recommendations"]:
        lines.append(f"- {rule}")

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This scan is metadata-only. It identifies Binder/service surfaces that should "
        "be decompiled and reconstructed; it does not invoke any service or prove runtime effect."
    )
    lines.append(
        "The pentest `VehicleService` case is used as an oracle seed. If it is not re-detected, "
        "the scanner fails the acceptance criteria."
    )
    SURFACE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    report = build_surface_report()
    SURFACE_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report)
    print(f"Wrote {SURFACE_JSON}")
    print(f"Wrote {SURFACE_MD}")
    print(f"Oracle VehicleService re-detected: {report['oracle_vehicle_service_redetected']}")
    for candidate in report["candidates"][:8]:
        print(
            f"{candidate['severity']:>8} {candidate['risk_score']:>3} "
            f"{candidate['package']}"
        )


if __name__ == "__main__":
    main()
