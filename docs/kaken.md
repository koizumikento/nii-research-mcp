# KAKEN

## MCPツール

| ツール | 用途 |
| --- | --- |
| `search_projects` | `query` にキーワードを指定し、課題名・課題番号・詳細ページを探す |
| `get_project` | `project_number` に課題・領域番号を指定し、研究機関、研究期間、実施状況を調べる。`21K00001` と `JP21K00001` のどちらも指定可能 |
| `search_researchers` | `name` に研究者の名前を指定し、研究者番号・現在の所属などを探す。`affiliation` で所属機関を絞り込める |

検索は1〜20件ずつ取得でき、続きは返された `next_start` を `start` に指定します。課題番号の照会では、該当するレコードを `items` に返します。照会した範囲で完全一致がなければ空になります。


## 出典と利用条件

コードはMIT Licenseです。国立情報学研究所の科研費データベース KAKEN のOpenSearch APIを使用します。NIIのAPI利用細則では、自己の学術研究・非営利の情報利活用以外の目的には事前の申請と承認が必要です。取得した情報を利用する際は出典を記載してください。[公式API仕様](https://support.nii.ac.jp/ja/kaken/api/api_outline) · [KAKEN 利用規程](https://support.nii.ac.jp/ja/kaken/about/terms) · [NII ウェブAPI利用細則](https://support.nii.ac.jp/sites/default/files/cinii/webapi-term.pdf)
