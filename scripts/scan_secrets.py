#!/usr/bin/env python3
"""
Kestrel Shield — Pre-Commit Secret Scanner
Scans files staged for git commit to prevent accidental leakage of:
- Supabase API keys, JWT secrets, and project URLs with credentials
- MetaTrader EA hardcoded tokens
- Private keys and cryptographic secrets
"""
import sys
import re
import subprocess
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PATTERNS = [
    (r"sb_publishable_[a-zA-Z0-9_\-]{20,}", "Supabase publishable key"),
    (r"sb_secret_[a-zA-Z0-9_\-]{20,}", "Supabase secret key"),
    (r"sbp_[a-zA-Z0-9_\-]{20,}", "Supabase service role / personal key"),
    (r"kestrel-enterprise-owner-vip", "Kestrel VIP enterprise token"),
    (r"mt5-adapter-secret-change-me", "Kestrel default adapter secret"),
    (r"https:\/\/[a-z0-9]+\.supabase\.co.*(?:apikey|Bearer)", "Supabase URL with embedded auth"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private cryptographic key"),
    (r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}", "Hardcoded JWT Token"),
]

# Allow-list files (e.g. scanner itself or documentation mentioning pattern)
ALLOWLIST_FILES = {
    "scripts/scan_secrets.py",
    ".gitleaks.toml",
    ".env.example",
    "backend/.env.example",
    "backend/db/supabase_schema.sql",  # Historical DDL reference
}

IGNORE_EXTENSIONS = {".pdf", ".db", ".sqlite", ".png", ".jpg", ".ico", ".svg"}


def get_staged_files() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        return []

def scan_file(filepath: str) -> list[str]:
    clean_path = filepath.replace("\\", "/")
    if clean_path in ALLOWLIST_FILES:
        return []
    if clean_path.endswith(".env") or "/.env" in clean_path:
        return []
    ext = os.path.splitext(clean_path)[1].lower()
    if ext in IGNORE_EXTENSIONS:
        return []
    if not os.path.exists(filepath):
        return []

    
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                for pattern, name in PATTERNS:
                    if re.search(pattern, line):
                        # Skip comment examples in example files
                        if ".example" in filepath:
                            continue
                        findings.append(f"  {filepath}:{line_no} - Detected {name}")
    except Exception as e:
        pass
    return findings

def main():
    staged = get_staged_files()
    if not staged:
        # If running standalone, scan repo tracked files
        print("[Kestrel Shield] Running full working directory scan...")
        all_findings = []
        for root, _, files in os.walk("."):
            if ".git" in root or "node_modules" in root or ".venv" in root or ".next" in root:
                continue
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), ".")
                all_findings.extend(scan_file(rel))
        if all_findings:
            print("[Kestrel Shield] \u274c BLOCKED: Secrets detected:")
            for f in all_findings:
                print(f)
            sys.exit(1)
        print("[Kestrel Shield] \u2705 Zero secrets found in working directory.")
        return

    all_findings = []
    for f in staged:
        all_findings.extend(scan_file(f))

    if all_findings:
        print("\n========================================================")
        print("[Kestrel Shield] \u274c COMMIT REJECTED: Secrets detected in staged files!")
        print("========================================================")
        for f in all_findings:
            print(f)
        print("\nPlease move secrets to environment variables (.env) before committing.")
        sys.exit(1)

    print("[Kestrel Shield] \u2705 Pre-commit secret scan passed. No secrets detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
