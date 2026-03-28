import sqlite3
import re
import os
from bs4 import BeautifulSoup
from lxml import etree

def clean_html(raw_html):
    """清除 HTML 標籤，返回純文字"""
    return re.sub(r'<[^>]+>', '', raw_html).strip()

def filter_kanji_field(text):
    """
    處理漢字欄位邏輯：
    1. 刪除 ▼ ▽ 【 】 〈 〉
    #2. 將 ・ 改為 空格
    """
    if not text: return ""
    # 刪除指定符號
    text = re.sub(r'[▼▽【】〈〉]', '', text)
    # 將中點改為空格
    #text = text.replace('・', ' ')
    # 處理可能產生的連續空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def init_database(txt_file, db_file="daijirin2.db"):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    c.execute('DROP TABLE IF EXISTS entries')
    c.execute('''
        CREATE TABLE entries (
            id TEXT PRIMARY KEY, 
            headword_kana TEXT, 
            headword_kanji TEXT,
            content TEXT
        )
    ''')
    
    print(f"正在讀取 {txt_file} ...")
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            data = f.read()
    except UnicodeDecodeError:
        with open(txt_file, 'r', encoding='utf-16') as f:
            data = f.read()

    pattern = re.compile(r'@(.*?)\n(.*?)\n</>', re.DOTALL)
    entries = pattern.findall(data)
    
    print(f"找到 {len(entries)} 個區塊，正在深度解析...")
    
    to_insert = []

    for entry_id, content in entries:
        parser = etree.HTMLParser()
        tree = etree.HTML(content, parser=parser)
        
        # 見出仮名
        node = tree.xpath('//span[@data-name="見出仮名"]')
        if node:
            target = node[0]
            raw_text = ''.join(target.itertext())
            cleaned = raw_text.replace(" ", "").replace("　", "")
            headword_kana = cleaned.replace("・", "")
            headword_kana = re.sub(r'[◦〈〉▼▽\（\）—\s]', '', headword_kana)
            
            # 標準表記
            node2 = tree.xpath('//span[@data-name="標準表記"]')
            if node2:
                # 直接用 itertext() 展開巢狀 span
                headword_kanji = ''.join(node2[0].itertext())
                headword_kanji = re.sub(r'\s|・', '', headword_kanji)
                headword_kanji = re.sub(r'[◦〈〉▼▽\（\）—\s]', '', headword_kanji)  # 去掉空白和中點
            else:
                headword_kanji = headword_kana
        else:
            # 慣用語處理
            ku_match = re.search(r'<span data-name="句表記">(.*?)</span>', content)
            headword_kana = clean_html(ku_match.group(1)).replace('・', '') if ku_match else entry_id
            headword_kanji = filter_kanji_field(headword_kana)
        
        # 確保都是字串
        to_insert.append((
            str(entry_id),
            str(headword_kana),
            str(headword_kanji),
            str(content)
        ))
    
    c.executemany('INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?)', to_insert)
    c.execute('CREATE INDEX idx_kana ON entries(headword_kana)')
    c.execute('CREATE INDEX idx_kanji ON entries(headword_kanji)')
    
    conn.commit()
    conn.close()
    print(f"tetetet")

if __name__ == "__main__":
    target_txt = "daijirin2.txt"
    if os.path.exists(target_txt):
        init_database(target_txt)