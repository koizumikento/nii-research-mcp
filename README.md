# nii-research-mcp

CiNii Researchの論文・研究データと、KAKENの科研費・研究者情報を調べるMCPサーバーです。MCP、CLI、Pythonライブラリから同じ機能を使えます。

[準備](#準備) · [MCP登録](#mcpクライアントに登録する) · [CLI](#cliで使う) · [Python](#pythonで使う) · [移行手順](docs/migration.md)

## 準備

Python 3.12以上、[uv](https://docs.astral.sh/uv/)、Gitが必要です。

```sh
git clone https://github.com/koizumikento/nii-research-mcp.git
cd nii-research-mcp
uv sync --locked
```

各自が登録したNIIのアプリケーションIDを使います。CiNii Researchには `CINII_APP_ID`、KAKENには `KAKEN_APP_ID` を設定してください。

```powershell
$env:CINII_APP_ID = "YOUR_CINII_APP_ID"
$env:KAKEN_APP_ID = "YOUR_KAKEN_APP_ID"
```

macOSやLinuxでは次のように設定します。

```sh
export CINII_APP_ID="YOUR_CINII_APP_ID"
export KAKEN_APP_ID="YOUR_KAKEN_APP_ID"
```

## MCPクライアントに登録する

設定例の `/absolute/path/to/nii-research-mcp` をクローン先の絶対パスに置き換えます。Windowsでは `C:/projects/nii-research-mcp` のように書けます。

### Codex

```sh
codex mcp add nii-research-mcp --env CINII_APP_ID=YOUR_CINII_APP_ID --env KAKEN_APP_ID=YOUR_KAKEN_APP_ID -- uv --directory "/absolute/path/to/nii-research-mcp" run --locked nii-research-mcp
codex mcp list
```

新しいセッションで `/mcp` を開いて接続状態を確認します。

### Claude Desktop / Cursor

Claude DesktopはOSに応じて次のファイルに設定します。

- Windowsは `%APPDATA%/Claude/claude_desktop_config.json`
- macOSは `~/Library/Application Support/Claude/claude_desktop_config.json`

Cursorはプロジェクト内の `.cursor/mcp.json` を使います。`mcpServers` に次の項目を追加し、クライアントを再起動してください。

```json
{
  "mcpServers": {
    "nii-research-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/nii-research-mcp",
        "run",
        "--locked",
        "nii-research-mcp"
      ],
      "env": {
        "CINII_APP_ID": "YOUR_CINII_APP_ID",
        "KAKEN_APP_ID": "YOUR_KAKEN_APP_ID"
      }
    }
  }
}
```

`uv` が見つからない場合は、`command` に実行ファイルの絶対パスを指定してください。

## ツール

データごとの入力条件、結果、出典と利用条件は、表のリンク先に記載しています。

| ツール | データと操作の説明 |
| --- | --- |
| `search_articles` | [CiNii Research](docs/cinii.md) |
| `search_records` | [CiNii Research](docs/cinii.md) |
| `get_record` | [CiNii Research](docs/cinii.md) |
| `search_projects` | [KAKEN](docs/kaken.md) |
| `search_researchers` | [KAKEN](docs/kaken.md) |
| `get_project` | [KAKEN](docs/kaken.md) |

## CLIで使う

クローン先で実行します。取得結果はUTF-8のJSONとして標準出力に書き出します。

```sh
uv run nii-research-mcp cinii search-articles --query 地震 --limit 3
uv run nii-research-mcp kaken search-projects --query 防災 --limit 3
```

引数の説明は、各サブコマンドに `--help` を付けて確認できます。

## Pythonで使う

自分のPythonプロジェクトの依存関係に追加します。

```sh
uv add "git+https://github.com/koizumikento/nii-research-mcp.git@main"
```

次のコードを `example.py` に保存し、`uv run python example.py` で実行します。

```python
import asyncio

from nii_research_mcp import search_articles

result = asyncio.run(search_articles(query="地震", limit=3))
print(result)
```

ツールと同じ名前の非同期関数を利用できます。すでにイベントループがある場合は、直接 `await` してください。

## 出典と利用条件

コードはMITライセンスです。データは実行時に各提供元から取得します。取得データには、データ別の説明に記載した提供元の利用条件が適用されます。

## 開発

```sh
uv sync --locked
uv run ruff check .
uv run ty check
uv run pytest
uv build
```
