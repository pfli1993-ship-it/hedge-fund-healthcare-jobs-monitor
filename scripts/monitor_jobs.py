#!/usr/bin/env python3
"""Helpers for the hedge fund healthcare jobs monitor skill."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

MIN_FINDINGS = 10
ALLOWED_LOCATIONS = ["shanghai", "singapore", "hong kong", "hongkong", "香港", "上海", "新加坡"]
LOCATION_PRIORITY = [
    ("shanghai", "上海"),
    ("singapore", "新加坡"),
    ("hong kong", "hongkong", "香港"),
]
KNOWN_HEADHUNTER_DOMAINS = [
    "selbyjennings.com",
    "hays.com",
    "michaelpage.com",
    "robertwalters.com",
    "randstad.com",
    "kornferry.com",
    "egonzehnder.com",
    "heidrick.com",
    "spencerstuart.com",
    "russellreynolds.com",
    "morganmckinley.com",
    "efinancialcareers.com",
    "optionsgroup.com",
    "dynamicssearchpartners.com",
    "longridgepartners.com",
    "mondrian-alpha.com",
    "loteandpartners.com",
]
ACTIVE_STATUS_TERMS = ["actively hiring", "正在招聘", "招聘中", "apply visible", "apply now", "open role"]
STOPPED_STATUS_TERMS = [
    "no longer accepting",
    "no longer accepting applications",
    "applications closed",
    "application closed",
    "job closed",
    "position closed",
    "position filled",
    "role filled",
    "expired",
    "closed",
    "已停止接受求职申请",
    "已停止接受申请",
    "停止接受求职申请",
    "停止接受申请",
    "不再接受申请",
    "不再接受求职申请",
    "职位已关闭",
    "岗位已关闭",
    "招聘已关闭",
    "已关闭",
    "已招满",
    "暂停招聘",
    "停止招聘",
]
CORE_TERMS = [
    "hedge fund",
    "headge fund",
    "analyst",
    "资管",
    "二级",
    "家办",
    "healthcare",
    "healthcare equity",
    "healthcare l/s",
    "healthcare long short",
    "biotech",
    "biopharma",
    "pharma",
    "medtech",
    "life sciences",
    "equity research",
    "investment analyst",
    "public equity",
    "long/short",
    "long short",
    "Asia healthcare",
    "China healthcare",
    "Greater China",
    "PM",
    "APM",
    "医药",
    "医疗",
    "生物医药",
    "创新药",
    "药企",
    "医疗器械",
    "港股医药",
    "A股医药",
    "美股医药",
    "研究员",
    "分析师",
    "投资分析师",
    "股票研究",
    "行业研究",
    "主动招聘",
    "正在招聘",
    "上海",
    "新加坡",
    "香港",
    "招聘",
]

QUERIES = [
    "医药 研究员 招聘 二级",
    "医药 分析师 招聘 资管",
    "医药 研究员 家办 招聘",
    "healthcare analyst hedge fund hiring",
    "healthcare analyst asset management",
    "biotech analyst hedge fund",
    "pharma analyst family office",
    "headge fund healthcare analyst",
    "我要找工作 healthcare equity analyst hedge fund Shanghai",
    "我要找工作 healthcare equity analyst hedge fund Singapore",
    "我要找工作 healthcare equity analyst hedge fund Hong Kong",
    "我要找工作 医药 研究员 私募 上海",
    "我要找工作 医药 研究员 资管 香港",
    "我要找工作 healthcare long short analyst Hong Kong Singapore Shanghai",
    "我要找工作 site:selbyjennings.com Shanghai healthcare equity analyst hedge fund",
    "我要找工作 site:hays.com Shanghai healthcare investment analyst",
    "我要找工作 site:michaelpage.com Shanghai healthcare investment analyst",
    "我要找工作 site:robertwalters.com Singapore Hong Kong healthcare analyst asset management",
    "我要找工作 site:efinancialcareers.com Shanghai Singapore Hong Kong healthcare hedge fund analyst",
    "我要找工作 site:longridgepartners.com healthcare hedge fund analyst",
    "我要找工作 site:mondrian-alpha.com healthcare hedge fund analyst",
    "我要找工作 site:loteandpartners.com hedge fund analyst Hong Kong",
]


def normalize(text: Any) -> str:
    value = "" if text is None else str(text)
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def dedupe(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in findings:
        url = normalize(item.get("url"))
        if not url:
            continue
        if url:
            key = f"url:{url}"
        else:
            key = "text:" + "|".join(
                normalize(item.get(field)) for field in ("channel", "title", "publisher")
            )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def has_allowed_location(item: dict[str, Any]) -> bool:
    haystack = normalize(
        " ".join(str(item.get(field) or "") for field in ("location", "title", "summary", "date_note"))
    )
    return any(term in haystack for term in ALLOWED_LOCATIONS)


def location_rank(item: dict[str, Any]) -> int:
    haystack = normalize(
        " ".join(str(item.get(field) or "") for field in ("location", "title", "summary", "date_note"))
    )
    for idx, terms in enumerate(LOCATION_PRIORITY):
        if any(term in haystack for term in terms):
            return idx
    return len(LOCATION_PRIORITY)


def source_rank(item: dict[str, Any]) -> int:
    url = normalize(item.get("url"))
    if any(domain in url for domain in KNOWN_HEADHUNTER_DOMAINS):
        return 0
    if "linkedin.com" in url:
        return 1
    return 2


def is_stopped_accepting(item: dict[str, Any]) -> bool:
    haystack = normalize(
        " ".join(
            str(item.get(field) or "")
            for field in (
                "recruiting_status",
                "status",
                "summary",
                "date_note",
                "title",
                "raw_status",
            )
        )
    )
    return any(term in haystack for term in STOPPED_STATUS_TERMS)


def has_active_linkedin_status(item: dict[str, Any]) -> bool:
    if "linkedin" not in normalize(item.get("channel")) and "linkedin.com" not in normalize(item.get("url")):
        return True
    status = normalize(item.get("recruiting_status") or item.get("status") or item.get("date_note"))
    text = normalize(" ".join(str(item.get(field) or "") for field in ("summary", "date_note", "title")))
    if is_stopped_accepting(item):
        return False
    return any(term in status or term in text for term in ACTIVE_STATUS_TERMS)


def filter_findings(findings: list[dict[str, Any]], strict_job_filters: bool = False) -> list[dict[str, Any]]:
    linked = [item for item in dedupe(findings) if not is_stopped_accepting(item)]
    if not strict_job_filters:
        return sorted(linked, key=lambda item: (location_rank(item), source_rank(item), normalize(item.get("title"))))
    active = [item for item in linked if has_allowed_location(item) and has_active_linkedin_status(item)]
    return sorted(active, key=lambda item: (location_rank(item), source_rank(item), normalize(item.get("title"))))


def minimum_result_note(count: int) -> str:
    if count >= MIN_FINDINGS:
        return f"已满足至少 {MIN_FINDINGS} 条带原始链接结果。"
    return f"当前仅验证到 {count} 条带原始链接结果，未满足至少 {MIN_FINDINGS} 条要求；请在报告中说明渠道失败、登录限制或公开结果不足原因。"


def coerce_hits(item: dict[str, Any]) -> list[str]:
    hits = item.get("keyword_hits", [])
    if isinstance(hits, str):
        hits = [part.strip() for part in hits.split(",")]
    if not isinstance(hits, list):
        hits = []
    return [str(hit) for hit in hits if str(hit).strip()]


def today_iso() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def last_30_days_label(payload: dict[str, Any]) -> str:
    end = payload.get("end_date") or payload.get("date") or today_iso()
    start = payload.get("start_date")
    if not start:
        try:
            start_date = dt.date.fromisoformat(str(end)) - dt.timedelta(days=29)
            start = start_date.isoformat()
        except ValueError:
            start = "近30天"
    return f"{start} 至 {end}"


def safe_filename(value: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value, flags=re.UNICODE)
    value = value.strip(".-")
    return value or "report"


def html_report(payload: dict[str, Any]) -> str:
    date_range = html.escape(last_30_days_label(payload))
    findings = filter_findings(payload.get("findings") or [], bool(payload.get("strict_job_filters")))
    failures = payload.get("channel_failures") or []

    rows = []
    if findings:
        for idx, item in enumerate(findings, 1):
            hits = "、".join(coerce_hits(item)) or "未标注"
            url = item.get("url") or ""
            url_html = (
                f'<a class="link-button" href="{html.escape(str(url))}">打开链接</a>'
                if url
                else "无链接"
            )
            rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td>{html.escape(str(item.get('channel') or '未知'))}</td>"
                f"<td>{html.escape(str(item.get('title') or '未命名招聘线索'))}</td>"
                f"<td>{html.escape(str(item.get('publisher') or '未识别'))}</td>"
                f"<td>{html.escape(str(item.get('location') or '未标注'))}</td>"
                f"<td>{html.escape(str(item.get('recruiting_status') or item.get('status') or '未标注'))}</td>"
                f"<td>{html.escape(str(item.get('summary') or '未提供摘要'))}</td>"
                f"<td>{html.escape(str(item.get('date_note') or '未标注'))}</td>"
                f"<td>{html.escape(hits)}</td>"
                f"<td>{url_html}</td>"
                "</tr>"
            )
    else:
        rows.append('<tr><td colspan="10">近 1 个月未发现带原始链接的明确匹配招聘信息。</td></tr>')

    failure_items = []
    for failure in failures:
        if isinstance(failure, dict):
            channel = failure.get("channel") or "未知渠道"
            reason = failure.get("reason") or "未说明"
        else:
            channel = "未知渠道"
            reason = str(failure)
        failure_items.append(f"<li>{html.escape(str(channel))}：{html.escape(str(reason))}</li>")
    failures_html = (
        f"<h2>渠道状态</h2><ul>{''.join(failure_items)}</ul>" if failure_items else ""
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>近1个月对冲基金医药研究员招聘监控</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif; color: #111827; margin: 32px; }}
    h1 {{ font-size: 24px; margin-bottom: 4px; }}
    .meta {{ color: #4b5563; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; vertical-align: top; word-break: break-word; font-size: 12px; }}
    th {{ background: #f3f4f6; }}
    td:nth-child(1) {{ width: 28px; text-align: center; }}
    td:nth-child(2) {{ width: 64px; }}
    .link-button {{ color: #fff; background: #2563eb; border-radius: 4px; padding: 4px 8px; text-decoration: none; white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>近1个月对冲基金医药研究员招聘监控</h1>
  <div class="meta">日期范围：{date_range}；匹配结果：{len(findings)} 条；{html.escape(minimum_result_note(len(findings)))}</div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>渠道</th><th>标题/职位名</th><th>机构/发布者</th><th>地点</th><th>招聘状态</th><th>招聘需求摘要</th><th>日期判断</th><th>关键词命中</th><th>原始链接</th>
      </tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  {failures_html}
</body>
</html>"""


def pdf_lines(payload: dict[str, Any]) -> list[str]:
    findings = filter_findings(payload.get("findings") or [], bool(payload.get("strict_job_filters")))
    failures = payload.get("channel_failures") or []
    lines = [
        "近1个月对冲基金医药研究员招聘监控",
        f"日期范围：{last_30_days_label(payload)}",
        f"匹配结果：{len(findings)} 条",
        minimum_result_note(len(findings)),
        "",
    ]
    if findings:
        for idx, item in enumerate(findings, 1):
            hits = "、".join(coerce_hits(item)) or "未标注"
            lines.extend(
                [
                    f"{idx}. {item.get('title') or '未命名招聘线索'}",
                    f"渠道：{item.get('channel') or '未知'}",
                    f"机构/发布者：{item.get('publisher') or '未识别'}",
                    f"地点：{item.get('location') or '未标注'}",
                    f"招聘状态：{item.get('recruiting_status') or item.get('status') or '未标注'}",
                    f"招聘需求摘要：{item.get('summary') or '未提供摘要'}",
                    f"日期判断：{item.get('date_note') or '未标注'}",
                    f"关键词命中：{hits}",
                    f"原始链接：打开链接",
                    "",
                ]
            )
    else:
        lines.extend(["近 1 个月未发现带原始链接的明确匹配招聘信息。", ""])

    if failures:
        lines.append("渠道状态：")
        for failure in failures:
            if isinstance(failure, dict):
                channel = failure.get("channel") or "未知渠道"
                reason = failure.get("reason") or "未说明"
            else:
                channel = "未知渠道"
                reason = str(failure)
            lines.append(f"- {channel}：{reason}")
    return lines


def write_pdf_report(payload: dict[str, Any], output_dir: str | None = None) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas

    output_root = Path(output_dir or os.path.expanduser("~/Downloads")).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)
    date_value = payload.get("end_date") or payload.get("date") or today_iso()
    filename = safe_filename(f"近1个月对冲基金医药研究员招聘监控-{date_value}.pdf")
    output_path = output_root / filename

    font_name = "STSong-Light"
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    page_width, page_height = A4
    margin = 42
    line_height = 15
    current_y = page_height - margin
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle("近1个月对冲基金医药研究员招聘监控")
    c.setFont(font_name, 10)

    def new_page() -> None:
        nonlocal current_y
        c.showPage()
        c.setFont(font_name, 10)
        current_y = page_height - margin

    link_queue = [item.get("url") for item in filter_findings(payload.get("findings") or [], bool(payload.get("strict_job_filters"))) if item.get("url")]

    def draw_link_button(label: str, url: str) -> None:
        nonlocal current_y
        if current_y < margin:
            new_page()
        prefix = "原始链接："
        c.setFillColorRGB(0, 0, 0)
        c.drawString(margin, current_y, prefix)
        button_x = margin + 52
        button_y = current_y - 3
        button_w = 54
        button_h = 14
        c.setFillColorRGB(0.15, 0.38, 0.92)
        c.roundRect(button_x, button_y, button_w, button_h, 3, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(button_x + 8, current_y, label)
        c.linkURL(url, (button_x, button_y, button_x + button_w, button_y + button_h), relative=0)
        c.setFillColorRGB(0, 0, 0)
        current_y -= line_height

    max_chars = 78
    for raw_line in pdf_lines(payload):
        if str(raw_line).startswith("原始链接：打开链接") and link_queue:
            draw_link_button("打开链接", str(link_queue.pop(0)))
            continue
        wrapped = textwrap.wrap(str(raw_line), width=max_chars) or [""]
        for line in wrapped:
            if current_y < margin:
                new_page()
            c.drawString(margin, current_y, line)
            current_y -= line_height
    c.save()
    return output_path


def print_queries() -> None:
    json.dump(
        {
            "keywords": CORE_TERMS,
            "queries": QUERIES,
            "location_priority": ["Shanghai/上海", "Singapore/新加坡", "Hong Kong/香港"],
            "known_headhunter_domains": KNOWN_HEADHUNTER_DOMAINS,
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", action="store_true", help="Print default keyword and query plan.")
    parser.add_argument("--format-html", action="store_true", help="Format a one-month HTML report from stdin.")
    parser.add_argument("--format-pdf", action="store_true", help="Write a one-month PDF report from stdin.")
    parser.add_argument("--output-dir", help="Directory for generated PDF reports. Defaults to ~/Downloads.")
    args = parser.parse_args()

    if args.queries:
        print_queries()
        return 0

    if args.format_html:
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Invalid JSON payload: {exc}\n")
            return 2
        sys.stdout.write(html_report(payload))
        sys.stdout.write("\n")
        return 0

    if args.format_pdf:
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Invalid JSON payload: {exc}\n")
            return 2
        output_path = write_pdf_report(payload, args.output_dir)
        sys.stdout.write(str(output_path))
        sys.stdout.write("\n")
        return 0

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
