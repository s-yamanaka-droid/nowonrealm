"""Now on REALm 朝刊を Slack #朝刊 に送信。"""
import json
import os
import sys
import requests
from datetime import datetime, date
from pathlib import Path

SLACK_TOKEN = os.environ.get("SLACK_TOKEN", "") or os.environ.get("SLACK_BOT_TOKEN", "")
CHANNEL = os.environ.get("SLACK_DAILY_CHANNEL", "C0B3M8YB1B9")
MENTION = "<@U0A5ALYDKMZ>"
SITE_URL = os.environ.get("NOW_ON_SITE_URL", "https://s-yamanaka-droid.github.io/nowonrealm/")
BRAND = os.environ.get("NOW_ON_BRAND", "REALm")

ROOT = Path(__file__).parent.parent
TARGET = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

articles_path = ROOT / "docs" / "news" / TARGET / "articles.json"
if not articles_path.exists():
    print(f"[skip] {articles_path} なし"); sys.exit(0)
if not SLACK_TOKEN:
    raise RuntimeError("SLACK_TOKEN 未設定")

articles = json.loads(articles_path.read_text(encoding="utf-8"))

trend = "本日の不動産業界ニュースをお届けします。"
weekly_files = sorted((ROOT / "docs" / "weekly").glob("*.json"), reverse=True)
if weekly_files:
    try:
        trend = json.loads(weekly_files[0].read_text(encoding="utf-8")).get("trend_summary", trend)
    except Exception: pass

top5_lines = []
for i, a in enumerate(articles[:5], 1):
    title = a.get("title", "")[:60]
    source = a.get("source", "")
    summary = a.get("lede", "")[:80]
    link = (a.get("links") or [""])[0]
    line = f"{i}. *[{source}]* {title}"
    if summary: line += f"\n    _{summary}_"
    if link: line += f"\n    🔗 <{link}|元記事を読む>"
    top5_lines.append(line)
top5_text = "\n\n".join(top5_lines)

date_str = datetime.strptime(TARGET, "%Y-%m-%d").strftime("%Y/%m/%d")
blocks = [
    {"type": "header", "text": {"type": "plain_text", "text": f"🏘 Now on {BRAND} — {date_str}"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": f"{MENTION} おはようございます！本日 6:35 配信の不動産業界ニュースです。"}},
    {"type": "divider"},
    {"type": "section", "text": {"type": "mrkdwn", "text": f"*📊 今週のトレンド総評*\n{trend}"}},
    {"type": "divider"},
    {"type": "section", "text": {"type": "mrkdwn", "text": f"*🔥 Top 5 ピックアップ*\n\n{top5_text}"}},
    {"type": "divider"},
    {"type": "context", "elements": [{"type": "mrkdwn", "text": f"🏘 *Now on {BRAND}* — Real Estate Morning Intelligence · 毎朝6:35 JST · <{SITE_URL}|サイトを見る>"}]},
]
resp = requests.post("https://slack.com/api/chat.postMessage",
    headers={"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"},
    json={"channel": CHANNEL, "blocks": blocks}, timeout=15)
resp.raise_for_status()
if not resp.json().get("ok"): raise RuntimeError(f"Slack APIエラー: {resp.json().get('error')}")
print(f"✓ Slack #朝刊 配信完了 Now on {BRAND} ({TARGET}, {len(articles[:5])}件)")
