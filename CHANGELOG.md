# Changelog

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
