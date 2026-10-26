#!/usr/bin/env python3
"""플러그인 없이 gitignore-guard 를 ~/.claude 에 설치한다.

  python install.py

1) 검사 스크립트를 ~/.claude/hooks/ 로 복사
2) ~/.claude/settings.json 에 PreToolUse(Bash) 훅 추가 (기존 설정 보존, 백업 생성)
"""
import json
import shutil
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent / "plugins" / "gitignore-guard" / "scripts" / "check_gitignore.py"
CLAUDE_DIR = Path.home() / ".claude"
DEST = CLAUDE_DIR / "hooks" / "check_gitignore.py"
SETTINGS = CLAUDE_DIR / "settings.json"


def main():
    script = DEST.as_posix()
    command = f'python3 "{script}" --claude 2>/dev/null || python "{script}" --claude'
    entry = {
        "matcher": "Bash",
        "hooks": [{
            "type": "command",
            "command": command,
            "timeout": 15,
            "statusMessage": "민감 파일 .gitignore 검사 중...",
        }],
    }

    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"settings.json 이 올바른 JSON 이 아니라 중단합니다 (수정하지 않음): {e}", file=sys.stderr)
            return 1

    pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    already = any("check_gitignore.py" in h.get("command", "") for e in pre for h in e.get("hooks", []))

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DEST)
    print(f"스크립트 복사됨: {DEST}")

    if already:
        print("settings.json 에 훅이 이미 등록돼 있어 그대로 둡니다.")
    else:
        if SETTINGS.exists():
            backup = SETTINGS.with_name(f"settings.json.bak-{time.strftime('%Y%m%d%H%M%S')}")
            shutil.copyfile(SETTINGS, backup)
            print(f"settings.json 백업: {backup}")
        pre.append(entry)
        SETTINGS.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("settings.json 에 훅 등록 완료")

    print("\n다음 단계")
    print("  1) Claude Code 에서 /hooks 를 한 번 열거나 재시작하세요.")
    print("  2) git 훅(직접 입력한 git 명령까지 검사)은 각 저장소 폴더에서:")
    print(f'     python "{script}" --install')
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
