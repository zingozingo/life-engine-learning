#!/usr/bin/env python3
"""Verify token math across all logged sessions."""
import json
import sys
from pathlib import Path


def verify_session(filepath):
    """Verify a single session's token math."""
    session = json.loads(Path(filepath).read_text())
    query = session["query_text"]
    total_input = session.get("total_input_tokens", 0)
    total_output = session.get("total_output_tokens", 0)

    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print(f"Session totals: {total_input:,} in + {total_output:,} out = {(total_input+total_output):,}")
    print(f"{'='*70}")

    api_calls = [e for e in session["events"] if e["event_type"] == "api_call"]
    all_pass = True

    sum_input = 0
    sum_output = 0

    for call in api_calls:
        d = call["data"]
        round_num = d["round_number"]
        total_rounds = d.get("total_rounds", "?")
        input_tokens = d["input_tokens"]
        output_tokens = d["output_tokens"]
        sum_input += input_tokens
        sum_output += output_tokens

        print(f"\n  Round {round_num} of {total_rounds}: {input_tokens:,} in + {output_tokens:,} out")

        breakdown = d.get("input_breakdown", [])
        if breakdown:
            items_sum = 0
            verified_total = 0
            print("  Breakdown:")
            for item in breakdown:
                label = item.get("label", "?")
                tokens = item.get("tokens", item.get("tokens_est", 0)) or 0
                if item.get("is_real"):
                    verified_total = tokens
                    print(f"    [=] {label}: {verified_total:,} (verified)")
                elif item.get("is_metadata"):
                    # Metadata items (like clean_call verification) don't count towards sum
                    print(f"    [~] {label}: {tokens:,}")
                else:
                    items_sum += tokens
                    marker = (
                        "M"
                        if item.get("is_measured")
                        else "C" if item.get("is_computed") else "~"
                    )
                    print(f"    [{marker}] {label}: {tokens:,}")

            # Verify sum
            if verified_total > 0:
                diff = items_sum - verified_total
                status = (
                    "PASS" if diff == 0 else f"FAIL (off by {diff:+,})"
                )
                print(
                    f"  Math check: items sum = {items_sum:,}, verified total = {verified_total:,} -> {status}"
                )
                if diff != 0:
                    all_pass = False

    # Verify session totals
    print(f"\n  Aggregate check:")
    input_match = sum_input == total_input
    output_match = sum_output == total_output
    print(
        f"    Sum of round inputs: {sum_input:,} vs session total_input_tokens: {total_input:,} -> {'PASS' if input_match else 'FAIL'}"
    )
    print(
        f"    Sum of round outputs: {sum_output:,} vs session total_output_tokens: {total_output:,} -> {'PASS' if output_match else 'FAIL'}"
    )

    if not input_match or not output_match:
        all_pass = False

    # Verify breakdown split
    print(f"\n  Breakdown split check:")
    split_pass = verify_breakdown_split(session)
    if not split_pass:
        all_pass = False

    return all_pass


def verify_breakdown_split(session):
    """Verify that breakdown items correctly split history and user question.

    For Round 1:
    - If has history: prompt + tools + history + question = verified total
    - If no history: prompt + tools + question = verified total

    For Round 2+:
    - prompt + tools + [history] + question + tool_exchanges = verified total
    """
    api_calls = [e for e in session["events"] if e["event_type"] == "api_call"]
    if not api_calls:
        return True  # No API calls to verify

    all_pass = True
    seq = session.get("sequence", 1)

    for call in api_calls:
        d = call["data"]
        round_num = d["round_number"]
        breakdown = d.get("input_breakdown", [])

        if not breakdown:
            continue

        # Extract components
        verified_total = 0
        computed_sum = 0
        has_history = False
        has_question = False
        clean_call = None

        for item in breakdown:
            tokens = item.get("tokens", item.get("tokens_est", 0)) or 0
            label = item.get("label", "").lower()

            if item.get("is_real"):
                verified_total = tokens
            elif item.get("is_metadata"):
                if "clean call" in label:
                    clean_call = tokens
            else:
                computed_sum += tokens
                if "conversation history" in label:
                    has_history = True
                if "your question" in label:
                    has_question = True

        # Verify sum
        diff = computed_sum - verified_total
        if diff != 0:
            print(f"    [FAIL] Round {round_num}: breakdown sum={computed_sum:,} != verified={verified_total:,} (off by {diff:+,})")
            all_pass = False
        else:
            print(f"    [PASS] Round {round_num}: breakdown sum={computed_sum:,} = verified={verified_total:,}")

        # Verify split logic
        if round_num == 1:
            if seq == 1:
                # First query in conversation should NOT have history
                if has_history:
                    print(f"    [WARN] seq=1 Round 1 should not have history component")
            else:
                # Subsequent queries SHOULD have history
                if not has_history:
                    print(f"    [WARN] seq={seq} Round 1 should have history component")

            if not has_question:
                print(f"    [WARN] Round 1 should have 'Your question' component")

            # Verify clean_call matches verified (for seq=1 only, since no history)
            if seq == 1 and clean_call is not None:
                if clean_call != verified_total:
                    print(f"    [INFO] clean_call={clean_call:,} != verified={verified_total:,} (expected for seq>1)")

    return all_pass


def verify_conversations(log_dir="logs"):
    """Verify conversation grouping across sessions."""
    files = sorted(Path(log_dir).glob("session_*.json"), key=lambda f: f.stat().st_mtime)
    sessions = [json.loads(f.read_text()) for f in files]

    if not sessions:
        print("\nNo sessions to check for conversation grouping")
        return True

    # Group by conversation_id
    convos = {}
    for s in sessions:
        conv_id = s.get("conversation_id", s["query_id"])
        if conv_id not in convos:
            convos[conv_id] = []
        convos[conv_id].append(s)

    print(f"\n{'='*70}")
    print("CONVERSATION GROUPING CHECK")
    print(f"{'='*70}")
    print(f"Total sessions: {len(sessions)}")
    print(f"Total conversations: {len(convos)}")

    all_pass = True

    for conv_id, queries in convos.items():
        queries.sort(key=lambda s: s.get("sequence", 1))
        query_count = len(queries)

        print(f"\n  Conversation {conv_id[:12]}... ({query_count} queries)")

        for q in queries:
            seq = q.get("sequence", 1)
            hist = q.get("conversation_history_tokens", 0) or 0
            qid = q["query_id"]
            text = q["query_text"][:50]

            # Check: conversation_id should NOT equal query_id (unless solo conversation)
            grouping_ok = conv_id != qid or query_count == 1

            # Check: sequence 1 should have 0 history tokens
            # sequence > 1 should have > 0 history tokens
            history_ok = True
            if seq == 1 and hist > 0:
                history_ok = False
            if seq > 1 and hist == 0:
                history_ok = False

            status = "PASS" if (grouping_ok and history_ok) else "FAIL"
            if not (grouping_ok and history_ok):
                all_pass = False

            print(f"    [{status}] seq={seq} history={hist:,} query=\"{text}\"")
            if not grouping_ok:
                print(f"           conversation_id == query_id (grouping broken)")
            if not history_ok:
                print(f"           history_tokens mismatch for sequence {seq}")

    return all_pass


def main():
    """Run verification on all session files."""
    log_dir = Path("logs")
    if not log_dir.exists():
        print("No logs directory found")
        sys.exit(1)

    files = sorted(log_dir.glob("session_*.json"), key=lambda f: f.stat().st_mtime)
    if not files:
        print("No session files found")
        sys.exit(1)

    print(f"Found {len(files)} session files")
    all_pass = True
    pass_count = 0
    fail_count = 0

    for f in files:
        try:
            if verify_session(f):
                pass_count += 1
            else:
                fail_count += 1
                all_pass = False
        except Exception as e:
            print(f"\nError processing {f}: {e}")
            fail_count += 1
            all_pass = False

    # Add conversation grouping check
    conversations_pass = verify_conversations()

    print(f"\n{'='*70}")
    overall = all_pass and conversations_pass
    print(f"TOKEN MATH: {pass_count} passed, {fail_count} failed")
    print(f"CONVERSATION GROUPING: {'PASS' if conversations_pass else 'FAIL'}")
    print(f"OVERALL: {'ALL PASS' if overall else 'SOME FAILURES'}")
    print(f"{'='*70}")

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
