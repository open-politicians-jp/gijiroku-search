# マニフェストの要約


## 前提として
- 要約のアルゴリズム等は公開する
- 偏りのない要約に徹すること

## 対象
- 自民党：https://storage2.jimin.jp/pdf/pamphlet/202507_manifest.pdf
- 立憲民主党：https://cdp-japan.jp/election2025/visions/
- 日本維新の会：https://o-ishin.jp/policy/
  - https://o-ishin.jp/policy/pdf/2025_core_policy.pdf
  - https://o-ishin.jp/policy/pdf/2025_election_manifesto.pdf
  - https://o-ishin.jp/policy/pdf/ishin_8saku2025.pdf
  - https://o-ishin.jp/policy/pdf/2025_lower_social_insurance_premiums.pdf
- 公明党：https://www.komei.or.jp/content/manifesto2025_02/
- 日本共産党：https://www.jcp.or.jp/cms/wp-content/uploads/2025/06/202506_sanin_seisaku.pdf
- 国民民主党：https://new-kokumin.jp/policies
- れいわ新撰組：https://reiwa-shinsengumi.com/policy/
  - https://reiwa-shinsengumi.com/wp-content/uploads/2025/02/%E3%82%8C%E3%81%84%E3%82%8F%E6%96%B0%E9%81%B8%E7%B5%84%E5%9F%BA%E6%9C%AC%E6%94%BF%E7%AD%96.pdf
- 参政党：https://sanseito.jp/pdf/pillar/ten_pillar.pdf
  - https://sanseito.jp/political_measures_2025/specific_policies/
- 日本保守党：https://hoshuto.jp/policy/
- チームみらい：https://policy.team-mir.ai/view/README.md
  - githubで公開しているのでそれを取得するでも良さそう


## 要約するために
- PDFの政党に関して
  - PDFからできる限り文字列を抽出して要約をすること

- リンクが複数あり、PDFもある場合
  - リンク先内容、PDFの内容どちらも必ず文字列抽出して要約をすること

- リンクが有効でないと判断できた場合(AI対策的な)
  - 各政党のマニフェスト相当＝政策(2025とついているなど)についてのへーじを検索してください
  - また対象と記載している政党が全部ではないため可能なかぎり参院選に出馬している政党のマニフェストを集めてください
    - 補足に今回の参議院選に参戦しているとされる政党を記載しました


## 政党単位で要約する
- 各政策に対して
  - 例として物価高に言及している場合物価高というラベル(タグ)とタイトルをつけること
  - ポジティブなら○(賛成)、ネガティブならX(反対)、どちらでもないは△として中立
- 要約したものは、政党単位で残しておく

## 簡略した対比表を作成する
- 機械的な判断で比較表を作成したとする文言付きで対比表を作成してほしい
- comparison.mdに対比表を記載するようにしてください

## 重要
- 決して偏見・傾倒をしないこと、客観的に中立的な要約に徹すること
- 出力先
  - output
    - summary.md：政党別に要約を
    - comparison.md：対比表


# 補足
参政党
立憲民主党
国民民主党
NHK党
自由民主党
日本共産党
れいわ新選組
日本改革党
日本保守党
チームみらい
日本維新の会
国政ガバナンスの会
公明党
社会民主党
日本誠真会
日本の家庭を守る会
新党やまと
再生の道
差別撲滅党
核融合党
減税日本
税金とうめい化の党（自分ことしか考えていない国会議員退場の党）
新党くにも