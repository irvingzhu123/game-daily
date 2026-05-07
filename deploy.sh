#!/bin/bash
# 游戏日报自动部署脚本
# 每日生成 HTML → 更新站点 → 推送到 GitHub → 触发 Vercel 部署

SITE_DIR="/Users/irving/.openclaw/workspace/game-daily-site"
SKILL_DIR="/Users/irving/.openclaw/workspace/skills/game-daily-report"
TODAY=$(date +"%Y-%m-%d")

# 1. 生成今日日报 HTML
python3 "$SKILL_DIR/scripts/game_daily.py" > /tmp/today_articles.json 2>/dev/null

# 2. 检查是否有新文章
if [ "$(cat /tmp/today_articles.json)" = "NO_NEW_ARTICLES" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') [deploy] 无新增文章" >> /tmp/game_daily.log
  exit 0
fi

ARTICLE_COUNT=$(cat /tmp/today_articles.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
echo "$(date '+%Y-%m-%d %H:%M:%S') [deploy] 发现 $ARTICLE_COUNT 篇新文章" >> /tmp/game_daily.log

# 3. 将生成的 HTML 复制到站点目录
# (HTML 文件由 skill 生成后复制到 daily/ 目录)
if [ -f "$SKILL_DIR/reports/game-daily-$TODAY.html" ]; then
  cp "$SKILL_DIR/reports/game-daily-$TODAY.html" "$SITE_DIR/daily/"
fi

# 4. 推送到 GitHub
cd "$SITE_DIR"
git add -A
git commit -m "📊 游戏行业日报 $TODAY" --allow-empty
git push origin main 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M:%S') [deploy] 已推送到 GitHub，Vercel 自动部署" >> /tmp/game_daily.log
