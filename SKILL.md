---
name: hedge-fund-healthcare-jobs-monitor
description: Search and report current or recent-month hedge fund, asset-management, family-office, and secondary-market healthcare research analyst recruiting posts across Xiaohongshu, LinkedIn, WeChat public-account articles, and specialist recruiter websites. Use when Codex needs to collect active buy-side healthcare analyst hiring leads, generate a PDF report with clickable source buttons, or respond to the trigger phrase 我要找工作. Prioritize Shanghai, then Singapore, then Hong Kong; exclude internships, VC, PE, and FOF roles; focus on keywords such as hedge fund, headge fund, analyst, 资管, 二级, 家办, healthcare, 医药, 研究员, 招聘, healthcare equity, long/short, biotech, biopharma, medtech, Asia healthcare, China healthcare, APM, 上海, 新加坡, and 香港.
---

# Hedge Fund Healthcare Jobs Monitor

## Workflow

Use this skill to produce a same-day recruiting digest for healthcare research analyst roles at hedge funds, asset managers, family offices, and other secondary-market buy-side platforms.

If the user says `我要找工作`, immediately run the active job-search workflow: collect current recruiting posts, require Shanghai/Singapore/Hong Kong as the job location, treat Shanghai as the highest-priority location, require LinkedIn roles to be `Actively Hiring` / `正在招聘`, prioritize healthcare/medical-direction roles within each location, and output a PDF with clickable link buttons.

1. Build the search plan with `scripts/monitor_jobs.py --queries`.
2. Check GitHub first for high-star, clearly maintained search/crawler skills or tools that improve the requested channels:
   - Run `gh search repos "xiaohongshu linkedin wechat search crawler skill" --sort stars --limit 10`.
   - Consider a GitHub tool usable only when its README is clear, recent enough, does not require unsafe credential handling, and is directly relevant to Xiaohongshu, LinkedIn, WeChat article, or cross-platform search.
   - If no safe, better option is obvious, use Agent Reach built-in channels below.
3. Search each channel for today's posts. Keep channel failures in the final report instead of stopping the whole workflow.
4. Normalize findings into JSON and run `scripts/monitor_jobs.py --format-pdf` or `--format-html` to deduplicate, filter, sort, and format the report.
5. Save the generated report path and summarize important channel limitations for the user.

## One-Month PDF Report

When the user asks for recent-month, last-30-days, 近1个月, or monthly recruiting information, search the same channels over the last 30 days instead of only today's posts.

1. Use Chrome direct web-page collection first when Chrome/plugin/browser automation is available. Open search result pages and collect visible result titles, snippets, dates, publishers, and original result/detail links from the web pages themselves.
2. Use the same GitHub-first and Agent Reach channel flow as fallback, but keep results from the last 30 calendar days.
3. Force a minimum of 10 results whenever enough relevant public results exist. If fewer than 10 can be verified after location and active-status filtering, explain which channels failed or lacked enough matching posts.
4. Discard any finding without an original URL. Every PDF/HTML/report item must include a source link copied from the result/detail page, not a generated placeholder.
5. Proactively delete stopped or expired postings before generating any output. Exclude any item whose listing status, summary, or date note says `Expired`, `Job expired`, `No longer accepting applications`, `Applications closed`, `招聘停止`, `已停止招聘`, `停止投递`, `已停止接受求职申请`, `已停止接受申请`, `不再接受申请`, `职位已关闭`, `已招满`, `已过期`, `暂停招聘`, or `停止招聘`.
6. Proactively delete internships and internship-like postings before output, including posts containing `实习`, `实习生`, `暑期`, `日常实习`, `intern`, `internship`, `summer analyst`, `summer intern`, `project intern`, or `trainee`.
7. Proactively delete VC, PE, and FOF postings before output, including posts containing `VC`, `PE`, `PEVC`, `private equity`, `venture capital`, `growth equity`, `buyout`, `私募股权`, `股权投资`, `FOF`, `fund of funds`, `母基金`, or `基金中基金`.
8. For LinkedIn findings, keep only jobs whose visible/listing status is `Actively Hiring`, `Apply visible`, `Apply now`, `正在招聘`, or `招聘中`; exclude closed or stopped application statuses even if the title otherwise matches.
9. Keep only postings located in Shanghai, Singapore, or Hong Kong. Sort Shanghai/上海 first with highest priority, then Singapore/新加坡, then Hong Kong/香港. Within each location, show healthcare/medical-direction roles before broader buy-side equity roles.
10. Normalize the payload with `start_date`, `end_date`, `strict_job_filters: true`, `findings`, and `channel_failures`.
11. Generate the PDF directly into the Downloads folder with:

```bash
python3 /Users/lipengfei/.codex/skills/hedge-fund-healthcare-jobs-monitor/scripts/monitor_jobs.py --format-pdf < findings.json
```

12. The script prints the generated PDF path. Default output is `~/Downloads/近1个月对冲基金医药研究员招聘监控-YYYY-MM-DD.pdf`.
13. If PDF generation fails, generate HTML with `--format-html`, save it to `~/Downloads`, and tell the user the PDF dependency failure.

## Channel Commands

Use the Agent Reach skill as the source of truth for channel-specific details.

- Chrome direct collection: if the user asks to use Chrome/plugin/web pages directly, use the Chrome plugin to visit search pages, collect visible results, open result details when needed, and copy original links from the browser page. Prefer this for Xiaohongshu and LinkedIn when logged-in Chrome state is required.
- Xiaohongshu: run `xhs search "QUERY"`, then read promising results with `xhs read RESULT_URL_OR_ID`. Do not read a bare note id that was not obtained from search/feed results.
- LinkedIn: run `mcporter call 'linkedin-scraper.search_jobs(keyword: "QUERY", limit: 10)'`. If login or MCP state fails, record the failure and continue.
- WeChat public-account articles: run `mcporter call 'exa.web_search_exa(query: "QUERY", numResults: 5, includeDomains: ["mp.weixin.qq.com"])'`; crawl promising article URLs with `exa.crawling_exa`.

## Xiaohongshu Search Integration

Use the strongest available Xiaohongshu search path in this order:

1. Existing Agent Reach route: `xhs search "QUERY"` and `xhs read RESULT_URL_OR_ID`. This is the default because it is already installed in this environment.
2. `jackwener/xiaohongshu-cli`: a GitHub CLI/skill with search/read support and structured YAML/JSON output; use when Agent Reach `xhs` is missing or stale.
3. `autoclaw-cc/xiaohongshu-skills`: use `python scripts/cli.py search-feeds --keyword "QUERY"` when a local checkout or installation exists.
4. `@lucasygu/redbook`: use as a Node CLI fallback when available for Xiaohongshu/RedNote search and reading.
5. Chrome direct collection: use the logged-in Chrome Xiaohongshu web UI when CLI auth fails, while respecting CAPTCHA and login prompts.

Only install a new Xiaohongshu tool after the user explicitly asks for installation. Otherwise, report the candidate integration method and continue with installed channels.

## Headhunter Websites

Actively search well-known headhunter and finance recruiting websites before relying only on LinkedIn. Use site-specific queries for:

- Selby Jennings / Phaidon: `site:selbyjennings.com`
- Hays: `site:hays.com`
- Michael Page: `site:michaelpage.com`
- Robert Walters: `site:robertwalters.com`
- Randstad: `site:randstad.com`
- Korn Ferry, Egon Zehnder, Heidrick & Struggles, Spencer Stuart, Russell Reynolds
- Morgan McKinley, eFinancialCareers, Options Group, Dynamics Search Partners
- Long Ridge Partners, Mondrian Alpha, Lote and Partners

For `我要找工作`, prioritize official recruiter/job pages over aggregator snippets when both contain the same role, and keep Shanghai results ahead of Singapore and Hong Kong.

## Matching Rules

Treat a result as reportable when it is from the current local date and has evidence for both recruiting intent and healthcare/buy-side relevance.

- Recruiting intent examples: 招聘, 招人, base, JD, opening, hire, hiring, analyst, researcher, 研究员, 分析师, 岗位.
- Buy-side examples: hedge fund, headge fund, fund, asset management, 资管, 二级, 家办, family office, 买方, 私募, 对冲基金.
- Healthcare examples: healthcare, healthcare equity, healthcare L/S, pharma, biotech, biopharma, medtech, life sciences, Asia healthcare, China healthcare, 医药, 医疗, 生物医药, 创新药, 药企, 医疗器械, 港股医药, A股医药, 美股医药.
- Work-location examples: Shanghai, Singapore, Hong Kong, 上海, 新加坡, 香港.
- Role-shape examples: equity research, investment analyst, public equity, long/short, long short, PM, APM, 股票研究, 行业研究, 投资分析师.
- If the date is ambiguous but the content says today or appears in a same-day search result, include it with a clear date note such as `日期判断：搜索结果显示为当天，原文日期未明`.

## Output

Format every finding with:

- 渠道
- 标题/职位名
- 机构/发布者
- 地点
- 招聘状态
- 招聘需求摘要
- 日期判断
- 原始链接
- 关键词命中

Deduplicate by URL first. If there is no URL, deduplicate by normalized title, channel, and publisher. Generate a report even when no results are found so the user can see channel status.

For user-requested data collection, `我要找工作`, and one-month reports, return at least 10 findings when enough relevant source pages exist. Never count or report a finding that lacks an original link. PDF output must render each original link as a clickable `打开链接` button rather than printing a long URL.

The helper script enforces this by excluding findings with an empty `url` and proactively deleting stopped-application findings from HTML and PDF output. If fewer than 10 linked active findings remain, the report must include a short explanation of the channel, location, active-status, or login limitation.

The helper script also removes internship, VC, PE, and FOF postings before HTML and PDF output. Do not count these as valid findings even when they otherwise match healthcare, Shanghai, or active-status rules.

## Helper Script

Use `scripts/monitor_jobs.py --queries` to print the default query set.

Use `scripts/monitor_jobs.py --format-pdf < findings.json` for a recent-month PDF report. Include `start_date`, `end_date`, and `strict_job_filters: true` when the report is triggered by `我要找工作`:

```json
{
  "date": "2026-06-07",
  "start_date": "2026-05-09",
  "end_date": "2026-06-07",
  "strict_job_filters": true,
  "findings": [
    {
      "channel": "小红书",
      "title": "医药研究员招聘",
      "publisher": "发布者",
      "location": "Hong Kong",
      "recruiting_status": "Actively Hiring",
      "summary": "招聘需求摘要",
      "date_note": "原文发布日期为当天",
      "url": "https://example.com",
      "keyword_hits": ["医药", "二级", "研究员"]
    }
  ],
  "channel_failures": [
    {"channel": "LinkedIn", "reason": "登录态失效"}
  ]
}
```
