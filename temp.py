import sqlite3

def delete_entries_by_range(db_file="korean_dict.db"):
    # 建立連線
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    try:
        c.execute("VACUUM")
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"資料庫操作出錯：{e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 在執行前建議先備份一份資料庫檔案，以免誤刪
    delete_entries_by_range()