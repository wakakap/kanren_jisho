import sqlite3
import opencc
import re

# 初始化 OpenCC 转换器
s2t_converter = opencc.OpenCC('s2t')  # 简体转繁体
t2s_converter = opencc.OpenCC('t2s')  # 繁体转简体

# 函数：从日文汉字生成三元组
def generate_zh_to_jp_data(jp_chars):
    """
    从日文汉字列表生成 (简体, 繁体, 日文) 三元组。
    输入：jp_chars - 日文汉字字符串（全角空格分隔）
    输出：zh_to_jp_data - 三元组列表
    """
    zh_to_jp_data = []
    
    # 使用全角空格（U+3000）分割
    jp_char_list = re.split(r'　', jp_chars.strip())
    
    for jp_char in jp_char_list:
        if not jp_char:  # 跳过空字符串
            continue
        # 尝试将日文汉字转为中文简体和繁体
        zh_simple = t2s_converter.convert(jp_char)
        zh_traditional = s2t_converter.convert(jp_char)
        
        # 如果简体和繁体相同且与日文不同，可能是日文特有汉字
        if zh_simple == zh_traditional and zh_simple != jp_char:
            zh_simple = jp_char  # 保留原字符作为简体
        
        # 添加三元组
        zh_to_jp_data.append((zh_simple, zh_traditional, jp_char))
    
    return zh_to_jp_data

# 读取 TXT 文件
def read_jp_chars_from_file(file_path):
    """从 TXT 文件读取日文汉字"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

# 主程序
def main():
    # 文件路径（假设文件名为 jp_chars.txt）
    file_path = "./kanji/jyouyou_list.txt"
    
    # 读取日文汉字
    jp_chars = read_jp_chars_from_file(file_path)
    
    # 生成三元组数据
    zh_to_jp_data = generate_zh_to_jp_data(jp_chars)
    
    # 连接数据库
    conn = sqlite3.connect("KANJI_MAP_STJ.db")
    cursor = conn.cursor()
    
    # 创建 zh_to_jp 表
    cursor.execute("DROP TABLE IF EXISTS zh_to_jp")
    cursor.execute('''CREATE TABLE zh_to_jp
                      (zh_simple TEXT, zh_traditional TEXT, jp_char TEXT)''')
    
    # 插入数据
    cursor.executemany("INSERT INTO zh_to_jp VALUES (?, ?, ?)", zh_to_jp_data)
    conn.commit()

    # 可选：打印前几条数据检查
    cursor.execute("SELECT * FROM zh_to_jp LIMIT 5")
    print("前 5 条数据：")
    for row in cursor.fetchall():
        print(row)
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    main()