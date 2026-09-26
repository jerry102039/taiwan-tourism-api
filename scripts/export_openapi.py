"""匯出 API 規格文件到 docs/：
    - openapi.json / openapi.yaml ：OpenAPI 3 規格檔（可匯入 Postman、Bruno、Swagger Editor）
    - index.html                  ：不需啟動伺服器即可瀏覽的 Swagger UI 靜態頁（可放 GitHub Pages）

用法：python scripts/export_openapi.py
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

DOCS = ROOT / "docs"

SWAGGER_HTML = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Taiwan Tourism Open Data API - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    const spec = __SPEC__;
    SwaggerUIBundle({ spec, dom_id: "#swagger-ui", deepLinking: true, docExpansion: "none" });
  </script>
</body>
</html>
"""


def main() -> None:
    spec = app.openapi()
    spec["servers"] = [{"url": "http://127.0.0.1:8000", "description": "本機開發伺服器"}]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "openapi.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (DOCS / "openapi.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (DOCS / "index.html").write_text(
        SWAGGER_HTML.replace("__SPEC__", json.dumps(spec, ensure_ascii=False)), encoding="utf-8"
    )
    ops = sum(len(v) for v in spec["paths"].values())
    print(f"已匯出 {len(spec['paths'])} 個路徑、{ops} 個 API 操作 → docs/openapi.json, docs/openapi.yaml, docs/index.html")


if __name__ == "__main__":
    main()
