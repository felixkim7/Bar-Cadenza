# Start here

## 1. Put the pack in a new project folder
Extract the ZIP with hidden folders included. Suggested location: `C:\Projects\BarCadenza`.
Do not extract over an existing implementation without comparing files first. Keep art references in `references/art/`.

## 2. Open the root in VS Code
Use File → Open Folder, then open a Windows PowerShell terminal in that folder. Native Windows is the recommended first runtime. Claude Code may use another environment, but Windows behavior is the acceptance target.

## 3. Check prerequisites
```powershell
py -3.14 --version
uv --version
git --version
claude --version
```
Python 3.14 is the user-selected baseline (D019). If a prerequisite is missing, use its official installer; see docs/SETUP_WINDOWS.md. Do not assume Claude Code subscription access supplies game API credits.

## 4. Run the standalone handoff check
```powershell
py -3.14 tools/check_starter.py
py -3.14 tools/starter_info.py
```
These require only Python. They do not install dependencies, call an AI service, or launch a game.

## 5. Start Claude Code
```powershell
claude
```
Paste:

> Read CLAUDE.md, docs/DECISIONS.md, docs/STATUS.md, and docs/tasks/INDEX.md. Start T001 only. Preserve all confirmed decisions, including continuous time and Korean/English new-game selection. Resolve and lock dependencies on Windows, verify the bootstrap, and record actual evidence. Do not implement later tasks or change the game scope. Ask only for a decision that blocks T001.

After T001, request the next task or an explicitly named range. See docs/CLAUDE_WORKFLOW.md for prompts.

## Before a live API task
Choose a provider/model and a budget. Until then, mock/offline work continues. Do not paste keys into Claude conversations; store them locally using the provider-specific environment variable once implemented.

## 한국어 요약
1. ZIP 전체를 새 프로젝트 폴더에 풀고 VS Code에서 해당 폴더를 연다.
2. Windows에서 Python과 uv 실행을 확인한다.
3. `tools/check_starter.py`로 자료 구성을 검증한다.
4. 프로젝트 루트에서 Claude Code를 실행하고 위의 첫 지시문을 전달한다.
5. T001부터 의존 순서대로 진행한다. 지금 포함된 코드는 게임 구현이 아니라 시작용 구조다.
6. 단계별 완성본을 남기되, 최종 목표를 6개 레시피나 3명 손님으로 축소하지 않는다.
