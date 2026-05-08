#!/bin/bash
# 游戏日报自动部署脚本
# 每日自动抓取 → 生成 HTML → 更新首页 → 推送 GitHub → Vercel 自动部署

SKILL_DIR="/Users/irving/.openclaw/workspace/skills/game-daily-report"
SITE_DIR="/Users/irving/.openclaw/workspace/game-daily-site"
TODAY=$(date +"%Y-%m-%d")
LOG_FILE="/tmp/game_daily_deploy.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 开始日报部署 =====" >> "$LOG_FILE"

# 1. 检查 WeWe RSS 状态
SETUP_RESULT=$(cd "$SKILL_DIR" && /usr/bin/python3 scripts/setup_wewe_rss.py 2>&1)
PHASE=$(echo "$SETUP_RESULT" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('phase',''))" 2>/dev/null || echo "error")

if [ "$PHASE" != "ready" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ WeWe RSS 未就绪 (phase=$PHASE)，跳过" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 部署终止 =====" >> "$LOG_FILE"
  exit 1
fi
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ WeWe RSS 就绪" >> "$LOG_FILE"

# 2. 抓取新文章
ARTICLES=$(/usr/bin/python3 "$SKILL_DIR/scripts/game_daily.py" 2>&1)
echo "$ARTICLES" > /tmp/today_articles.json

if [ "$ARTICLES" = "NO_NEW_ARTICLES" ] || [ -z "$ARTICLES" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')]  无新增文章" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 部署终止 =====" >> "$LOG_FILE"
  exit 0
fi

ARTICLE_COUNT=$(echo "$ARTICLES" | /usr/bin/python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📄 发现 $ARTICLE_COUNT 篇新文章" >> "$LOG_FILE"

# 3. 检查是否已生成今日 HTML
HTML_FILE="$SKILL_DIR/reports/game-daily-$TODAY.html"
if [ ! -f "$HTML_FILE" ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 今日 HTML 尚未生成，请先手动触发日报生成" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 部署终止 =====" >> "$LOG_FILE"
  exit 1
fi

# 4. 复制到站点目录
cp "$HTML_FILE" "$SITE_DIR/daily/$TODAY.html"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 HTML 已复制到站点目录" >> "$LOG_FILE"

# 5. 推送 GitHub
cd "$SITE_DIR"
git add -A
git commit -m "📊 游戏行业日报 $TODAY (自动部署)" --allow-empty 2>/dev/null
PUSH_RESULT=$(git push origin main 2>&1)
PUSH_CODE=$?

if [ $PUSH_CODE -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')]  推送成功 → GitHub → Vercel 自动部署" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 部署完成 =====" >> "$LOG_FILE"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 推送失败: $PUSH_RESULT" >> "$LOG_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 部署失败 =====" >> "$LOG_FILE"
  exit 1
fi
