from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class SkillMetadata:
    name: str
    description: str
    path: Path


def parse_skill_frontmatter(skill_path: Path) -> SkillMetadata | None:
    """Parse YAML frontmatter from SKILL.md"""
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return None

    content = skill_file.read_text()

    # Split frontmatter from content (between --- markers)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            return SkillMetadata(
                name=frontmatter.get("name", skill_path.name),
                description=frontmatter.get("description", "No description"),
                path=skill_path,
            )
    return None


def discover_skills(skills_dir: Path) -> list[SkillMetadata]:
    """Find all skills in the skills directory"""
    skills = []
    if not skills_dir.exists():
        return skills

    for item in skills_dir.iterdir():
        if item.is_dir():
            metadata = parse_skill_frontmatter(item)
            if metadata:
                skills.append(metadata)
    return skills


def load_skill_instructions(skill_name: str, skills_dir: Path) -> str:
    """Load the full SKILL.md content (without frontmatter)"""
    skill_path = skills_dir / skill_name / "SKILL.md"
    if not skill_path.exists():
        return f"Skill '{skill_name}' not found."

    content = skill_path.read_text()

    # Remove frontmatter, return just the markdown
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


def build_skills_prompt(skills: list[SkillMetadata]) -> str:
    """Build the Level 1 prompt showing available skills"""
    lines = ["## Available Skills\n"]
    for skill in skills:
        lines.append(f"- **{skill.name}**: {skill.description}")
    lines.append(
        "\nUse `load_skill(skill_name)` to get detailed instructions for a skill."
    )
    return "\n".join(lines)
