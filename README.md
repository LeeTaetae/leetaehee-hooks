# leetaehee-hooks

LeeTaetae의 Claude Code 훅 모음.

## gitignore-guard

`.env`, `*.pem`, `*.key`, `credentials.json` 같은 민감 파일이 `.gitignore`로 보호되지 않은 채 `git add` / `commit` / `push` 되는 것을 막고 경고를 띄웁니다.

| 훅 | 대상 | 차단 방식 |
|---|---|---|
| Claude 훅 (`PreToolUse` · `Bash`) | Claude 가 실행하는 git 명령 | 명령 거부 + 경고 표시 |
| git 훅 (`pre-commit`, `pre-push`) | 사용자가 터미널에서 직접 입력한 git 명령 | 경고 출력 후 `exit 1` |

**위험 판정**: 민감 파일이 ① 이미 git 에 추적 중이거나 ② untracked 인데 `.gitignore` 에 없을 때.
`.env.example` 같은 샘플 파일(`.example` `.sample` `.template` `.dist`)은 제외합니다.

### 설치 (방법 A: 플러그인, 추천)

Claude Code 안에서:

```
/plugin marketplace add LeeTaetae/leetaehee-hooks
/plugin install gitignore-guard@leetaehee-hooks
```

설치 후 `/hooks` 를 한 번 열거나 재시작하세요. 직접 입력한 git 명령까지 막으려면, git 저장소에서 아래 명령을 실행합니다.

```
/gitignore-guard:install-git-hooks
```

### 설치 (방법 B: 스크립트)

```bash
git clone https://github.com/LeeTaetae/leetaehee-hooks
python leetaehee-hooks/install.py
```

`~/.claude/settings.json` 은 백업 후 병합하며, 이미 등록돼 있으면 건드리지 않습니다.
git 훅은 각 저장소 폴더에서 `python ~/.claude/hooks/check_gitignore.py --install` 로 설치합니다.

### 요구 사항

- Python 3 (`python3` 또는 `python` 이 PATH 에 있어야 함)
- Windows 는 Git for Windows (Git Bash)

### 한계

- 파일명 패턴 기반이라 코드에 박힌 API 키 같은 내용은 못 잡습니다. 내용 검사는 gitleaks 등을 함께 쓰세요.
- Claude 훅은 명령 실행 *직전*에 검사하므로, 같은 명령 안에서 새로 만든 파일은 못 봅니다 (예: `echo K=1 > .env && git add .`). 이 경우는 git 훅이 막습니다.
- 기존 `pre-commit` 훅이 있는 저장소는 덮어쓰지 않고 건너뜁니다. 기존 훅에서 `.git/hooks/check_gitignore.py --git` 을 호출하세요.

### 제거

- 플러그인: `/plugin uninstall gitignore-guard@leetaehee-hooks`
- 스크립트 방식: `settings.json` 의 `PreToolUse` 항목과 `~/.claude/hooks/check_gitignore.py` 삭제
- git 훅: `.git/hooks/pre-commit`, `pre-push`, `check_gitignore.py` 삭제
