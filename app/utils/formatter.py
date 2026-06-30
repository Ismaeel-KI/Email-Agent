from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from app.schemas import EmailState

console = Console()

# ── Category display config ───────────────────────────────────────────────────
CATEGORY_CONFIG: dict[str, dict] = {
    "important": {"icon": "🔴", "color": "bold red",    "label": "IMPORTANT"},
    "work":      {"icon": "💼", "color": "bold blue",   "label": "WORK"},
    "jobs":      {"icon": "🧳", "color": "bold cyan",   "label": "JOBS"},
    "personal":  {"icon": "👤", "color": "bold green",  "label": "PERSONAL"},
    "finance":   {"icon": "💰", "color": "bold yellow", "label": "FINANCE"},
    "technology":{"icon": "⚙️", "color": "bold magenta","label": "TECHNOLOGY"},
    "ads":       {"icon": "📣", "color": "dim",         "label": "ADS"},
    "other":     {"icon": "📋", "color": "white",       "label": "OTHER"},
}

# Categories to show full detail for (ads are skipped/summarized)
SKIP_CATEGORIES = {"ads"}


def format_digest(results: list[EmailState], run_time: datetime | None = None) -> None:
    """
    Print a rich CLI digest of processed emails grouped by category.

    Args:
        results:  List of enriched EmailState dicts from the agent pipeline.
        run_time: Timestamp of this run (defaults to now).
    """
    run_time = run_time or datetime.now(timezone.utc)
    date_str = run_time.strftime("%d %b %Y, %H:%M UTC")

    # ── Header ────────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold white]Email Digest — {date_str}[/bold white]",
        box=box.DOUBLE,
        style="bold white",
        expand=False,
        padding=(0, 4),
    ))
    console.print()

    if not results:
        console.print("  [dim]No emails to display.[/dim]")
        _print_footer(results)
        return

    # ── Group by category ─────────────────────────────────────────────────────
    grouped: dict[str, list[EmailState]] = {}
    for email in results:
        cat = (email.get("category") or "other").lower()
        grouped.setdefault(cat, []).append(email)

    # ── Sort categories by priority ───────────────────────────────────────────
    priority_order = ["important", "work", "jobs", "personal", "finance", "technology", "other", "ads"]
    sorted_categories = sorted(
        grouped.keys(),
        key=lambda c: priority_order.index(c) if c in priority_order else 99
    )

    # ── Print each category ───────────────────────────────────────────────────
    for category in sorted_categories:
        emails = grouped[category]
        config = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["other"])
        icon = config["icon"]
        color = config["color"]
        label = config["label"]

        # Category header
        console.print(
            f"  {icon}  [{color}]{label}[/{color}] [dim]({len(emails)})[/dim]"
        )
        console.print(f"  {'─' * 54}", style="dim")

        if category in SKIP_CATEGORIES:
            # Ads — just list subjects, no detail
            for email in emails:
                console.print(f"  [dim]• {email['subject'][:60]}[/dim]")
            console.print()
            continue

        # Full detail for non-ad categories
        # Sort: action-required emails first
        sorted_emails = sorted(emails, key=lambda e: not e.get("requires_action", False))

        for email in sorted_emails:
            _print_email_row(email, color)

        console.print()

    # ── Footer ────────────────────────────────────────────────────────────────
    _print_footer(results)


def _print_email_row(email: EmailState, color: str) -> None:
    """Print a single email row with summary and action flags."""
    subject = email.get("subject", "(no subject)")[:55]
    summary = email.get("summary") or email.get("snippet", "")
    requires_action = email.get("requires_action", False)
    action_type = (email.get("action_type") or "").upper()
    deadline = email.get("deadline")
    has_error = bool(email.get("error"))

    # Action badge
    action_badge = ""
    if requires_action:
        action_badge = f" [bold yellow]▶ {action_type}[/bold yellow]"
        if deadline:
            action_badge += f" [yellow]by {deadline}[/yellow]"

    # Error badge
    error_badge = " [red]⚠ ERROR[/red]" if has_error else ""

    # Subject line
    console.print(f"  [bold]• {subject}[/bold]{action_badge}{error_badge}")

    # Summary line
    if summary:
        # Wrap long summaries at 70 chars
        words = summary.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 > 70:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            lines.append(current)

        console.print(f"    [dim]{lines[0]}[/dim]")
        for line in lines[1:]:
            console.print(f"    [dim]{line}[/dim]")

    # Sender line
    sender = email.get("sender", "")
    if sender:
        console.print(f"    [dim italic]From: {sender[:60]}[/dim italic]")

    console.print()


def _print_footer(results: list[EmailState]) -> None:
    """Print summary stats at the bottom of the digest."""
    total = len(results)
    action_count = sum(1 for r in results if r.get("requires_action"))
    ads_count = sum(1 for r in results if r.get("category") == "ads")
    error_count = sum(1 for r in results if r.get("error"))

    console.print("  " + "─" * 54, style="dim")
    stats = f"  {total} emails processed"
    if action_count:
        stats += f" · [yellow]{action_count} require action[/yellow]"
    if ads_count:
        stats += f" · [dim]{ads_count} ads skipped[/dim]"
    if error_count:
        stats += f" · [red]{error_count} errors[/red]"

    console.print(stats)
    console.print("  " + "═" * 54, style="dim")
    console.print()