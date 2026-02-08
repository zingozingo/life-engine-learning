"""Annotation engine for Four Questions framework.

Generates dynamic explanations for each event type at each level.
This is the brain behind the dashboard's educational content.
"""

from dataclasses import dataclass, asdict


@dataclass
class EventAnnotation:
    """Four Questions annotation for an event type."""

    title: str  # Human-readable event title
    what: str  # What is happening in plain English
    why: str  # Why this happens at this level
    q1_who_decides: str  # Who made this decision and why
    q2_what_visible: str  # What the LLM can see at this point
    q3_blast_radius: str  # What could go wrong, severity
    q4_human_involved: str  # Where/whether human is involved
    decision_maker: str  # "code" | "llm" | "human"
    level_insight: str  # What changes about this at other levels

    def to_dict(self) -> dict:
        return asdict(self)


# Level 1 annotations - the monolith
LEVEL_1_ANNOTATIONS: dict[str, EventAnnotation] = {
    "prompt_composed": EventAnnotation(
        title="System Prompt Built",
        what="The application assembled the full system prompt with ALL skill instructions baked in — weather, flights, hotels, activities, currency, visa, and packing. Every query gets this entire prompt regardless of what was asked.",
        why="Level 1 is the monolith — there's no routing or filtering. The simplest possible approach: give the LLM everything and let it figure out what's relevant.",
        q1_who_decides="CODE decided to load all skills. There was no decision about WHICH skills — they all load, every time. No classifier, no routing.",
        q2_what_visible="The LLM will see all 7 skill instruction sets (~3,000 tokens) plus all tool definitions. When you ask 'What's the weather in Tokyo?', the LLM also sees flight booking instructions, visa rules, hotel search guides, etc. — none of which are relevant.",
        q3_blast_radius="LOW direct risk — a bloated prompt doesn't break anything. But it has costs: higher token usage (you pay for ~3,000 tokens of irrelevant instructions every query), and the LLM occasionally follows the wrong skill's instructions.",
        q4_human_involved="None. The human chose to start Level 1 and typed a query. Everything else is automatic.",
        decision_maker="code",
        level_insight="At Level 2, only skill SUMMARIES load here (~200 tokens). At Level 3, a classifier runs first and only the RELEVANT skill loads. By Level 4, relevant data may already be pre-fetched and injected into this prompt.",
    ),
    "tool_registered": EventAnnotation(
        title="Tool Made Available",
        what="A tool was registered with the LLM, meaning the LLM can choose to call it during this query. The tool's function signature and description are added to the prompt.",
        why="Level 1 registers ALL tools on EVERY query. The LLM sees http_fetch and mock_api_fetch whether it needs them or not. Each tool definition costs tokens in the prompt.",
        q1_who_decides="CODE decided to register this tool. The LLM had no say — all tools are always registered at Level 1.",
        q2_what_visible="The LLM sees the tool's name, parameter types, and description. This tells it what the tool can do and how to call it. Even for a simple packing list question where no tools are needed, the LLM still sees all tool definitions.",
        q3_blast_radius="LOW — registering an extra tool wastes tokens (~20-50 per tool) and slightly increases the chance the LLM calls a tool unnecessarily.",
        q4_human_involved="None.",
        decision_maker="code",
        level_insight="At Level 3, tools are SCOPED per route — a creative packing query would register zero tools, saving tokens and preventing unnecessary tool calls.",
    ),
    "llm_request": EventAnnotation(
        title="Request Sent to LLM",
        what="The full request was sent to the Claude API. This includes the system prompt, all tool definitions, the conversation history, and the user's message. This is the moment where tokens become dollars.",
        why="Every agent call eventually sends a request to the LLM. The total token count here reflects everything loaded in previous steps — prompt size + tool definitions + conversation history.",
        q1_who_decides="CODE decided to send this request. The timing, model choice, and contents were all determined by your application code.",
        q2_what_visible="The LLM now sees EVERYTHING: the full system prompt (all skills), all tool definitions, the complete conversation history, and the current user message. This is the LLM's entire universe for making decisions.",
        q3_blast_radius="MEDIUM — this is where cost accumulates. A bloated prompt means every query costs more. At Level 1, even 'Convert 500 USD to Euros' sends ~3,000 tokens of irrelevant instructions.",
        q4_human_involved="None directly, but the human's original query is embedded in this request.",
        decision_maker="code",
        level_insight="The token count here is the key metric to watch across levels. Level 1 sends ~3,000+ tokens every time. Level 3 might send ~300 for a simple query. That's a 10x reduction for the same answer quality.",
    ),
    "tool_called": EventAnnotation(
        title="Tool Executed",
        what="The LLM decided to call a tool during its response generation. It chose which tool, what parameters to pass, and when in its reasoning to make the call. The tool ran and returned results.",
        why="The LLM read the skill instructions in the prompt and determined it needed external data to answer the question. For weather queries, the skill instructions tell the LLM to first geocode the city name, then fetch the forecast.",
        q1_who_decides="The LLM decided to call this tool — this is an IMPLICIT decision. The LLM read the instructions and chose to act. Your code didn't force this call.",
        q2_what_visible="The LLM sees the tool's parameter schema and its own reasoning so far. For sequential calls, the LLM also sees results of previous calls.",
        q3_blast_radius="LOW-MEDIUM — the API could timeout, return errors, or return unexpected data. The LLM might pass wrong parameters. However, these are read-only API calls with no side effects.",
        q4_human_involved="None — the LLM has full autonomy over tool calls at Level 1. There's no approval gate. This is appropriate because these are read-only data fetches with low blast radius.",
        decision_maker="llm",
        level_insight="At Level 4, high-confidence tool calls happen PROACTIVELY — your code calls the API before the LLM even starts, and injects the result into the prompt. This eliminates a round trip.",
    ),
    "llm_response": EventAnnotation(
        title="Response Generated",
        what="The LLM finished generating its response. This includes all the text the user sees, incorporating any data from tool calls. The duration reflects the total time from request to complete response.",
        why="This is the final output of the agent pipeline for this query. The response quality depends on everything that came before: the instructions in the prompt, the tools available, the data fetched.",
        q1_who_decides="The LLM decided what to say and how to format it, guided by the skill instructions in the prompt. CODE received the response and will display it to the user.",
        q2_what_visible="The LLM had access to everything from the llm_request step PLUS any tool results. This is the maximum context the LLM had for this query.",
        q3_blast_radius="LOW — a bad response wastes the user's time but has no system side effects. The user can simply ask again or rephrase.",
        q4_human_involved="The human receives this response and decides what to do next. This is the 'Review at End' pattern — the agent ran autonomously, and the human evaluates the output.",
        decision_maker="code",
        level_insight="Response quality should be similar across levels. What changes is the COST and SPEED of getting here. Level 1 pays a token tax on every query. Level 4 gets the same quality with fewer tokens.",
    ),
    "classifier_decision": EventAnnotation(
        title="Query Classified",
        what="A lightweight classifier analyzed the user's query and determined which category it belongs to. This classification drives all downstream decisions.",
        why="This event doesn't occur at Level 1 — it's shown here for reference. At Level 3+, explicit classification replaces implicit LLM routing.",
        q1_who_decides="CODE decided the category, using a small/cheap LLM or rule-based logic. This is an EXPLICIT decision — deterministic and predictable.",
        q2_what_visible="The classifier sees ONLY the user's query (~50 tokens). It doesn't see skill details, tool definitions, or conversation history.",
        q3_blast_radius="MEDIUM — a misclassification means the wrong skills and tools load. The LLM gets the wrong context and may give a bad answer.",
        q4_human_involved="None — classification is automatic. But a human designed the categories and routing rules.",
        decision_maker="code",
        level_insight="This event doesn't exist at Levels 1-2. It's unique to Level 3+ where code takes control of routing.",
    ),
    "proactive_fetch": EventAnnotation(
        title="Data Pre-Fetched",
        what="Based on classification, code determined with high confidence that specific data would be needed and fetched it BEFORE the LLM started generating.",
        why="This event doesn't occur at Level 1 — it's shown here for reference. At Level 4+, proactive fetching eliminates round trips for predictable needs.",
        q1_who_decides="CODE decided to pre-fetch this data. The LLM didn't ask for it — code predicted the need based on classification.",
        q2_what_visible="The LLM will see this data as part of its prompt, as if it were always there. It doesn't know the data was fetched proactively.",
        q3_blast_radius="LOW-MEDIUM — if classification was wrong, you fetched data for nothing (wasted API call and tokens). But the cost is bounded.",
        q4_human_involved="None.",
        decision_maker="code",
        level_insight="This event doesn't exist at Levels 1-3. Level 4 introduces the proactive/reactive split based on confidence.",
    ),
    "skill_loaded": EventAnnotation(
        title="Skill Instructions Loaded",
        what="The detailed instructions for a specific skill were loaded into the conversation, giving the LLM the full 'recipe' for handling this query type.",
        why="This event doesn't occur at Level 1 (all skills pre-loaded). At Level 2, the LLM calls load_skill to get details on demand.",
        q1_who_decides="At Level 2, the LLM decides which skill to load. At Level 3+, CODE loads the right skills based on classification.",
        q2_what_visible="After loading, the LLM sees the full skill detail. It does NOT see details of skills it didn't load.",
        q3_blast_radius="MEDIUM — loading the wrong skill means wrong context. Skipping the load means answering from training data alone.",
        q4_human_involved="None.",
        decision_maker="llm",
        level_insight="At Level 1, this event is implicit (all skills always loaded). At Level 2, it's an LLM decision. At Level 3+, it's a code decision.",
    ),
    "error": EventAnnotation(
        title="Error Occurred",
        what="Something went wrong during execution — an API call failed, a tool threw an exception, or the LLM returned an unexpected response.",
        why="Errors are inevitable in any system that makes external calls. The question isn't whether errors happen, but how they're handled.",
        q1_who_decides="Nobody 'decided' for an error to happen. What matters is who decides how to HANDLE it. At Level 1, error handling is minimal.",
        q2_what_visible="The LLM sees the error message and can try to recover — use different parameters, try a different tool, or explain to the user what went wrong.",
        q3_blast_radius="Depends on the error. API timeout → LOW. Malformed data → MEDIUM. Unhandled exception → HIGH (query fails completely).",
        q4_human_involved="At Level 1, the human sees the error in the response and can retry. In production, errors trigger alerts.",
        decision_maker="code",
        level_insight="Error handling improves with architecture maturity. Level 3 can fall back to a broader route. Level 4 can skip failed proactive fetches.",
    ),
}

# Level info for API
LEVEL_INFO = {
    1: {
        "number": 1,
        "name": "Monolith",
        "description": "Everything hardcoded in one prompt",
        "implemented": True,
    },
    2: {
        "number": 2,
        "name": "Skills + Tools",
        "description": "Progressive disclosure via load_skill",
        "implemented": False,
    },
    3: {
        "number": 3,
        "name": "Classifier",
        "description": "Explicit routing via query classification",
        "implemented": False,
    },
    4: {
        "number": 4,
        "name": "Adaptive",
        "description": "Proactive + reactive data fetching",
        "implemented": False,
    },
    5: {
        "number": 5,
        "name": "MCP",
        "description": "Distributed tool servers",
        "implemented": False,
    },
}


def get_annotations(level: int) -> dict[str, dict]:
    """Get annotations for a given level.

    Args:
        level: Engine level (1-5)

    Returns:
        Dict mapping event_type to annotation dict
    """
    if level == 1:
        return {k: v.to_dict() for k, v in LEVEL_1_ANNOTATIONS.items()}

    # Future levels will have their own annotation dicts
    # For now, return Level 1 annotations as a base
    # Level 2+ will override specific fields
    return {k: v.to_dict() for k, v in LEVEL_1_ANNOTATIONS.items()}


def get_annotation_for_event(event_type: str, level: int) -> dict | None:
    """Get annotation for a specific event type at a level.

    Args:
        event_type: The event type (e.g., "prompt_composed")
        level: Engine level (1-5)

    Returns:
        Annotation dict or None if not found
    """
    annotations = get_annotations(level)
    return annotations.get(event_type)


def get_level_info(level: int) -> dict | None:
    """Get info about a specific level.

    Args:
        level: Engine level (1-5)

    Returns:
        Level info dict or None if not found
    """
    return LEVEL_INFO.get(level)


def get_all_levels() -> list[dict]:
    """Get info about all levels.

    Returns:
        List of level info dicts
    """
    return list(LEVEL_INFO.values())
