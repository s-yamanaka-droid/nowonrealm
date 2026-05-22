"""
Now on REALm - Researcher
不動産・住宅・REIT関連の RSS フィードからニュースを収集。
"""
import feedparser
import requests
import json
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ── 不動産・住宅・REIT・建設・PropTech RSS ──
RSS_FEEDS = [
    # 主要不動産メディア
    ("SUUMOジャーナル",        "https://suumo.jp/journal/feed/"),
    ("楽待新聞",              "https://www.rakumachi.jp/news/feed"),
    ("ZUU online 不動産",      "https://zuuonline.com/category/real-estate/feed"),
    # 業界紙
    ("住宅新報",              "https://www.jutaku-s.com/feed"),
    ("R.E.port",              "https://www.re-port.net/rss/"),
    # 投資・REIT
    ("Real Estate Capital",   "https://www.recapnews.com/feed/"),
    ("不動産投資の楽待",        "https://www.rakumachi.jp/news/category/column/feed"),
    # 海外 PropTech
    ("Inman",                 "https://www.inman.com/feed/"),
    ("PropTech Today",        "https://www.proptechtoday.com/feed/"),
    # 建設・住宅
    ("新建ハウジング",          "https://www.s-housing.jp/feed"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

SKIP_TAGS = {"script", "style", "nav", "header", "footer",
             "aside", "form", "button", "noscript", "iframe"}

SEEN_FILE = Path(__file__).parent.parent / "seen_urls.json"


def _load_seen() -> set[str]:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _save_seen(urls: set[str]):
    SEEN_FILE.write_text(json.dumps(sorted(urls), ensure_ascii=False), encoding="utf-8")


def mark_seen(urls: list[str]):
    seen = _load_seen()
    seen.update(urls)
    _save_seen(seen)
    print(f"[seen] {len(seen)}件のURLを既読登録済み")


def _fetch_body(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup.find_all(list(SKIP_TAGS)):
            tag.decompose()
        # 本文っぽい要素を優先
        article = soup.find("article") or soup.find("main") or soup.body
        if not article:
            return ""
        text = article.get_text(separator="\n", strip=True)
        return text[:3000]
    except Exception:
        return ""


def fetch_latest(max_per_feed: int = 3, fetch_body: bool = True) -> list[dict]:
    seen = _load_seen()
    results = []
    skipped = 0

    for source_name, feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"  [{source_name}] feed error: {e}")
            continue

        count = 0
        for entry in parsed.entries:
            if count >= max_per_feed:
                break
            link = entry.get("link", "").strip()
            if not link or link in seen:
                skipped += 1
                continue

            title   = entry.get("title", "").strip()
            summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
            body    = _fetch_body(link) if fetch_body else ""

            results.append({
                "source":  source_name,
                "title":   title,
                "summary": summary[:500],
                "link":    link,
                "body":    body,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
            count += 1

    print(f"[researcher] 収集:{len(results)}件 / スキップ(既出):{skipped}件")
    return results


if __name__ == "__main__":
    r = fetch_latest(max_per_feed=2, fetch_body=False)
    for a in r[:5]:
        print(f"[{a['source']}] {a['title']}")
