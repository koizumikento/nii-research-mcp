# CiNii Research

## MCPツール

| ツール | 用途 |
| --- | --- |
| `search_articles` | 論文だけをキーワード検索する |
| `search_records` | 全件を横断検索するか、`kind` で対象を選ぶ |
| `get_record` | 検索結果の `crid` で、CiNiiが公開するJSON-LDのメタデータを取得する |

`search_records` の `kind` で対象を選べます。

| 指定値 | 対象 |
| --- | --- |
| `all` | すべて（既定） |
| `data` | 研究データ |
| `articles` | 論文 |
| `books` | 本 |
| `dissertations` | 博士論文 |
| `projects` | プロジェクト |
| `researchers` | 研究者 |
| `projectsAndProducts` | 課題・成果 |

検索は1〜50件ずつ取得でき、続きは返された `next_start` を `start` に指定します。`get_record` に渡すのはURLの `/crid/` に続く数字です。取得できる項目はレコードによって異なります。


## データの出典と利用条件

書誌情報の取り扱いはNIIと提供元の利用条件に従ってください。商用サイトでの利用を希望する場合は、申請前にNIIへ連絡してください。[OpenSearch仕様](https://support.nii.ac.jp/ja/cir/r_opensearch)・[JSON-LD仕様](https://support.nii.ac.jp/ja/cir/r_json)・[ウェブAPI利用細則](https://support.nii.ac.jp/sites/default/files/cinii/webapi-term.pdf)・[CiNii Research利用細則](https://support.nii.ac.jp/sites/default/files/cinii/ciniir-term.pdf)

MIT Licenseはこのリポジトリのコードに適用します。
