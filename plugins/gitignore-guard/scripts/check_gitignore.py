#!/usr/bin/env python3
"""git add/commit/push 전에 민감 파일이 .gitignore 밖에 노출돼 있는지 검사한다.

사용법
  --claude   Claude Code PreToolUse 훅 (Bash 도구, stdin 으로 JSON 입력)
  --git      git pre-commit / pre-push 훅 (사용자가 직접 입력한 git 명령 대상)
  --install  현재 저장소에 pre-commit / pre-push 훅 설치

위험 판정 (둘 중 하나라도 해당하면 차단)
  1) 민감 파일이 이미 git 에 추적 중 (.gitignore 는 추적 중인 파일에 효과 없음)
  2) 민감 파일이 untracked 인데 .gitignore 에 없음 (git add . 하면 올라감)
"""
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys

# 파일명(basename) 기준 패턴, 대소문자 무시
SENSITIVE = [
    ".env", ".env.*", "*.env",
    "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    "credentials.json", ".credentials.json", "service-account*.json",
    "secrets.*", "secret.*", ".netrc", "settings.local.json",
]
# 값이 비어 있는 샘플 파일은 올려도 되므로 제외
TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist")

# git add / commit / push 만 대상 (git -C dir push 같은 옵션 포함, 파이프·&& 뒤도 인식)
GIT_CMD = re.compile(r"(?:^|[;&|(]\s*)git\s+(?:-[cC]\s+\S+\s+|-\S+\s+)*(add|commit|push)\b")


def run_git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def is_sensitive(path):
    name = os.path.basename(path).lower()
    if name.endswith(TEMPLATE_SUFFIXES):
        return False
    return any(fnmatch.fnmatch(name, pat) for pat in SENSITIVE)


def find_risks(cwd):
    """[(경로, 사유)] 반환. git 저장소가 아니면 None."""
    code, top = run_git(cwd, "rev-parse", "--show-toplevel")
    if code != 0:
        return None
    top = top.strip()
    _, tracked = run_git(top, "ls-files", "-z")
    # --exclude-standard: .gitignore 에 걸린 파일은 빠지므로, 남는 것이 "무방비" 파일
    _, untracked = run_git(top, "ls-files", "-z", "--others", "--exclude-standard")

    risks = [(p, "이미 git 에 추적 중") for p in tracked.split("\0") if p and is_sensitive(p)]
    risks += [(p, ".gitignore 에 없음") for p in untracked.split("\0") if p and is_sensitive(p)]
    return risks


def build_message(risks):
    lines = ["[보안 경고] 민감 파일이 .gitignore 로 보호되지 않아 git 작업을 차단했습니다."]
    lines += [f"  - {path}  ({reason})" for path, reason in risks]
    lines += [
        "조치: .gitignore 에 해당 파일을 추가하세요.",
        "이미 추적 중이면 'git rm --cached <파일>' 로 추적을 해제해야 하며,",
        "이미 push 한 적이 있다면 해당 키/비밀번호는 폐기·재발급하세요.",
    ]
    return "\n".join(lines)


def claude_mode():
    payload = json.load(sys.stdin)
    command = (payload.get("tool_input") or {}).get("command", "")
    if not GIT_CMD.search(command):
        return 0
    risks = find_risks(payload.get("cwd") or os.getcwd())
    if not risks:
        return 0
    msg = build_message(risks)
    json.dump({
        "systemMessage": msg,  # 사용자 화면에 경고 표시
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",  # 명령 실행 차단 (Claude 에게도 사유 전달)
            "permissionDecisionReason": msg,
        },
    }, sys.stdout, ensure_ascii=False)
    return 0


def git_mode():
    risks = find_risks(os.getcwd())
    if not risks:
        return 0
    print(build_message(risks), file=sys.stderr)
    return 1


def install():
    code, path = run_git(os.getcwd(), "rev-parse", "--git-path", "hooks")
    if code != 0:
        print("git 저장소가 아닙니다.", file=sys.stderr)
        return 1
    hooks_dir = os.path.abspath(os.path.join(os.getcwd(), path.strip()))
    os.makedirs(hooks_dir, exist_ok=True)
    # 플러그인 캐시 경로는 업데이트 때 바뀌므로, 스크립트를 훅 폴더로 복사해 저장소 안에서 자급자족하게 한다
    shutil.copyfile(os.path.abspath(__file__), os.path.join(hooks_dir, "check_gitignore.py"))
    # python3 / python 중 실제로 실행되는 것을 사용 (Windows 스토어 python3 스텁 대비)
    body = (
        "#!/bin/sh\n"
        'for PY in python3 python; do\n'
        '  command -v "$PY" >/dev/null 2>&1 || continue\n'
        '  "$PY" -c "" 2>/dev/null || continue\n'
        '  exec "$PY" "$(dirname "$0")/check_gitignore.py" --git\n'
        "done\n"
        'echo "[gitignore-guard] python 을 찾지 못해 검사를 건너뜁니다." >&2\n'
    )
    for name in ("pre-commit", "pre-push"):
        target = os.path.join(hooks_dir, name)
        if os.path.exists(target):
            print(f"건너뜀 (이미 존재): {target}")
            continue
        with open(target, "w", newline="\n") as f:
            f.write(body)
        os.chmod(target, 0o755)
        print(f"설치됨: {target}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    handlers = {"--claude": claude_mode, "--git": git_mode, "--install": install}
    if mode not in handlers:
        print(__doc__)
        sys.exit(2)
    sys.exit(handlers[mode]())
