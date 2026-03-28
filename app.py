import sqlite3
import random
from litestar import Litestar, get
from litestar.response import Response
from litestar.static_files import create_static_files_router
import json
from pathlib import Path

DB_NAME = "daijirin2.db"

DATA_FILE = Path("history.json")

def save_quiz_result(result: dict):
    # 讀取原本資料
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    result = {
        "kana": result["kana"],
        "kanji": result["kanji"]
    }

    data.append(result)

    # 寫回檔案
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
def query_db(sql, params=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@get("/api/search")
async def search(word: str, page: int = 1) -> dict:
    limit = 40
    offset = (page - 1) * limit
    w_contain = f"%{word}%"
    w_start = f"{word}%"
    
    count_sql = "SELECT COUNT(*) as total FROM entries WHERE headword_kana LIKE ? OR headword_kanji LIKE ?"
    total_row = query_db(count_sql, (w_contain, w_contain), one=True)
    total_count = total_row["total"] if total_row else 0
    total_pages = max(1, (total_count + limit - 1) // limit)

    sql = """
        SELECT id, headword_kana, headword_kanji FROM entries 
        WHERE headword_kana LIKE ? OR headword_kanji LIKE ?
        ORDER BY 
            CASE 
                WHEN headword_kana = ? OR headword_kanji = ? THEN 0
                WHEN headword_kana LIKE ? OR headword_kanji LIKE ? THEN 1
                ELSE 2
            END,
            headword_kana ASC
        LIMIT ? OFFSET ?
    """
    params = (w_contain, w_contain, word, word, w_start, w_start, limit, offset)
    results = query_db(sql, params)
    
    output = []
    for r in results:
        kana = r["headword_kana"]
        kanji = r["headword_kanji"]
        display = kana if kana == kanji else f"{kana} ({kanji})"
        output.append({"id": r["id"], "headword": display})
        
    return {"results": output, "current_page": page, "total_pages": total_pages}

@get("/api/entry/{entry_id:str}")
async def get_entry(entry_id: str) -> Response:
    row = query_db("SELECT content FROM entries WHERE id = ?", (entry_id,), one=True)
    return Response(content=row["content"] if row else "<h3>未找到</h3>", media_type="text/html")

@get("/api/quiz/random")
async def get_random_quiz() -> dict:
    # 測驗優先挑選有漢字差異的
    row = query_db("SELECT * FROM entries WHERE headword_kana != headword_kanji ORDER BY RANDOM() LIMIT 1", one=True)
    if not row: row = query_db("SELECT * FROM entries ORDER BY RANDOM() LIMIT 1", one=True)
    kana = row["headword_kana"]

    kanji_rows = query_db(
        "SELECT DISTINCT headword_kanji FROM entries WHERE headword_kana = ?",
        (kana,)
    )
    kanji_list = [r["headword_kanji"] for r in kanji_rows]
    count = len(kanji_list) - 1
    kanji_str = "、".join(kanji_list)

    #sql = "SELECT COUNT(*) as cnt FROM entries WHERE headword_kana = ?"
    #result = query_db(sql, (row["headword_kana"],), one=True)
    #count = int(result["cnt"]) -1 if result else 0

    result = {"kana": row["headword_kana"], "kanji": row["headword_kanji"], "content": row["content"], "count": count, "kanjiList": kanji_str}
    save_quiz_result(result)
    return result

app = Litestar(route_handlers=[search, get_entry, get_random_quiz, create_static_files_router(path="/", directories=["static"], html_mode=True)])