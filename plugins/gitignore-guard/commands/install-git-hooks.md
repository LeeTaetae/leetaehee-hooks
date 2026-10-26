---
description: 현재 git 저장소에 gitignore-guard 의 pre-commit / pre-push 훅을 설치합니다
allowed-tools: Bash
---

현재 작업 디렉터리의 git 저장소에 git 훅을 설치합니다. 아래 명령을 그대로 실행하고, 출력된 결과(설치됨/건너뜀)를 한국어로 간단히 알려주세요.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_gitignore.py" --install || python "${CLAUDE_PLUGIN_ROOT}/scripts/check_gitignore.py" --install
```

"건너뜀 (이미 존재)"이 나오면 기존 훅이 있다는 뜻입니다. 덮어쓰지 말고, 기존 훅 파일 안에서 `.git/hooks/check_gitignore.py --git` 을 호출하도록 안내하세요.
