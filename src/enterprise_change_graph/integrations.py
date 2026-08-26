from __future__ import annotations


def github_pr_comment(markdown_report: str) -> str:
    marker = "<!-- enterprise-change-graph -->"
    return f"{marker}\n{markdown_report.rstrip()}\n"


def servicenow_change_update(markdown_report: str) -> dict[str, str]:
    return {"work_notes": markdown_report.rstrip()}


def jira_comment_adf(markdown_report: str) -> dict:
    paragraphs = []
    for line in markdown_report.rstrip().splitlines():
        paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": line or " "}]})
    return {"body": {"type": "doc", "version": 1, "content": paragraphs}}
