"""Concept registry — all level metadata lives here.

Source of truth for what each level teaches, what forces the next level,
and the Four Questions at the level-wide scope. Content derived from
docs/ARCHITECTURE_SPEC.md.
"""

from .models import Concept, ForcingFunction, FourQuestions, LevelConcept

LEVEL_CONCEPTS: dict[int, LevelConcept] = {
    1: LevelConcept(
        number=1,
        name="The Monolith",
        one_liner="Everything always present. Nobody manages context.",
        who_curates="Nobody — everything is always present",
        description="All skills and tools hardcoded in one prompt. Every query pays full cost.",
        implemented=True,
        teaches=[
            Concept(
                id="token_cost",
                label="What context costs",
                description="Tokens as a finite resource with real dollar costs",
            ),
            Concept(
                id="monolith_tax",
                label="The monolith tax",
                description="Fixed overhead of system prompt + tools paid every query",
            ),
            Concept(
                id="input_dominance",
                label="Input dominates output",
                description="~95%+ of cost is input tokens in tool-using queries",
            ),
            Concept(
                id="suitcase_model",
                label="The suitcase mental model",
                description="Every API call packs everything and sends it",
            ),
        ],
        forces_next=ForcingFunction(
            trigger="Prompt exceeds ~3-4k tokens, LLM confused by competing instructions",
            observable="Adding any capability grows the prompt linearly",
        ),
        four_questions=FourQuestions(
            q1_who_decides="LLM decides everything — which skill, which tool",
            q2_what_visible="Everything — all skills, all tools, all instructions, always",
            q3_blast_radius="Wrong instructions followed, irrelevant tools called, confused by competing context",
            q4_human_involved="Bookend only — start (query) and end (response)",
        ),
    ),
    2: LevelConcept(
        number=2,
        name="Skills + Generic Tools",
        one_liner="Progressive disclosure. The LLM manages its own context.",
        who_curates="The LLM — reads skill menu, decides what to load",
        description="Skills broken into summaries (always present) and details (loaded on demand). Generic tools replace endpoint-specific functions.",
        implemented=True,
        teaches=[
            Concept(
                id="progressive_disclosure",
                label="Progressive disclosure",
                description="Separating what's available from what's loaded",
            ),
            Concept(
                id="generic_tools",
                label="Generic tool pattern",
                description="Tools as verbs, skills as nouns — the Swiss Army knife",
            ),
            Concept(
                id="agent_skills_spec",
                label="Agent Skills spec",
                description="Industry standard (agentskills.io) for skill packaging",
            ),
            Concept(
                id="token_scaling",
                label="Token scaling math",
                description="Tool definitions stay flat; only skill summaries scale linearly",
            ),
        ],
        forces_next=ForcingFunction(
            trigger="LLM loads wrong skill for ambiguous queries, inconsistent behavior",
            observable="Implicit routing is unreliable when queries span domains",
        ),
        four_questions=FourQuestions(
            q1_who_decides="LLM decides what to load (reads menu, picks skill). Code decides tool implementations",
            q2_what_visible="Skill summaries always. Full details on demand. Generic tool definitions (flat count)",
            q3_blast_radius="Wrong skill loaded, unnecessary loading, skipped loading when needed",
            q4_human_involved="Same bookend control as L1",
        ),
    ),
    3: LevelConcept(
        number=3,
        name="Query Classification",
        one_liner="Your code decides what the LLM sees. Explicit routing.",
        who_curates="Your code — classifier routes to pre-configured context",
        description="Lightweight classifier examines query before main agent. Classification determines which skills and tools are loaded.",
        implemented=False,
        teaches=[
            Concept(
                id="explicit_routing",
                label="Explicit vs implicit routing",
                description="Classifier is cheap and deterministic; LLM is expensive and non-deterministic",
            ),
            Concept(
                id="lowest_cost_decider",
                label="Lowest-cost decider principle",
                description="Push decisions to the cheapest reliable component",
            ),
            Concept(
                id="token_scoping",
                label="Token scoping",
                description="Zero tools for creative queries, full toolset for technical queries",
            ),
            Concept(
                id="route_configuration",
                label="Route configuration as code",
                description="Deterministic mapping from classification to context",
            ),
        ],
        forces_next=ForcingFunction(
            trigger="LLM always calls same tool first in certain routes — predictable fetches",
            observable="Paying for round trips the system could pre-empt",
        ),
        four_questions=FourQuestions(
            q1_who_decides="Code decides what to load (classifier routes). LLM decides how to use it",
            q2_what_visible="Only skills and tools for the classified route. No menu, no irrelevant context",
            q3_blast_radius="Misclassification → wrong route → wrong context. Contained to one query",
            q4_human_involved="Bookend + classification checkpoint possible",
        ),
    ),
    4: LevelConcept(
        number=4,
        name="Adaptive Context Engineering",
        one_liner="Your code manages context as a resource with a budget.",
        who_curates="Your code, intelligently — confidence-driven proactive/reactive split",
        description="Classification output is a confidence signal. High-confidence needs pre-fetched. Uncertain needs stay reactive. Active context budget management.",
        implemented=False,
        teaches=[
            Concept(
                id="proactive_reactive",
                label="Proactive vs reactive loading",
                description="Confidence as a decision signal for what to pre-fetch vs leave available",
            ),
            Concept(
                id="context_budget",
                label="Context budget awareness",
                description="Context rot is real — performance degrades as context grows",
            ),
            Concept(
                id="long_horizon",
                label="Long-horizon context management",
                description="Compaction, structured notes, selective retention over time",
            ),
            Concept(
                id="confidence_framework",
                label="Confidence framework",
                description="~100% certain = proactive, ~50% = reactive, ~0% = not loaded",
            ),
        ],
        forces_next=None,  # This is the architectural ceiling
        four_questions=FourQuestions(
            q1_who_decides="Code decides proactive/reactive split. LLM decides within reactive scope",
            q2_what_visible="Pre-loaded data for high-confidence needs + available tools for uncertain needs",
            q3_blast_radius="Over-fetching wastes tokens. Under-fetching misses data. Compaction loses subtle context",
            q4_human_involved="Checkpoints at classification, after pre-fetch, and at session boundaries",
        ),
    ),
}
