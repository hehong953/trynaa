import sqlite3
import random
from litestar import Litestar, get
from litestar.response import Response
from litestar.static_files import create_static_files_router
import json
from pathlib import Path

# 資料庫配置
DB_CONFIG = {
    "ja": "daijirin2.db",
    "ko": "korean_dict.db"
}

DATA_FILE = Path("history.json")

def save_quiz_result(result: dict, lang: str):
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # 統一儲存格式：kana/word 對應發音，kanji/hanja 對應漢字
    save_data = {
        "lang": lang,
        "word": result.get("kana") or result.get("word"),
        "extra": result.get("kanji") or result.get("hanja")
    }
    data.append(save_data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def query_db(db_key, sql, params=(), one=False):
    db_path = DB_CONFIG.get(db_key, DB_CONFIG[db_key])
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@get("/api/search")
async def search(word: str, lang: str, page: int = 1) -> dict:
    limit = 40
    offset = (page - 1) * limit
    w_contain = f"%{word}%"
    w_start = f"{word}%"
    
    # 根據語言決定欄位名稱
    col_main = "headword_kana" if lang == "ja" else "word"
    col_sub = "headword_kanji" if lang == "ja" else "hanja"

    count_sql = f"SELECT COUNT(*) as total FROM entries WHERE {col_main} LIKE ? OR {col_sub} LIKE ?"
    total_row = query_db(lang, count_sql, (w_contain, w_contain), one=True)
    total_count = total_row["total"] if total_row else 0
    total_pages = max(1, (total_count + limit - 1) // limit)

    sql = f"""
        SELECT id, {col_main}, {col_sub} FROM entries 
        WHERE {col_main} LIKE ? OR {col_sub} LIKE ?
        ORDER BY 
            CASE 
                WHEN {col_main} = ? OR {col_sub} = ? THEN 0
                WHEN {col_main} LIKE ? OR {col_sub} LIKE ? THEN 1
                ELSE 2
            END,
            {col_main} ASC
        LIMIT ? OFFSET ?
    """
    params = (w_contain, w_contain, word, word, w_start, w_start, limit, offset)
    results = query_db(lang, sql, params)
    
    output = []
    for r in results:
        main = r[col_main]
        sub = r[col_sub]
        # 如果漢字/漢字欄位與主詞條不同且不為空，則顯示括號
        display = main if (not sub or main == sub) else f"{main} ({sub})"
        output.append({"id": r["id"], "headword": display, "lang": lang})
        
    return {"results": output, "current_page": page, "total_pages": total_pages}

@get("/api/entry/{lang:str}/{entry_id:str}")
async def get_entry(lang: str, entry_id: str) -> Response:
    # 這裡的 entry_id 可能是數字字串，需確保查詢正確
    row = query_db(lang, "SELECT content FROM entries WHERE id = ?", (entry_id,), one=True)
    return Response(content=row["content"] if row else "<h3>未找到</h3>", media_type="text/html")

@get("/api/quiz/random")
async def get_random_quiz(lang: str = "ja") -> dict:
    col_main = "headword_kana" if lang == "ja" else "word"
    col_sub = "headword_kanji" if lang == "ja" else "hanja"

    # ja
    if lang == "ja":
        row = query_db(lang, f"SELECT * FROM entries WHERE {col_sub} IS NOT NULL AND {col_sub} != '' AND {col_main} NOT LIKE '@%' ORDER BY RANDOM() LIMIT 1", one=True)
        if not row: 
            row = query_db(lang, "SELECT * FROM entries ORDER BY RANDOM() LIMIT 1", one=True)
    else:  # ko
        row = query_db(lang, f"SELECT * FROM entries WHERE {col_sub} ORDER BY RANDOM() LIMIT 1", one=True)
        if not row: 
            row = query_db(lang, "SELECT * FROM entries ORDER BY RANDOM() LIMIT 1", one=True)
    
    main_val = row[col_main]
    sub_val = row[col_sub]

    if sub_val == "":
        sub_val = main_val

    # 獲取同音的其他詞
    other_rows = query_db(lang, f"SELECT DISTINCT {col_sub} FROM entries WHERE {col_main} = ?", (main_val,))
    sub_list = [r[col_sub] for r in other_rows if r[col_sub]]
    
    count = len(sub_list) - 1
    sub_str = "、".join(sub_list)

    result = {
        "kanji": main_val, 
        "kana": sub_val, 
        "content": row["content"], 
        "count": count, 
        "kanjiList": sub_str,
        "lang": lang
    }
    
    save_quiz_result(result, lang)
    return result

app = Litestar(route_handlers=[
    search, 
    get_entry, 
    get_random_quiz, 
    create_static_files_router(path="/", directories=["static"], html_mode=True)
])