#!/usr/bin/env python3
"""Extract articles from daily HTML reports and build a data dashboard."""

import re
import json
import os
from collections import Counter
from datetime import datetime

REPORTS_DIR = os.path.expanduser("~/.openclaw/workspace/game-daily-site/daily")
SITE_DIR = os.path.expanduser("~/.openclaw/workspace/game-daily-site")

def extract_articles(html_path):
    """Parse a daily report HTML and extract all articles."""
    with open(html_path, 'r') as f:
        html = f.read()
    
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', html)
    date = date_match.group(1) if date_match else 'unknown'
    
    articles = []
    
    # Pattern 1: <a class="article" href="..."> (newer format)
    pattern_new = re.compile(
        r'<a\s+class="article"\s+href="([^"]+)".*?'
        r'<h2>(.*?)</h2>.*?'
        r'<p\s+class="summary">(.*?)</p>.*?'
        r'<span\s+class="tag\s+source">(.*?)</span>',
        re.DOTALL
    )
    
    # Pattern 2: <div class="article"> with <a class="link" href="..."> inside (older format)
    pattern_old = re.compile(
        r'<div\s+class="article">.*?'
        r'<h2>(.*?)</h2>.*?'
        r'<p\s+class="summary">(.*?)</p>.*?'
        r'<span\s+class="tag\s+source">(.*?)</span>.*?'
        r'<a\s+class="link"\s+href="([^"]+)"',
        re.DOTALL
    )
    
    for m in pattern_new.finditer(html):
        url, title, summary, source = m.groups()
        summary = re.sub(r'<[^>]+>', '', summary).strip()
        title = re.sub(r'<[^>]+>', '', title).strip()
        articles.append({
            'url': url.strip(),
            'title': title,
            'summary': summary,
            'source': source.strip(),
            'date': date
        })
    
    # If new format found nothing, try old format
    if not articles:
        for m in pattern_old.finditer(html):
            title, summary, source, url = m.groups()
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            title = re.sub(r'<[^>]+>', '', title).strip()
            articles.append({
                'url': url.strip(),
                'title': title,
                'summary': summary,
                'source': source.strip(),
                'date': date
            })
    
    return articles

def extract_game_names(title, summary):
    """Extract game names mentioned in 《》 brackets."""
    text = title + ' ' + summary
    games = re.findall(r'《([^》]+)》', text)
    return games

def extract_keywords(title, summary):
    """Extract key topic keywords."""
    text = title + ' ' + summary
    keywords = []
    
    # Topic keywords to look for
    topics = [
        'AI', '出海', '小游戏', 'SLG', 'RPG', 'ARPG', '抽卡', '二次元',
        '买量', '投放', 'KOL', '广告', 'Unity', '腾讯', '网易', '米哈游',
        '完美世界', '三七', 'Supercell', 'Playrix', '任天堂', '任天堂',
        '畅销榜', '收入', '流水', 'DAU', 'CPI', 'ROI', 'LTV',
        '跨端', 'PC', '主机', '手游', '独立游戏', 'UGC',
        '电竞', '赛事', 'IP', '版号', '合规', '欧洲', '东南亚',
        '日本', '北美', '北美', '微信', '抖音', 'TikTok',
        '长线运营', '版本更新', '商业化', '变现', '留存', '拉新',
        '战斗通行证', 'Battle Pass', 'BattlePass',
        '元宇宙', 'Web3', '区块链',
        '大模型', 'AIGC', '生成式AI',
        '开放世界', '开放世界',
        '模拟经营', '三消', '塔防', '策略',
        '版号', '监管', '16+', 'PEGI',
        '财报', '融资', '收购', '并购',
    ]
    
    text_lower = text.lower()
    for topic in topics:
        if topic.lower() in text_lower:
            keywords.append(topic)
    
    return keywords

def build_dashboard(articles):
    """Build the dashboard HTML with charts."""
    
    # Aggregate data
    dates = sorted(set(a['date'] for a in articles))
    sources = sorted(set(a['source'] for a in articles))
    
    # Articles per date per source
    date_source_count = {}
    for d in dates:
        date_source_count[d] = Counter()
    for a in articles:
        date_source_count[a['date']][a['source']] += 1
    
    # Source totals
    source_totals = Counter(a['source'] for a in articles)
    
    # Game mentions
    game_counter = Counter()
    for a in articles:
        for g in extract_game_names(a['title'], a['summary']):
            game_counter[g] += 1
    top_games = game_counter.most_common(15)
    
    # Keyword trends
    keyword_counter = Counter()
    date_keywords = {}
    for d in dates:
        date_keywords[d] = Counter()
    for a in articles:
        kws = extract_keywords(a['title'], a['summary'])
        for kw in kws:
            keyword_counter[kw] += 1
            date_keywords[a['date']][kw] += 1
    top_keywords = keyword_counter.most_common(20)
    
    # Article count trend
    date_counts = Counter(a['date'] for a in articles)
    
    # Build JSON data for JS
    data_json = json.dumps({
        'dates': dates,
        'sources': sources,
        'dateCounts': [date_counts.get(d, 0) for d in dates],
        'dateSourceCount': {d: dict(date_source_count[d]) for d in dates},
        'sourceTotals': dict(source_totals),
        'topGames': [{'name': g, 'count': c} for g, c in top_games],
        'topKeywords': [{'name': k, 'count': c} for k, c in top_keywords],
        'dateKeywords': {d: dict(date_keywords[d]) for d in dates},
        'totalArticles': len(articles),
        'totalSources': len(sources),
    }, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>游戏行业数据看板 - Republic Zhu</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
    <style>
        :root {{
            --bg: #0f1117;
            --card: #1a1d27;
            --border: #2a2d3a;
            --accent: #6c5ce7;
            --accent2: #a29bfe;
            --text: #e2e4ed;
            --text-dim: #8a8d9a;
            --green: #00b894;
            --orange: #fdcb6e;
            --red: #ff6b6b;
            --cyan: #00cec9;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro SC", "PingFang SC", "Microsoft YaHei", sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
        }}
        .nav {{
            background: #1a1d27;
            border-bottom: 1px solid var(--border);
            padding: 16px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav .brand {{
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }}
        .nav .links {{ display: flex; gap: 20px; }}
        .nav .links a {{
            color: var(--text-dim);
            text-decoration: none;
            font-size: 14px;
            transition: color 0.2s;
        }}
        .nav .links a:hover {{ color: var(--accent2); }}

        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}

        /* Header */
        .header {{
            text-align: center;
            padding: 30px 0;
            margin-bottom: 30px;
        }}
        .header .logo {{ font-size: 36px; margin-bottom: 8px; }}
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header p {{ color: var(--text-dim); font-size: 14px; }}

        /* KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .kpi-card .icon {{ font-size: 28px; margin-bottom: 8px; }}
        .kpi-card .value {{ font-size: 32px; font-weight: 700; color: var(--accent2); }}
        .kpi-card .label {{ font-size: 13px; color: var(--text-dim); margin-top: 4px; }}

        /* Chart Cards */
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(560px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
        }}
        .chart-card h3 {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chart-card canvas {{ max-height: 350px; }}

        /* Full width chart */
        .chart-full {{
            grid-column: 1 / -1;
        }}

        /* Tags / Lists */
        .tag-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 8px 0;
        }}
        .tag-item {{
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 13px;
            background: rgba(108,92,231,0.12);
            color: var(--accent2);
            border: 1px solid var(--border);
            cursor: default;
            transition: all 0.2s;
        }}
        .tag-item:hover {{
            background: rgba(108,92,231,0.25);
        }}
        .tag-item .count {{
            margin-left: 4px;
            font-size: 11px;
            color: var(--text-dim);
        }}

        /* Ranked list */
        .ranked-list {{ list-style: none; }}
        .ranked-list li {{
            display: flex;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
        }}
        .ranked-list li:last-child {{ border-bottom: none; }}
        .ranked-list .rank {{
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 700;
            margin-right: 12px;
            flex-shrink: 0;
        }}
        .rank.r1 {{ background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: #fff; }}
        .rank.r2 {{ background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #fff; }}
        .rank.r3 {{ background: linear-gradient(135deg, #00b894, #00cec9); color: #fff; }}
        .rank.normal {{ background: var(--border); color: var(--text-dim); }}
        .ranked-list .name {{ flex: 1; font-size: 14px; }}
        .ranked-list .bar {{
            width: 120px;
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            overflow: hidden;
            margin: 0 12px;
        }}
        .ranked-list .bar-fill {{
            height: 100%;
            border-radius: 3px;
            background: linear-gradient(90deg, var(--accent), var(--accent2));
        }}
        .ranked-list .count {{ font-size: 13px; color: var(--text-dim); min-width: 24px; text-align: right; }}

        /* Source table */
        .source-table {{ width: 100%; border-collapse: collapse; }}
        .source-table th, .source-table td {{
            padding: 10px 12px;
            text-align: left;
            font-size: 14px;
        }}
        .source-table th {{
            color: var(--text-dim);
            font-weight: 500;
            border-bottom: 2px solid var(--border);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .source-table td {{ border-bottom: 1px solid var(--border); }}
        .source-table tr:last-child td {{ border-bottom: none; }}
        .source-table .total-row {{ font-weight: 600; }}

        .footer {{
            text-align: center;
            padding: 30px 0;
            border-top: 1px solid var(--border);
            margin-top: 30px;
            color: var(--text-dim);
            font-size: 13px;
        }}
        .footer a {{ color: var(--accent2); text-decoration: none; }}

        @media (max-width: 768px) {{
            .container {{ padding: 20px 12px; }}
            .chart-grid {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 22px; }}
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="../index.html" class="brand">🧱 Republic Zhu</a>
            <div class="links">
                <a href="../index.html">← 返回首页</a>
                <a href="../index.html">日报</a>
                <a href="https://republic-zhu.com" target="_blank">官网</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="header">
            <div class="logo">📊</div>
            <h1>游戏行业数据看板</h1>
            <p>基于公众号日报自动聚合 · 数据持续积累中</p>
        </div>

        <!-- KPI Cards -->
        <div class="kpi-grid" id="kpiGrid"></div>

        <!-- Charts -->
        <div class="chart-grid">
            <div class="chart-card chart-full">
                <h3>📈 每日文章数趋势</h3>
                <canvas id="trendChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>📊 各公众号发文分布</h3>
                <canvas id="sourceChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>🎮 游戏提及排行榜</h3>
                <ul class="ranked-list" id="gameList"></ul>
            </div>
            <div class="chart-card chart-full">
                <h3>🏷️ 热点关键词云</h3>
                <div class="tag-list" id="keywordCloud"></div>
            </div>
        </div>

        <!-- Source Detail Table -->
        <div class="chart-card" style="margin-bottom: 30px;">
            <h3>📋 公众号详细数据</h3>
            <table class="source-table" id="sourceTable">
                <thead>
                    <tr>
                        <th>公众号</th>
                        <th>总文章数</th>
                        <th>占比</th>
                        <th>日均产出</th>
                        <th>覆盖天数</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>

        <div class="footer">
            <p>数据来源：9 个游戏行业公众号 · AI 自动抓取聚合</p>
            <p style="margin-top:8px">Powered by 小柱子 AI · 持续更新中</p>
        </div>
    </div>

<script>
const DATA = {data_json};

// Chart.js defaults
Chart.defaults.color = '#8a8d9a';
Chart.defaults.borderColor = '#2a2d3a';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "SF Pro SC", "PingFang SC", sans-serif';

const colors = ['#6c5ce7', '#a29bfe', '#00b894', '#fdcb6e', '#ff6b6b', '#00cec9', '#e17055', '#74b9ff', '#d63031', '#0984e3', '#e84393', '#55efc4'];

// KPI Cards
const kpis = [
    {{ icon: '📰', value: DATA.totalArticles, label: '累计文章数' }},
    {{ icon: '📅', value: DATA.dates.length, label: '覆盖天数' }},
    {{ icon: '📡', value: DATA.totalSources, label: '覆盖公众号' }},
    {{ icon: '🎮', value: DATA.topGames.length, label: '提及游戏数' }},
];
const kpiGrid = document.getElementById('kpiGrid');
kpis.forEach(k => {{
    kpiGrid.innerHTML += `
        <div class="kpi-card">
            <div class="icon">${{k.icon}}</div>
            <div class="value">${{k.value}}</div>
            <div class="label">${{k.label}}</div>
        </div>
    `;
}});

// Trend Chart
new Chart(document.getElementById('trendChart'), {{
    type: 'line',
    data: {{
        labels: DATA.dates.map(d => d.substring(5)),
        datasets: [{{
            label: '每日文章数',
            data: DATA.dateCounts,
            borderColor: '#6c5ce7',
            backgroundColor: 'rgba(108,92,231,0.1)',
            fill: true,
            tension: 0.4,
            pointRadius: 6,
            pointHoverRadius: 8,
            pointBackgroundColor: '#6c5ce7',
            borderWidth: 3,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{
                backgroundColor: '#1a1d27',
                borderColor: '#2a2d3a',
                borderWidth: 1,
                titleColor: '#e2e4ed',
                bodyColor: '#a29bfe',
                padding: 12,
                cornerRadius: 8,
            }}
        }},
        scales: {{
            x: {{ grid: {{ display: false }} }},
            y: {{
                beginAtZero: true,
                grid: {{ color: '#2a2d3a' }},
                ticks: {{ stepSize: 2 }}
            }}
        }}
    }}
}});

// Source Distribution Chart
const sourceEntries = Object.entries(DATA.sourceTotals).sort((a, b) => b[1] - a[1]);
new Chart(document.getElementById('sourceChart'), {{
    type: 'doughnut',
    data: {{
        labels: sourceEntries.map(s => s[0]),
        datasets: [{{
            data: sourceEntries.map(s => s[1]),
            backgroundColor: colors,
            borderWidth: 0,
            hoverOffset: 8,
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        cutout: '55%',
        plugins: {{
            legend: {{
                position: 'bottom',
                labels: {{ padding: 12, usePointStyle: true, pointStyle: 'circle', font: {{ size: 11 }} }}
            }}
        }}
    }}
}});

// Game Rankings
const gameList = document.getElementById('gameList');
const maxGameCount = DATA.topGames.length > 0 ? DATA.topGames[0].count : 1;
DATA.topGames.forEach((g, i) => {{
    const rank = i + 1;
    const rankClass = rank <= 3 ? `r${{rank}}` : 'normal';
    const pct = (g.count / maxGameCount * 100).toFixed(0);
    gameList.innerHTML += `
        <li>
            <span class="rank ${{rankClass}}">${{rank}}</span>
            <span class="name">《${{g.name}}》</span>
            <span class="bar"><span class="bar-fill" style="width: ${{pct}}%"></span></span>
            <span class="count">${{g.count}}</span>
        </li>
    `;
}});

// Keyword Cloud
const cloud = document.getElementById('keywordCloud');
const maxKwCount = DATA.topKeywords.length > 0 ? DATA.topKeywords[0].count : 1;
DATA.topKeywords.forEach(kw => {{
    const size = 12 + (kw.count / maxKwCount * 16);
    const opacity = 0.3 + (kw.count / maxKwCount * 0.7);
    cloud.innerHTML += `
        <span class="tag-item" style="font-size: ${{size}}px; opacity: ${{opacity}};">
            ${{kw.name}}<span class="count">${{kw.count}}</span>
        </span>
    `;
}});

// Source Detail Table
const tbody = document.querySelector('#sourceTable tbody');
const totalArticles = DATA.totalArticles;
const numDays = DATA.dates.length;
sourceEntries.forEach((s, i) => {{
    const pct = (s[1] / totalArticles * 100).toFixed(1);
    const avg = (s[1] / numDays).toFixed(1);
    // Count days this source was active
    let activeDays = 0;
    DATA.dates.forEach(d => {{
        if (DATA.dateSourceCount[d] && DATA.dateSourceCount[d][s[0]] > 0) activeDays++;
    }});
    tbody.innerHTML += `
        <tr>
            <td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${{colors[i % colors.length]}};margin-right:8px;"></span>${{s[0]}}</td>
            <td>${{s[1]}}</td>
            <td>${{pct}}%</td>
            <td>${{avg}}</td>
            <td>${{activeDays}}/${{numDays}}</td>
        </tr>
    `;
}});
// Total row
tbody.innerHTML += `
    <tr class="total-row">
        <td>合计</td>
        <td>${{totalArticles}}</td>
        <td>100%</td>
        <td>${{(totalArticles / numDays).toFixed(1)}}</td>
        <td>${{numDays}}/${{numDays}}</td>
    </tr>
`;
</script>
</body>
</html>'''
    
    return html

def main():
    # Collect all articles
    all_articles = []
    for fname in sorted(os.listdir(REPORTS_DIR)):
        if not fname.endswith('.html'):
            continue
        path = os.path.join(REPORTS_DIR, fname)
        articles = extract_articles(path)
        print(f"  {fname}: {len(articles)} articles")
        all_articles.extend(articles)
    
    print(f"\nTotal: {len(all_articles)} articles extracted")
    
    # Build dashboard
    dashboard_html = build_dashboard(all_articles)
    
    # Save to dashboards directory
    os.makedirs(os.path.join(SITE_DIR, 'dashboards'), exist_ok=True)
    output_path = os.path.join(SITE_DIR, 'dashboards', 'industry-dashboard.html')
    with open(output_path, 'w') as f:
        f.write(dashboard_html)
    
    print(f"Dashboard saved to: {output_path}")

if __name__ == '__main__':
    main()
