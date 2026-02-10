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
                if item.get("is_real"):
                    verified_total = item.get("tokens", 0)
                    print(f"    [=] {label}: {verified_total:,} (verified)")
                else:
                    tokens = item.get("tokens", item.get("tokens_est", 0)) or 0
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
