# 衆院選2026 候補者一覧ページ

## 概要
- 2026年衆議院議員総選挙向けの候補者一覧ページを追加しました。
- 参議院選2025の候補者一覧ページと同じUI/UXで、検索・フィルタリング可能です。
- 「衆院選2026（政策要約）」ページから遷移できるようにリンクを追加しています。

## 追加ページ
- ルート: `/shugiin-candidates`
- 実装: `frontend/app/shugiin-candidates/page.tsx`

## データソース
- 読み込みファイル: `frontend/public/data/shugiin_candidates/shugiin_2026_candidates_latest.json`
- 取得方法: SPA対応の静的JSON（GitHub Pages対応、basePath付き）
- 優先ソース: **選挙ドットコム（go2senkyo.com）**
- 収集スクリプト: `scripts/uv-data-collection/collect_shugiin_2026_candidates.py`
  - 推奨実行: `uv run python collect_shugiin_2026_candidates.py --only-go2senkyo --enrich-party`
  - `--include-party-sites` を付けた場合のみ政党公式サイトを併用

## 収集範囲
- 小選挙区 + 比例代表（`hireiku/*/hirei_party/*/candidates` を解析）
- 不明政党はプロフィールページから補完（`--enrich-party`）

## 表示内容
- 候補者名
- 政党（バッジ）
- 選挙区名 + 選挙区タイプ
- 主要政策（`policy_positions` がある場合のみ）
- 外部リンク
  - `profile_url`（プロフィール詳細）
  - `source_url`（データ元）

## 検索・フィルター
- 候補者名／政党名／選挙区で検索
- 政党フィルター
- 選挙区タイプフィルター
- 選挙区フィルター

## 政党名の統一
- 立憲民主党・公明党は「中道改革連合」に統一
- 政策ページは `https://craj.jp/party/policies/` を公式マニフェストとして使用

## 関連リンク追加
- `frontend/app/shugiin-manifestos/page.tsx` から候補者一覧へ遷移可能

## 補足
- Go2senkyo側の候補者公開状況に応じて更新されます。
- 候補者データが不足・不正確な場合は、収集スクリプトのHTML解析ロジックを見直します。
