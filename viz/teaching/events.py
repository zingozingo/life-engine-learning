"""Event-level teaching content.

Maps (level, event_type) to EventTeaching instances with templated
level_insight fields. Templates use {placeholders} filled from real
session data by the insight engine.
"""

from .models import EventTeaching, FourQuestions

# Template placeholders:
# {system_tokens} — measured system prompt tokens
# {tool_tokens} — measured tool definition tokens
# {total_input} — verified total input tokens
# {total_output} — verified total output tokens
# {input_pct} — computed input percentage
# {skill_count} — counted skills loaded

EVENT_TEACHING: dict[tuple[int, str], EventTeaching] = {
    (1, "prompt_composed"): EventTeaching(
        title="System Prompt Composed",
        what="All skills and instructions packed into one system prompt",
        why="At Level 1, everything goes in the suitcase every time — there's no mechanism to select what's relevant",
        four_questions=FourQuestions(
            q1_who_decides="Nobody — all content is hardcoded, no selection occurs",
            q2_what_visible="Every skill, every instruction, every constraint — always",
            q3_blast_radius="Competing instructions may confuse the LLM. Irrelevant context dilutes focus",
            q4_human_involved="Human authored the prompt once. No per-query control",
        ),
        decision_maker="code",
        level_insight_template="System prompt: {system_tokens:,} tokens with {skill_count} skills. This is the monolith tax — paid on every query. At Level 2, progressive disclosure loads only what's needed.",
        concepts_demonstrated=["monolith_tax", "suitcase_model"],
    ),
    (1, "tool_registered"): EventTeaching(
        title="Tool Registered",
        what="Tool definition added to the API call",
        why="Every tool the LLM might need is registered, whether this query will use it or not",
        four_questions=FourQuestions(
            q1_who_decides="Code registers all tools unconditionally",
            q2_what_visible="All tool definitions — the LLM sees every available action",
            q3_blast_radius="More tools = more tokens + more chances the LLM picks the wrong one",
            q4_human_involved="Human defined the tools. No per-query filtering",
        ),
        decision_maker="code",
        level_insight_template="Tool definitions: {tool_tokens:,} tokens across all tools. At Level 2, generic tools replace endpoint-specific ones — fewer definitions, same capabilities. At Level 3, only route-relevant tools are registered.",
        concepts_demonstrated=["monolith_tax", "token_cost"],
    ),
    (1, "tool_called"): EventTeaching(
        title="Tool Executed",
        what="The LLM chose to call a tool and received results",
        why="The LLM selected this tool from all available options based on the query",
        four_questions=FourQuestions(
            q1_who_decides="LLM decides which tool to call and with what parameters",
            q2_what_visible="Tool results are added to context for the next round — the suitcase gets heavier",
            q3_blast_radius="Wrong tool call wastes a round trip. Results add to context for all subsequent rounds",
            q4_human_involved="No human checkpoint between tool selection and execution",
        ),
        decision_maker="llm",
        level_insight_template="Tool call added results to context. Total input now {total_input:,} tokens. The suitcase gets heavier with each round.",
        concepts_demonstrated=["suitcase_model", "token_cost"],
    ),
    (1, "api_call"): EventTeaching(
        title="API Round Trip",
        what="Complete request/response cycle with Claude",
        why="Each round sends the full suitcase — system prompt, tools, conversation history, and any tool results",
        four_questions=FourQuestions(
            q1_who_decides="Code decides when to make API calls. LLM decides if more rounds are needed",
            q2_what_visible="Everything from all prior rounds plus new tool results",
            q3_blast_radius="Each round compounds cost — input tokens grow with conversation history",
            q4_human_involved="No human checkpoint between rounds in a multi-round exchange",
        ),
        decision_maker="code",
        level_insight_template="Round trip: {total_input:,} input + {total_output:,} output tokens. Input is {input_pct:.0f}% of total — the suitcase weighs far more than the postcard back.",
        concepts_demonstrated=["input_dominance", "suitcase_model"],
    ),
    (1, "skill_loaded"): EventTeaching(
        title="Skill Content Loaded",
        what="Skill instructions embedded in system prompt",
        why="At Level 1, all skills are loaded unconditionally — there's no loading mechanism, just hardcoded content",
        four_questions=FourQuestions(
            q1_who_decides="Nobody decides — all skills are always present",
            q2_what_visible="Full skill text for every domain, regardless of query relevance",
            q3_blast_radius="Irrelevant skills waste tokens and may confuse routing",
            q4_human_involved="Human authored skill content. No per-query selection",
        ),
        decision_maker="code",
        level_insight_template="All {skill_count} skills loaded regardless of query. At Level 2, only the relevant skill's details get loaded on demand.",
        concepts_demonstrated=["monolith_tax", "token_cost"],
    ),
    (1, "error"): EventTeaching(
        title="Error Occurred",
        what="Something went wrong during processing",
        why="Errors at Level 1 have maximum blast radius — no isolation, no fallback routing",
        four_questions=FourQuestions(
            q1_who_decides="Nobody — errors propagate uncontrolled",
            q2_what_visible="Error details added to context, consuming tokens",
            q3_blast_radius="Full blast radius — no route isolation, no graceful degradation",
            q4_human_involved="Human sees error in response. No recovery mechanism",
        ),
        decision_maker="code",
        level_insight_template="Error with full blast radius. At Level 3, classifier-based routing contains errors to a single route. At Level 4, confidence-driven fallbacks can recover gracefully.",
        concepts_demonstrated=["token_cost"],
    ),
}

# Events that don't exist at L1 but will at higher levels — registered here
# so the framework knows about them. They have no L1 teaching content.
FUTURE_EVENTS: dict[str, dict] = {
    "classifier_decision": {
        "min_level": 3,
        "concepts": ["explicit_routing", "lowest_cost_decider"],
    },
    "proactive_fetch": {
        "min_level": 4,
        "concepts": ["proactive_reactive", "confidence_framework"],
    },
}
