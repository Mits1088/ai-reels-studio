"""
Generate edit-plan.md — the human-readable summary that ships alongside
edit-plan.json. This is what the user reviews to approve a plan before
the compiler runs.

The markdown is intentionally compact:
  - Header with project + style + counts
  - Per-beat summary table
  - Per-beat detail section with rationale and asset selection reason

It is NOT a render preview — that happens in Remotion. It's an editorial
review document.
"""

from __future__ import annotations

from .model import EditPlan, BeatPlan


def render_edit_plan_markdown(plan: EditPlan) -> str:
    """Return the markdown text for an EditPlan."""
    lines: list[str] = []
    lines.append(f"# Edit Plan: {plan.project_slug}")
    lines.append("")
    lines.append(f"**Style:** {plan.style}")
    lines.append(f"**Beats:** {len(plan.beats)}")
    if plan.generated_at:
        lines.append(f"**Generated:** {plan.generated_at}")
    if plan.compiler_version:
        lines.append(f"**Compiler:** `{plan.compiler_version}`")
    lines.append(f"**Schema:** v{plan.schema_version}")

    if plan.verbatim_lanes:
        lines.append("")
        lines.append(
            f"_This plan carries {len(plan.verbatim_lanes)} verbatim "
            f"lane(s); the compiler will pass them through unchanged._"
        )

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| # | Beat | Template | Caption | Split | Asset | Conf. | Review |"
    )
    lines.append(
        "|---|------|----------|---------|-------|-------|-------|--------|"
    )
    for i, bp in enumerate(plan.beats, start=1):
        asset_label = bp.selected_asset_filename or bp.selected_asset_id or "—"
        if asset_label and len(asset_label) > 32:
            asset_label = asset_label[:29] + "..."
        review = "yes" if bp.human_review_required else ""
        lines.append(
            f"| {i} "
            f"| `{bp.beat_id}` "
            f"| {bp.template_id} "
            f"| {bp.caption_mode} "
            f"| {bp.split_ratio} "
            f"| {asset_label} "
            f"| {bp.selection_confidence:.2f} "
            f"| {review} |"
        )

    lines.append("")
    lines.append("## Per-beat detail")
    lines.append("")
    for bp in plan.beats:
        lines.extend(_render_beat_detail(bp))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_beat_detail(bp: BeatPlan) -> list[str]:
    out: list[str] = []
    out.append(f"### `{bp.beat_id}` — {bp.template_id}")
    out.append("")
    out.append(f"- **Avatar:** {bp.avatar_mode}")
    out.append(f"- **Caption mode:** {bp.caption_mode}")
    out.append(f"- **Split ratio:** {bp.split_ratio}")
    if bp.proof_class:
        out.append(f"- **Proof class:** {bp.proof_class}")
    if bp.proof_protected:
        out.append("- **Proof-protected:** yes")

    asset_label = bp.selected_asset_filename or bp.selected_asset_id or "_(none)_"
    out.append(f"- **Selected asset:** {asset_label} (confidence {bp.selection_confidence:.2f})")
    if bp.selection_reason:
        out.append(f"- **Selection reason:** {bp.selection_reason}")
    if bp.candidate_assets and len(bp.candidate_assets) > 1:
        out.append("- **Other candidates:**")
        for c in bp.candidate_assets:
            if c.asset_id == bp.selected_asset_id:
                continue
            out.append(f"  - `{c.asset_id}` (score {c.score:.2f}) — {c.reason}")
    if bp.fallback_asset_ids:
        out.append(f"- **Fallbacks:** {', '.join(bp.fallback_asset_ids)}")
    if bp.human_review_required:
        out.append("- **Human review required:** yes")

    out.append("")
    out.append(f"**Motion budget:** hero=`{bp.motion_budget.hero.kind}`")
    if bp.motion_budget.support:
        out.append(f"  - support=`{bp.motion_budget.support.kind}`")
    if bp.motion_budget.accent:
        out.append(f"  - accent=`{bp.motion_budget.accent.kind}`")

    if bp.rationale:
        out.append("")
        out.append(f"**Rationale:** {bp.rationale}")

    if bp.notes:
        out.append("")
        out.append(f"_Notes: {bp.notes}_")

    return out
