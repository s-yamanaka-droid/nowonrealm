"""
Now on REALm — Generator
元記事本文をLLMに渡してファクトグラウンドな要約を生成する（不動産業界版）
"""
import json

SYSTEM = """あなたは不動産業界ニュースを「日本の不動産プロ／投資家／経営者」に届ける専門編集者です。
与えられた記事の【元記事本文】を一次情報として使い、ニュースサイト掲載用データをJSON配列で返してください。

出力形式（JSON配列）:
[
  {
    "title": "見出し（日本語・40字以内）",
    "category": "カテゴリ（市況/政策・税制/PropTech/投資・REIT/賃貸/海外動向/その他）",
    "source": "ソース名",
    "lede": "リード文（日本語・100字以内・核心を一文で）",
    "keypoints": ["要点1（30字以内）", "要点2", "要点3", "要点4"],
    "pull": "プルクォート（60字以内・本質的な洞察を）",
    "bizapp": {
      "summary": "このニュースを不動産ビジネスでどう活かすか（60字以内・結論ファースト）",
      "actions": [
        "売買・仲介：現場での具体アクション（30字以内）",
        "投資・資産運用：投資家視点の判断材料（30字以内）",
        "注目理由：なぜ今これを知っておくべきか（30字以内）"
      ]
    },
    "links": ["元記事URL"],
    "likes": 0
  }
]

【文章スタイルの指針】
- 対象読者：不動産仲介・売買・賃貸・投資家・宅建士・工務店経営者・REIT投資家
- 専門用語（LTV・キャップレート・REIT・ロードファクター等）は使ってOK、ただし初出時は括弧で簡単補足
- 「自分の物件・顧客・地域にどう影響するか」が伝わる書き方
- 抽象論より「価格・利回り・規制・テクノロジー」など現場判断材料を優先
- 見出しは新聞一面のように、読んだ瞬間に内容がわかる表現

【bizapp の書き方】
- summary：「〇〇に使える」「〇〇が変わる」など結論ファースト
- actions[0] 売買・仲介：内見・査定・契約・販促・顧客提案など現場視点
- actions[1] 投資・資産運用：物件選定・利回り判断・出口戦略・税対策
- actions[2] 注目理由：金利・規制・人口動態・テック等のマクロ要因

【厳守ルール】
- 上位8件を重要度順で選ぶ（日本の不動産ビジネス文脈で影響が大きい順）
- 全て日本語
- 【元記事本文】に書かれていない事実・数字・固有名詞は絶対に追加しない
- 本文が空の場合はタイトルとRSS要約だけを根拠にする
- 同じトピックの記事は1本にまとめる"""


def generate_articles(raw_articles: list[dict]) -> list[dict]:
    from llm import chat_json, extract_json
    # 記事ごとに元本文を含めた情報を構築
    blocks = []
    for a in raw_articles[:24]:
        body_part = f"\n【元記事本文】\n{a['body'][:1500]}" if a.get("body") else ""
        blocks.append(
            f"[{a['source']}] {a['title']}\n"
            f"RSS要約: {a['summary'][:200]}\n"
            f"URL: {a.get('link','')}"
            f"{body_part}"
        )
    digest = "\n\n---\n\n".join(blocks)

    text = chat_json(
        system=SYSTEM,
        user=f"今日のAI関連記事:\n\n{digest}",
        max_tokens=6000,
    )
    return json.loads(extract_json(text, "array"))


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.home() / "agents/cmo/x_agent"))
    from researcher import fetch_latest
    raw = fetch_latest(max_per_feed=3, fetch_body=True)
    articles = generate_articles(raw)
    print(json.dumps(articles, ensure_ascii=False, indent=2))
