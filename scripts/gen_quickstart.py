"""
記事に quickstart フィールドを追加。
個人事業主・社長が「明日からできる3ステップ＋プロンプト＋ツール＋コスト」を持てるようにする。
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))
from llm import chat_json, extract_json

QUICKSTART_PROMPT = """以下の不動産業界ニュース記事リストに対して、各記事に「不動産仲介・売買・賃貸・投資家・宅建士・工務店経営者が明日から自社で試せるアクション」を quickstart フィールドとして追加してください。

quickstart の構造:
{
  "headline": "明日から自社でこう使える、を15字以内で（例: 物件査定書を30分で完成）",
  "tool": {
    "name": "推奨ツール名（不動産業務に使えるAIツールやSaaS。例: ChatGPT Plus / Claude Pro / Gemini / SUUMO / アットホーム / 楽待 など実在ツール）",
    "url": "公式URL",
    "cost": "月額目安（例: 無料 / ¥3,000/月）"
  },
  "time": "試すのにかかる時間（例: 10分 / 30分 / 半日）",
  "steps": [
    "ステップ1：何をするか（25字以内・命令形）",
    "ステップ2：何をするか（25字以内・命令形）",
    "ステップ3：何をするか（25字以内・命令形）"
  ],
  "prompt": "コピペで即使えるChatGPT/Claudeプロンプト本体（150字以内・「あなたは〜」から始まり、{物件種別}{地域}{築年数}{顧客属性}など不動産業務の差し替え変数を{}付きで含める）",
  "roi": "想定効果（例: 査定書作成を月10時間削減＝3万円相当 / 反響メール返信を70%短縮）"
}

【重要ルール】
- 対象は「不動産仲介・売買・賃貸の現場担当／個人投資家／工務店・宅建士」
- 大手不動産会社向けの抽象論ではなく、明日からPCを開いて試せる具体性
- prompt は本当にコピペするだけで動くもの。{物件種別}{地域}{築年数}{顧客属性}{利回り目標}など不動産業務の変数を{}で明示
- 査定書・反響メール・物件紹介文・売却提案・賃貸契約書・内見スクリプト・投資シミュレーションなど、不動産業務に直結する用途を優先
- tool.url は実在の公式URLのみ
- ニュース内容と無関係に汎用的な提案にしない。記事の本質を活かす
- 全て日本語

入力の各記事の title・lede・keypoints・bizapp を参考に、JSON配列で返してください。順番は入力と同じ。

出力形式:
[
  {"headline": "...", "tool": {...}, "time": "...", "steps": [...], "prompt": "...", "roi": "..."},
  ...
]
"""


def generate_quickstart(articles: list[dict]) -> list[dict]:
    digest_parts = []
    for i, a in enumerate(articles):
        kp = "\n".join(f"  - {k}" for k in a.get("keypoints", []))
        bz = a.get("bizapp", {})
        bz_text = ""
        if bz:
            bz_text = f"bizapp.summary: {bz.get('summary','')}\nbizapp.actions: {bz.get('actions',[])}"
        digest_parts.append(
            f"[{i}] {a['title']}\n"
            f"lede: {a.get('lede','')}\n"
            f"keypoints:\n{kp}\n"
            f"{bz_text}"
        )
    digest = "\n\n".join(digest_parts)

    text = chat_json(
        system="あなたは日本のAI活用コンサルタントです。指示に従って厳密にJSONを返してください。",
        user=f"{QUICKSTART_PROMPT}\n\n記事リスト:\n{digest}",
        max_tokens=4500,
    )
    return json.loads(extract_json(text, "array"))


def process_file(path: Path, force: bool = False) -> bool:
    with open(path) as f:
        articles = json.load(f)

    if not force and all("quickstart" in a for a in articles):
        print(f"  SKIP (already done): {path.parent.name}")
        return False

    print(f"  Generating quickstart for {len(articles)} articles in {path.parent.name}...")
    qs_list = generate_quickstart(articles)

    for article, qs in zip(articles, qs_list):
        article["quickstart"] = qs

    with open(path, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"  DONE: {path.parent.name}")
    return True


if __name__ == "__main__":
    import sys
    base = Path("/Users/yamanakashuto/apps/vigil-news/docs/news")

    if len(sys.argv) > 1:
        # 単一日付指定
        target = base / sys.argv[1] / "articles.json"
        process_file(target, force=True)
    else:
        # 全件
        for p in sorted(base.glob("*/articles.json")):
            process_file(p)
