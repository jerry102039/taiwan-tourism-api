"""將 data/AttractionList.json 匯入 SQLite（data/tourism.db）。

用法：
    python scripts/import_data.py          # 資料庫為空時才匯入
    python scripts/import_data.py --reset  # 刪除所有資料表後重新匯入（會清除使用者新增的評論、行程）
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DB_FILE  # noqa: E402
from app.seed import init_db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="清空並重新匯入")
    args = parser.parse_args()
    result = init_db(reset=args.reset)
    if result is None:
        print(f"{DB_FILE} 已有資料，未重新匯入（如需重建請加 --reset）")
    else:
        print(f"匯入完成 → {DB_FILE}")
        for table, count in result.items():
            print(f"  {table:<22}{count:>6} 筆")


if __name__ == "__main__":
    main()
