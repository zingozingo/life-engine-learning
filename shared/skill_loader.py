"""Skill discovery and loading utilities.

Reads skill definitions from the skills/ directory and builds prompts.
"""

from pathlib import Path

import yaml

from shared.models import SkillMetadata


def load_all_skills(skills_dir: str = "skills") -> dict[str, SkillMetadata]:
    """Load metadata for all skills from their SKILL.md frontmatter.

    Args:
        skills_dir: Path to the skills directory

    Returns:
        Dict mapping skill name to SkillMetadata
    """
    skills_path = Path(skills_dir)
    if not skills_path.exists():
        return {}

    skills = {}
    for skill_dir in skills_path.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        content = skill_file.read_text()
        metadata = _parse_frontmatter(content)
        if metadata:
            # Use folder name as key, but name from frontmatter for display
            skills[skill_dir.name] = SkillMetadata(
                name=metadata.get("name", skill_dir.name),
                description=metadata.get("description", "No description"),
                status=metadata.get("status", "active"),
            )

    return skills


def load_skill_detail(skill_name: str, skills_dir: str = "skills") -> str:
    """Load the full markdown body of a skill (everything after frontmatter).

    Args:
        skill_name: Name of the skill (directory name)
        skills_dir: Path to the skills directory

    Returns:
        Markdown content of the skill, or error message if not found
    """
    skill_file = Path(skills_dir) / skill_name / "SKILL.md"
    if not skill_file.exists():
        return f"Error: Skill '{skill_name}' not found."

    content = skill_file.read_text()
    return _extract_body(content)


def build_monolith_prompt(skills_dir: str = "skills") -> str:
    """Build the Level 1 monolith system prompt with ALL skills.

    This creates the "everything always loaded" prompt that demonstrates
    the bloat problem we're solving in later levels.

    Args:
        skills_dir: Path to the skills directory

    Returns:
        Complete system prompt with persona and all skill instructions
    """
    skills = load_all_skills(skills_dir)

    # Build the persona intro
    prompt_parts = [
        "# Travel Concierge Assistant",
        "",
        "You are an expert travel concierge assistant. You help users plan trips, "
        "find flights and hotels, check weather, convert currencies, understand visa "
        "requirements, and create packing lists.",
        "",
        "You have access to the following tools:",
        "- `http_fetch(url)`: Fetch data from any URL (used for weather API)",
        "- `mock_api_fetch(endpoint, params)`: Query travel data APIs (flights, hotels, etc.)",
        "- `get_current_datetime(timezone)`: Get current date, time, and day of week",
        "",
        "Below are detailed instructions for each skill you can perform.",
        "",
        "---",
        "",
    ]

    # Add each skill's full instructions
    for skill_name in sorted(skills.keys()):
        skill_detail = load_skill_detail(skill_name, skills_dir)
        prompt_parts.append(skill_detail)
        prompt_parts.append("")
        prompt_parts.append("---")
        prompt_parts.append("")

    return "\n".join(prompt_parts)


def _parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Parsed frontmatter dict, or None if no frontmatter
    """
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None


def _extract_body(content: str) -> str:
    """Extract markdown body (everything after frontmatter).

    Args:
        content: Full markdown file content

    Returns:
        Body content without frontmatter
    """
    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    return parts[2].strip()


def build_skill_menu(skills_dir: str = "skills") -> str:
    """Build the Level 2 skill menu with summaries only.

    Returns a formatted string listing all skills with name and description,
    preceded by instructions on how to load skill details.

    Args:
        skills_dir: Path to the skills directory

    Returns:
        Formatted skill menu for the L2 system prompt
    """
    skills = load_all_skills(skills_dir)

    lines = [
        "You have access to the following skills. To learn more about a skill "
        "before using it, call load_skill(skill_name). To see what reference "
        "files a skill has, call list_skill_files(skill_name).",
        "",
    ]
    for skill_name in sorted(skills.keys()):
        meta = skills[skill_name]
        lines.append(f"- **{meta.name}**: {meta.description}")

    return "\n".join(lines)


def list_skill_files(skills_dir: str, skill_name: str) -> list[str]:
    """List reference files available for a skill.

    Args:
        skills_dir: Path to the skills directory
        skill_name: Name of the skill (directory name)

    Returns:
        List of relative file paths (excluding SKILL.md), or empty list
        if skill has no reference files or doesn't exist
    """
    skill_path = Path(skills_dir) / skill_name
    if not skill_path.is_dir():
        return []

    files = []
    for f in sorted(skill_path.rglob("*")):
        if f.is_file() and f.name != "SKILL.md":
            files.append(str(f.relative_to(skill_path)))
    return files


def read_skill_file(skills_dir: str, skill_name: str, file_path: str) -> str:
    """Read a specific file from within a skill directory.

    Args:
        skills_dir: Path to the skills directory
        skill_name: Name of the skill (directory name)
        file_path: Relative path within the skill directory

    Returns:
        File contents, or error message if not found or invalid path
    """
    skill_path = Path(skills_dir) / skill_name
    if not skill_path.is_dir():
        return f"Error: Skill '{skill_name}' not found."

    # Security: prevent directory traversal
    target = (skill_path / file_path).resolve()
    if not str(target).startswith(str(skill_path.resolve())):
        return f"Error: Invalid file path '{file_path}'."

    if not target.is_file():
        return f"Error: File '{file_path}' not found in skill '{skill_name}'."

    return target.read_text()
