import json
import sqlite3
import os
from tqdm import tqdm

# --- 配置 ---
# 请确保这个文件名与你下载的文件名完全一致
JSON_FILE_PATH = 'jmdict-examples-eng-3.6.2.json'
DB_FILE_PATH = 'JMdict_new.db' # 这是将要生成的新数据库文件名
TABLE_NAME = 'entries'

def create_database_schema(cursor):
    """创建数据库表和索引"""
    print("Creating database schema...")
    # 使用 IF NOT EXISTS 确保脚本可以重复运行而不会报错
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY,
        is_common INTEGER NOT NULL,
        main_kanji TEXT,
        main_kana TEXT NOT NULL,
        all_kanji_forms TEXT NOT NULL,
        all_kana_forms TEXT NOT NULL,
        all_senses TEXT NOT NULL
    )
    ''')
    
    # 为常用的搜索字段创建索引，这对App的查询性能至关重要！
    print("Creating indexes for faster search...")
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_main_kanji ON {TABLE_NAME} (main_kanji)')
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_main_kana ON {TABLE_NAME} (main_kana)')
    print("Schema and indexes are ready.")

def process_and_insert_data(cursor, words_data):
    """处理JSON数据并插入数据库"""
    print(f"Processing {len(words_data)} entries...")
    
    # 使用 executemany 进行批量插入，性能更高
    entries_to_insert = []
    
    # 使用 tqdm 创建一个进度条
    for word in tqdm(words_data, desc="Converting entries"):
        try:
            word_id = int(word.get('id', 0))

            # 确定 is_common：只要kanji或kana中有一个是common，整个词条就是common
            is_common_flag = False
            if word.get('kanji'):
                is_common_flag = any(k.get('common', False) for k in word['kanji'])
            if not is_common_flag and word.get('kana'):
                is_common_flag = any(k.get('common', False) for k in word['kana'])
            is_common_int = 1 if is_common_flag else 0

            # 提取主要的kanji和kana（通常是第一个）
            main_kanji = word['kanji'][0]['text'] if word.get('kanji') else None
            # kana 应该总是存在
            main_kana = word['kana'][0]['text'] if word.get('kana') else ''

            # 将列表/对象转换为JSON字符串以便存储
            # ensure_ascii=False 对于正确存储日语至关重要
            kanji_forms_json = json.dumps(word.get('kanji', []), ensure_ascii=False)
            kana_forms_json = json.dumps(word.get('kana', []), ensure_ascii=False)
            senses_json = json.dumps(word.get('sense', []), ensure_ascii=False)

            entries_to_insert.append((
                word_id,
                is_common_int,
                main_kanji,
                main_kana,
                kanji_forms_json,
                kana_forms_json,
                senses_json
            ))
        except Exception as e:
            print(f"Skipping entry due to error: {e}, data: {word}")

    print("Inserting all entries into the database. This may take a moment...")
    sql_insert = f'''
    INSERT INTO {TABLE_NAME} (id, is_common, main_kanji, main_kana, all_kanji_forms, all_kana_forms, all_senses)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    cursor.executemany(sql_insert, entries_to_insert)
    print("Insertion complete.")


def main():
    """主函数，执行整个转换过程"""
    # 如果旧的数据库文件存在，先删除，确保每次都生成全新的文件
    if os.path.exists(DB_FILE_PATH):
        print(f"Removing old database file: {DB_FILE_PATH}")
        os.remove(DB_FILE_PATH)
        
    conn = None
    try:
        # 1. 连接到SQLite数据库（如果不存在，会自动创建）
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()

        # 2. 创建表结构和索引
        create_database_schema(cursor)

        # 3. 读取并解析JSON文件
        print(f"Loading JSON file: {JSON_FILE_PATH}...")
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        words_data = data.get('words', [])
        
        # 4. 处理数据并插入
        if words_data:
            process_and_insert_data(cursor, words_data)
        else:
            print("No 'words' data found in JSON file.")

        # 5. 提交事务
        print("Committing changes to the database...")
        conn.commit()
        print("Database conversion successful!")
        print(f"New database file created at: {DB_FILE_PATH}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 6. 关闭数据库连接
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == '__main__':
    main()