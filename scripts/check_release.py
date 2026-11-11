"""Check package metadata and links; optional license gate before publication."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator
import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-license", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    skill = root / "skills" / "paranoid"
    errors = []
    entry = (skill / "SKILL.md").read_text()
    metadata = yaml.safe_load(entry.split("---", 2)[1])
    if metadata.get("name") != skill.name or not metadata.get("description"):
        errors.append("Skill identity/description is invalid")
    if not re.fullmatch(r"\d+\.\d+\.\d+", metadata.get("metadata", {}).get("version", "")):
        errors.append("Skill version is missing or malformed")
    interface = yaml.safe_load((skill / "agents" / "openai.yaml").read_text())["interface"]
    if "$" + skill.name not in interface.get("default_prompt", ""):
        errors.append("Codex default prompt does not invoke this skill")
    if not 25 <= len(interface.get("short_description", "")) <= 64:
        errors.append("Codex short description has invalid length")
    Draft202012Validator.check_schema(json.loads((skill / "references" / "model.schema.json").read_text()))
    for document in root.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or not parsed.path:
                continue
            destination = (document.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f"Broken/nonportable link: {document.relative_to(root)} -> {target}")
    for model_path in (root / "examples").glob("*/model.json"):
        result = subprocess.run([sys.executable, "-B", str(skill / "scripts" / "validate_model.py"),
                                 str(model_path)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f"Example model failed validation: {model_path.relative_to(root)}: {result.stdout}{result.stderr}")
        model = json.loads(model_path.read_text())
        for source in model["scope"].get("sources", []):
            artifact = (model_path.parent / source["locator"]).resolve()
            if not artifact.is_relative_to(root) or not artifact.is_file():
                errors.append(f"Example source locator cannot be resolved: {source['locator']}")
            elif source["revision"] != "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest():
                errors.append(f"Example input digest mismatch: {artifact.relative_to(root)}")
    if args.require_license and not (root / "LICENSE").is_file():
        errors.append("Select and include LICENSE before publication")
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print("Package metadata, schema, relative references, example models, and input digests pass.")
        if not (root / "LICENSE").is_file():
            print("Publication remains pending: no license selected.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
