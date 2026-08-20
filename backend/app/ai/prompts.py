SYSTEM_JSON = (
    "You are an expert AI project manager for a Kanban board. "
    "Always respond with valid JSON only. Be concrete and actionable. "
    "Use the provided card ids exactly; never invent ids."
)


def prioritize_prompt(cards: list[dict]) -> str:
    return (
        "Prioritize these Kanban cards for the team.\n"
        "Return JSON: {\"ordered_card_ids\": [\"...\"], \"rationale\": [{\"card_id\": \"...\", \"reason\": \"...\", \"priority\": \"high|medium|low\"}]}\n"
        f"Cards: {cards}"
    )


def standup_prompt(activities: list[dict], cards: list[dict]) -> str:
    return (
        "Write a daily standup summary for this board.\n"
        "Return JSON: {\"summary\": \"...\", \"yesterday\": [\"...\"], \"today\": [\"...\"], \"blockers\": [\"...\"]}\n"
        f"Recent activity: {activities}\n"
        f"Open cards: {cards}"
    )


def risk_prompt(cards: list[dict], bottlenecks: list[dict]) -> str:
    return (
        "Detect project risks: blockers, stale work, overdue items, scope creep signals.\n"
        "Return JSON: {\"risks\": [{\"severity\": \"high|medium|low\", \"title\": \"...\", \"detail\": \"...\", \"card_ids\": []}]}\n"
        f"Cards: {cards}\n"
        f"Known bottleneck signals: {bottlenecks}"
    )


def workload_prompt(workload: list[dict], cards: list[dict]) -> str:
    return (
        "Suggest workload balancing / reassignment.\n"
        "Return JSON: {\"suggestions\": [{\"from_user\": \"...\", \"to_user\": \"...\", \"card_id\": \"...\", \"reason\": \"...\"}], \"summary\": \"...\"}\n"
        f"Workload: {workload}\n"
        f"Cards: {cards}"
    )


def sprint_plan_prompt(cards: list[dict], velocity: list[dict], capacity_points: float) -> str:
    return (
        f"Recommend a sprint scope for about {capacity_points} estimate points.\n"
        "Return JSON: {\"recommended_card_ids\": [\"...\"], \"total_points\": 0, \"notes\": \"...\"}\n"
        f"Velocity history: {velocity}\n"
        f"Backlog cards: {cards}"
    )


def similar_prompt(target: dict, candidates: list[dict]) -> str:
    return (
        "Find similar or duplicate cards relative to the target.\n"
        "Return JSON: {\"matches\": [{\"card_id\": \"...\", \"similarity\": 0.0, \"reason\": \"...\"}]}\n"
        f"Target: {target}\n"
        f"Candidates: {candidates}"
    )


def predict_prompt(cards: list[dict], velocity: list[dict]) -> str:
    return (
        "Estimate completion dates for open cards using historical velocity when available.\n"
        "Return JSON: {\"predictions\": [{\"card_id\": \"...\", \"eta_days\": 0, \"confidence\": \"low|medium|high\", \"note\": \"...\"}]}\n"
        f"Velocity: {velocity}\n"
        f"Open cards: {cards}"
    )
