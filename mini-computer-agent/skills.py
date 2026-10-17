"""SKILLS: SKILL.md files matched to the task and injected into the prompt.

A skill is not code that runs. It is a short instruction file that is
keyword-matched against the task; the best match is injected into the
brain's prompt as guidance. Same pattern as coding-agent/limbs/skills.

File format (skills/<name>/SKILL.md):

    ---
    name: open-an-app
    description: Launch a desktop application and verify its window appeared
    when: open, launch, start, app
    ---

    # Open an app

    ## Steps
    1. Use open_app with the app's launch command
    2. ...
"""
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"


class Skill:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.parent.name
        self.description = ""
        self.when = []
        self.steps = []
        self._parse(path.read_text())

    def _parse(self, text: str):
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        body = text
        if m:
            body = text[m.end():]
            for line in m.group(1).splitlines():
                if ":" not in line:
                    continue
                key, val = line.split(":", 1)
                key, val = key.strip().lower(), val.strip()
                if key == "description":
                    self.description = val
                elif key == "when":
                    self.when = [w.strip().lower() for w in val.split(",")]
        in_steps = False
        for line in body.splitlines():
            s = line.strip()
            if s.lower().startswith("## steps"):
                in_steps = True
                continue
            if s.lower().startswith("## ") and in_steps:
                break
            if in_steps and s:
                self.steps.append(re.sub(r"^\d+\.\s*", "", s))

    def score(self, task: str) -> float:
        """How well this skill matches the task (0..1)."""
        t = task.lower()
        sc = 0.0
        if self.name.replace("-", " ") in t:
            sc += 0.5
        for w in self.when:
            if w and w in t:
                sc += 0.25
        for word in self.description.lower().split():
            if len(word) > 4 and word in t:
                sc += 0.05
        return min(sc, 1.0)


def load_skills() -> list:
    if not SKILLS_DIR.exists():
        return []
    return [Skill(p) for p in sorted(SKILLS_DIR.glob("*/SKILL.md"))]


def match_skills(task: str, loaded=None) -> list:
    """Skills sorted best-match first."""
    skills = loaded if loaded is not None else load_skills()
    return sorted(skills, key=lambda s: s.score(task), reverse=True)


def skills_prompt(task: str) -> str:
    """Guidance text for the best-matching skill, or '' if nothing matches."""
    ranked = match_skills(task)
    if not ranked or ranked[0].score(task) <= 0:
        return ""
    s = ranked[0]
    steps = "\n".join(f"  {i + 1}. {st}" for i, st in enumerate(s.steps[:5]))
    return f"skill '{s.name}' matched this task:\n{steps}"
