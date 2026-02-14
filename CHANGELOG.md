# Changelog

## [Unreleased] - 2026-02-13

### Added
- Level 2 Skills Engine (engines/level2_skills.py) — 577 lines, 6 tools, progressive disclosure
- Three-level progressive disclosure: metadata → SKILL.md body → references/ files
- Time/date skill with native get_current_datetime() tool (Python stdlib, no external deps)
- Skill discovery tools: load_skill, list_skill_files, read_skill_file
- Reference files for 3 skills: weather/references/api_reference.md, visa/references/response_guide.md, activities/references/category_guide.md
- build_skill_menu(), list_skill_files(), read_skill_file() in shared/skill_loader.py
- run_level_2() in main.py with `make chat level=2` support
- Decisions #34-#39 documenting L2 architectural choices

### Changed
- L2 system prompt: 479 tokens vs L1's 4,106 (88% reduction)
- L1 engine now registers get_current_datetime as third tool
- SKILL_LOADED events carry disclosure_level (2 or 3) in data dict
- concepts.py L2 implemented flag flipped to True
- ARCHITECTURE_SPEC.md updated with L2 implementation details, expanded skills/tools tables

---

## [Unreleased] - 2026-02-11

### Added
- 4+3 architecture (4 levels + 3 overlays) replacing original 5-level model
- Data-driven teaching layer (viz/teaching/) with concept registry, insight generators, comparison engine
- Decorator registries (@insight, @comparison) for extensible educational content
- Template-based annotations with real token measurements — zero hardcoded numbers
- Teaching extensibility skill (skills/teaching/SKILL.md)
- ARCHITECTURE_SPEC.md as primary specification document
- FOUR_QUESTIONS.md decision framework
- AGENTS.md execution orchestration roadmap

### Changed
- annotations.py reduced to 25-line backward-compatible shim
- Dashboard wired to dynamic teaching layer with real session data
- Level 5 (MCP) removed from UI, MCP becomes infrastructure overlay
- Level constraint updated from 1-5 to 1-4 project-wide

### Removed
- engines/level5_mcp.py (MCP is now an overlay, not a level)
- 217 lines of hardcoded educational prose from annotations.py
