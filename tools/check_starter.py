"""Validate handoff integrity, not gameplay. Uses only the Python standard library."""

import ast
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    required = [
        "CLAUDE.md",
        "README.md",
        "START_HERE.md",
        "docs/DECISIONS.md",
        "docs/STATUS.md",
        "docs/tasks/INDEX.md",
        "docs/REQUIREMENTS.md",
        "docs/ART_DIRECTION.md",
        "pyproject.toml",
        ".env.example",
    ]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    try:
        tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"Invalid project TOML: {exc}")
    try:
        tasks = json.loads((root / "docs/tasks/catalog.json").read_text(encoding="utf-8"))["tasks"]
    except (OSError, ValueError, KeyError) as exc:
        return errors + [f"Invalid task catalogue: {exc}"], {}
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate task IDs")
    req_text = (root / "docs/REQUIREMENTS.md").read_text(encoding="utf-8")
    reqs = set(re.findall(r"^\| (R\d{3}) \|", req_text, flags=re.M))
    covered: set[str] = set()
    seen: set[str] = set()
    index_text = (root / "docs/tasks/INDEX.md").read_text(encoding="utf-8")
    for t in tasks:
        for dep in t["dependencies"]:
            if dep not in seen:
                errors.append(f"{t['id']} has unknown, cyclic or later dependency {dep}")
        seen.add(t["id"])
        path = root / t["file"]
        if not path.is_file():
            errors.append(f"Missing task file {t['file']}")
        else:
            task_text = path.read_text(encoding="utf-8")
            for heading in ["## Goal and work", "## Acceptance and verification", "## Evidence"]:
                if heading not in task_text:
                    errors.append(f"{t['id']} missing {heading}")
            for req in t["requirements"]:
                if req not in task_text:
                    errors.append(f"{t['id']} file missing mapped requirement {req}")
        if f"[{t['id']}]" not in index_text:
            errors.append(f"Task index missing {t['id']}")
        for req in t["requirements"]:
            if req not in reqs:
                errors.append(f"{t['id']} references unknown requirement {req}")
            covered.add(req)
    for req in reqs - covered:
        errors.append(f"Uncovered requirement {req}")
    for path in root.rglob("*.json"):
        if any(p in {".venv", ".git", "__pycache__"} for p in path.parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid JSON {path.relative_to(root)}: {exc}")
    for path in root.rglob("*.md"):
        if any(p in {".venv", ".git"} for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("https://", "http://", "#", "mailto:")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).exists():
                errors.append(f"Broken Markdown link {path.relative_to(root)}: {target}")
    for path in (root / "src").rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Python syntax: {exc}")
    en: dict[str, str] = {}
    try:
        en = json.loads((root / "content/locales/en.json").read_text(encoding="utf-8"))
        ko = json.loads((root / "content/locales/ko.json").read_text(encoding="utf-8"))
        if en.keys() != ko.keys():
            errors.append("Locale key mismatch")
        if any(not isinstance(v, str) or not v.strip() for v in [*en.values(), *ko.values()]):
            errors.append("Empty/non-string locale values")
        ingredients = json.loads(
            (root / "content/examples/ingredients.json").read_text(encoding="utf-8")
        )["ingredients"]
        ingredient_ids = {i["ingredient_id"] for i in ingredients}
        if len(ingredient_ids) != len(ingredients):
            errors.append("Duplicate example ingredient IDs")
        recipe = json.loads((root / "content/examples/recipe.json").read_text(encoding="utf-8"))
        for addition in recipe["ingredients"]:
            if addition["ingredient_id"] not in ingredient_ids:
                errors.append("Example recipe has unknown ingredient")
            if type(addition["volume_ul"]) is not int or addition["volume_ul"] <= 0:
                errors.append("Example recipe quantity invalid")
        for ingredient in ingredients:
            if not 0 <= ingredient["abv_fraction"] <= 1:
                errors.append("Invalid example ABV")
        character = json.loads(
            (root / "content/examples/character.json").read_text(encoding="utf-8")
        )
        if character["age_years"] < 18:
            errors.append("Example patron is not adult")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Example contract failure: {exc}")
    for name in [
        "palette_reference.png",
        "environment_reference.png",
        "characters_props_reference.png",
    ]:
        image = root / "references/art" / name
        if not image.is_file() or image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append(f"Missing/invalid PNG reference: {name}")
    if (root / ".env").exists():
        errors.append("Starter bundle must not contain a real .env")
    return errors, {"tasks": len(tasks), "requirements": len(reqs), "locale_keys": len(en)}


def main() -> int:
    errors, counts = validate(ROOT)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: starter handoff integrity")
    print(json.dumps(counts, ensure_ascii=False))
    print("This does not verify gameplay, Windows IME, live AI or executable packaging.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
