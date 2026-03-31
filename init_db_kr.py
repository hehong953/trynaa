import sqlite3
import re
import os

def clean_word_only(text):
    """
    徹底清除 Word 欄位中的漢字
    1. 刪除 【 】 及其內部的文字
    2. 刪除任何殘留的漢字字元 (CJK Ideographs)
    """
    if not text: return ""
    # 刪除所有 【 】 及其內部的文字
    text = re.sub(r'【.*?】', '', text)
    # 刪除所有漢字字元 (範圍: \u4e00-\u9fff)
    text = re.sub(r'[\u4e00-\u9fff]', '', text)
    return text.strip()

def extract_hanja_with_comma(text, content):
    """
    從詞條頭部和內容中提取所有 【】 內的文字，並用逗號隔開
    """
    full_text = text + content
    # 尋找所有 【 】 內的內容
    hanja_list = re.findall(r'【(.*?)】', full_text)
    
    # 去除重複項並用逗號結合 (使用 filter 確保沒有空字串)
    unique_hanja = []
    for h in hanja_list:
        h = h.strip()
        if h and h not in unique_hanja:
            unique_hanja.append(h)
            
    return ", ".join(unique_hanja)

def init_database(txt_file, db_file="korean_dict.db"):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute('DROP TABLE IF EXISTS entries')
    c.execute('''
        CREATE TABLE entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            word TEXT, 
            hanja TEXT,
            content TEXT
        )
    ''')
    
    print(f"正在讀取並處理 {txt_file} ...")
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            data = f.read()
    except UnicodeDecodeError:
        with open(txt_file, 'r', encoding='utf-16') as f:
            data = f.read()

    # 匹配模式：詞條行 + 縮排內容 + 結束符號 </>
    pattern = re.compile(r'^([^\n\t]+)\n\t(.*?)\n</>', re.DOTALL | re.MULTILINE)
    entries = pattern.findall(data)
    
    to_insert = []

    for raw_word, content in entries:
        # 1. 處理 Word：移除括號及所有漢字字元
        clean_word = clean_word_only(raw_word)
        
        # 2. 處理 Hanja：提取括號內容並以逗號分隔
        hanja_separated = extract_hanja_with_comma(raw_word, content)
        
        to_insert.append((
            clean_word,
            hanja_separated,
            content.strip()
        ))
    
    # 批量寫入資料庫
    c.executemany('INSERT INTO entries (word, hanja, content) VALUES (?, ?, ?)', to_insert)
    
    # 建立索引
    c.execute('CREATE INDEX idx_word ON entries(word)')
    c.execute('CREATE INDEX idx_hanja ON entries(hanja)')
    
    conn.commit()
    conn.close()
    print(f"處理完成！")
    print(f"資料庫：{db_file}")
    print(f"總筆數：{len(to_insert)}")

if __name__ == "__main__":
    # 請確保您的檔名正確
    target_txt = "韩语标准国语大辞典.txt" 
    if os.path.exists(target_txt):
        init_database(target_txt)
    else:
        print(f"找不到檔案: {target_txt}")