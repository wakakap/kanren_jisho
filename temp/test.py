import sqlite3
import re
import tkinter as tk
from tkinter import ttk

# 函数：去掉读音中的长音（ー）和促音（っ）
def normalize_reading(reading):
    """移除罗马音中的长音和促音，如 'taberu' -> 'tabe'"""
    return re.sub(r'[ーっ]', '', reading)

# 连接数据库
conn = sqlite3.connect("japanese_dict.db")
cursor = conn.cursor()

# 删除旧表
cursor.execute("DROP TABLE IF EXISTS dictionary")
cursor.execute("DROP TABLE IF EXISTS zh_to_jp")

# 创建主表 dictionary
cursor.execute('''CREATE TABLE dictionary
                  (word TEXT, reading TEXT, meaning TEXT, pos TEXT, 
                   particle TEXT, conjugations TEXT, example TEXT, level INTEGER,
                   reading_normalized TEXT)''')

# 创建中文到日文汉字转换表（三元形式）
cursor.execute('''CREATE TABLE zh_to_jp
                  (zh_simple TEXT,      -- 中文简体汉字
                   zh_traditional TEXT, -- 中文繁体汉字
                   jp_char TEXT)        -- 日文汉字
''')

# 主表数据
data = [
    ("食べる", "たべる, taberu", "吃", "动词", "を", "食べます, 食べた, 食べない", 
     "毎日ご飯を食べます。/ 我每天吃饭。", 0, normalize_reading("taberu")),
    ("食う", "くう, kuu", "吃", "动词", "を", "食います, 食った, 食わない", 
     "ラーメンを食う。/ 我吃拉面。", 0, normalize_reading("kuu")),
    ("食品", "しょくひん, shokuhin", "食品", "名词", "", "", 
     "スーパーで食品を買います。/ 我在超市买食品。", 0, normalize_reading("shokuhin")),
    ("食事", "しょくじ, shokuji", "饭菜", "名词", "する", "", 
     "夕食は食事の時間です。/ 晚饭是吃饭时间。", 0, normalize_reading("shokuji")),
    ("食堂", "しょくどう, shokudou", "食堂", "名词", "", "", 
     "学校の食堂で食べます。/ 我在学校食堂吃饭。", 0, normalize_reading("shokudou")),
    ("食物", "しょくもつ, shokumotsu", "食物", "名词", "", "", 
     "新鮮な食物が好きです。/ 我喜欢新鲜的食物。", 0, normalize_reading("shokumotsu")),
    ("食欲", "しょくよく, shokuyoku", "食欲", "名词", "", "", 
     "食欲がありません。/ 我没有食欲。", 0, normalize_reading("shokuyoku")),
    ("外食", "がいしょく, gaishoku", "外食", "名词", "する", "", 
     "いつも外食しています。/ 我经常外食。", 0, normalize_reading("gaishoku")),
    ("学ぶ", "まなぶ, manabu", "学习", "动词", "を", "学びます, 学んだ, 学ばない", 
     "日本語を学びます。/ 我学习日语。", 0, normalize_reading("manabu")),
    ("学生", "がくせい, gakusei", "学生", "名词", "", "", 
     "学生は教室にいます。/ 学生在教室里。", 0, normalize_reading("gakusei")),
    ("学校", "がっこう, gakkou", "学校", "名词", "", "", 
     "学校へ行きます。/ 我去学校。", 0, normalize_reading("gakkou")),
    ("学问", "がくもん, gakumon", "学问", "名词", "", "", 
     "学问を深めます。/ 我深入研究学问。", 0, normalize_reading("gakumon")),
]
cursor.executemany("INSERT INTO dictionary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)

# 创建索引
cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_reading ON dictionary(reading)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_reading_normalized ON dictionary(reading_normalized)")
conn.commit()

# 函数：将 query 中的中文汉字替换为日文汉字
def replace_zh_to_jp(query):
    """遍历 query 的每个字符，将中文简体或繁体替换为日文汉字，返回新字符串"""
    new_query = ""
    # 先加载 zh_to_jp 表到内存，提升效率
    cursor.execute("SELECT zh_simple, zh_traditional, jp_char FROM zh_to_jp")
    mapping = {row[0]: row[2] for row in cursor.fetchall()}  # 简体 -> 日文
    mapping.update({row[1]: row[2] for row in cursor.fetchall()})  # 繁体 -> 日文
    
    for char in query:
        # 如果字符在映射表中，替换为日文汉字，否则保持原样
        new_query += mapping.get(char, char)
    return new_query

# 搜索函数
def search_dictionary(query):
    """根据输入查询词典，返回匹配结果列表"""
    has_kanji = any('\u4e00' <= char <= '\u9fff' for char in query)
    results = []
    
    if has_kanji:
        new_query = replace_zh_to_jp(query)
        
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE word = ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (new_query,))
        results.extend(cursor.fetchall())
        
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE word LIKE ? AND word != ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (f"%{new_query}%", new_query))
        results.extend(cursor.fetchall())
        
        kanji_only = ''.join(c for c in new_query if '\u4e00' <= c <= '\u9fff')
        if kanji_only:
            cursor.execute("""
                SELECT * FROM dictionary 
                WHERE word = ? 
                ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
            """, (kanji_only,))
            results.extend(cursor.fetchall())
            
            cursor.execute("""
                SELECT * FROM dictionary 
                WHERE word LIKE ? AND word != ? 
                ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
            """, (f"%{kanji_only}%", kanji_only))
            results.extend(cursor.fetchall())
    
    else:
        normalized_query = normalize_reading(query)
        
        # A: 完全匹配（假名部分）
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE SUBSTR(reading, 1, INSTR(reading, ',') - 1) = ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (query,))
        results.extend(cursor.fetchall())
        
        # B: 含有字符（假名部分）
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE SUBSTR(reading, 1, INSTR(reading, ',') - 1) LIKE ? 
                  AND SUBSTR(reading, 1, INSTR(reading, ',') - 1) != ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (f"%{query}%", query))
        results.extend(cursor.fetchall())
        
        # A: 完全匹配（去长音促音的罗马音）
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE reading_normalized = ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (normalized_query,))
        results.extend(cursor.fetchall())
        
        # B: 含有字符（去长音促音的罗马音）
        cursor.execute("""
            SELECT * FROM dictionary 
            WHERE reading_normalized LIKE ? AND reading_normalized != ? 
            ORDER BY level ASC, CASE WHEN pos = '动词' THEN 0 ELSE 1 END
        """, (f"%{normalized_query}%", normalized_query))
        results.extend(cursor.fetchall())
    
    return results

# 界面搜索函数
def search():
    """从输入框获取查询词，调用 search_dictionary，显示结果"""
    query = entry.get().strip()
    if not query:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "请输入查询词！")
        return
    
    results = search_dictionary(query)
    result_text.delete(1.0, tk.END)
    
    if not results:
        result_text.insert(tk.END, "未找到匹配结果！")
    else:
        result_text.insert(tk.END, f"查询: {query}\n\n")
        for row in results:
            result_text.insert(tk.END, 
                f"单词: {row[0]}\n"
                f"读音: {row[1]}\n"
                f"意思: {row[2]}\n"
                f"词性: {row[3]}\n"
                f"级别: {row[7]}\n"
                f"例句: {row[6]}\n\n"
            )

# 创建界面
root = tk.Tk()
root.title("日语词典测试")
root.geometry("400x500")

tk.Label(root, text="输入查询词:").pack(pady=5)
entry = tk.Entry(root, width=30)
entry.pack(pady=5)

search_btn = tk.Button(root, text="搜索", command=search)
search_btn.pack(pady=5)

result_text = tk.Text(root, height=25, width=50)
result_text.pack(pady=10)

root.mainloop()

conn.close()