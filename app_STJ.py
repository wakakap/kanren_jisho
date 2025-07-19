import streamlit as st
import sqlite3
from jamdict import Jamdict
import os
import opencc

# --- 1. 初始化与配置 ---

# 获取app.py文件所在的绝对路径，确保文件引用准确无误
APP_DIR = os.path.dirname(os.path.abspath(__file__))
JMD_XML_PATH = os.path.join(APP_DIR, 'JMdict.xml')
JMD_DB_PATH = os.path.join(APP_DIR, 'JMdict.db')
FAV_DB_PATH = os.path.join(APP_DIR, 'favorites.db')

# --- 数据库与词典实例加载 (使用Streamlit缓存提高性能) ---

# @st.cache_resource 这里不注销会报错
def get_jamdict_instance():
    """加载Jamdict词典实例。如果数据库不存在，则从XML文件创建。"""
    if not os.path.exists(JMD_XML_PATH):
        st.error(f"错误：找不到 '{JMD_XML_PATH}' 文件。请确保已下载该文件并放置在应用根目录。")
        return None
    try:
        jmd = Jamdict(
            db_file=JMD_DB_PATH,
            jmd_xml_file=JMD_XML_PATH,
            cache_db=False,
            connect_args={'check_same_thread': False}
        )
        return jmd
    except Exception as e:
        st.error(f"加载词典数据时发生错误。请检查 '{JMD_XML_PATH}' 文件是否有效。详细错误: {e}")
        return None

@st.cache_resource
def get_favorites_db_connection():
    """获取收藏夹数据库的连接。"""
    conn = sqlite3.connect(FAV_DB_PATH, check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites
        (id INTEGER PRIMARY KEY,
        word TEXT NOT NULL,
        reading TEXT,
        definition TEXT NOT NULL,
        UNIQUE(word, definition));
    ''')
    return conn

# app.py

# --- 2. 核心功能：汉字转换、搜索与排序 ---

@st.cache_data
def convert_to_japanese_char(input_char, area='Simplified'):
    """
    使用 opencc 将单个中文字符转换为日文新字体汉字。
    area 参数决定了源语言区域。
    """
    # 为了提升性能，将转换器实例缓存起来
    if area == 'Simplified':
        converter1 = opencc.OpenCC('s2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        return converter2.convert(converter1.convert(input_char))
    elif area == 'Traditional':
        converter1 = opencc.OpenCC('hk2t.json') # 通用繁体
        return converter1.convert(input_char)
    elif area == 'Taiwan Traditional':
        converter1 = opencc.OpenCC('tw2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        return converter2.convert(converter1.convert(input_char))
    elif area == 'Hong Kong variant':
        converter1 = opencc.OpenCC('hk2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        return converter2.convert(converter1.convert(input_char))
    else:
        return input_char # 如果区域错误，返回原字符

def replace_zh_to_jp(query):
    """
    遍历查询字符串的每个字符，如果字符是中文，则替换为对应的日文汉字。
    默认使用简体中文作为转换源。
    """
    # 这里我们默认使用 'Simplified' 区域进行转换，您可以根据需要进行修改
    # 例如，可以在界面上增加一个选项让用户选择输入的是哪种中文
    return "".join([convert_to_japanese_char(char, 'Simplified') for char in query])

def search_word(jmd, query):
    """
    使用Jamdict进行搜索。现在使用opencc进行实时转换。
    """
    if not jmd or not query:
        return []

    # 检查查询中是否包含汉字
    has_kanji = any('\u4e00' <= char <= '\u9fff' for char in query)
    
    # 如果包含汉字，则进行简繁体 -> 日文汉字的转换
    translated_query = replace_zh_to_jp(query) if has_kanji else query
    
    # 使用原始查询和转换后的查询同时进行搜索
    result = jmd.lookup(query, strict_lookup=False)
    
    if translated_query != query:
        translated_result = jmd.lookup(translated_query, strict_lookup=False)
        all_entries = {entry.idseq: entry for entry in result.entries}
        for entry in translated_result.entries:
            all_entries[entry.idseq] = entry
        return list(all_entries.values())

    return result.entries

def custom_sort(entries, query):
    """
    排序算法，同样使用 opencc 进行实时转换以用于评分。
    """
    if not entries:
        return []

    has_kanji = any('\u4e00' <= char <= '\u9fff' for char in query)
    final_query = replace_zh_to_jp(query) if has_kanji else query

    def calculate_score(entry):
        score = 0
        kanji_forms = [k.text for k in entry.kanji_forms]
        kana_forms = [k.text for k in entry.kana_forms]

        # 核心匹配规则
        if final_query in kanji_forms:
            score += 10000
        elif any(k.startswith(final_query) for k in kanji_forms):
            score += 5000
            for k in kanji_forms:
                if k.startswith(final_query):
                    score += int(100 * (len(final_query) / len(k)))

        if query in kana_forms:
            score += 1000
            
        # 辅助加分规则
        if entry.senses:
            misc_info = " ".join(entry.senses[0].misc)
            if 'ichi1' in misc_info or 'news1' in misc_info or 'spec1' in misc_info:
                score += 500
        
        if kanji_forms:
            score -= len(kanji_forms[0]) * 10

        return score

    sorted_entries = sorted(entries, key=calculate_score, reverse=True)
    return sorted_entries

# --- 3. 收藏夹数据库操作 (与原版相同，无需修改) ---
def add_to_favorites(conn, entry):
    word = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
    reading = entry.kana_forms[0].text if entry.kana_forms else ""
    definition = "; ".join([f"{i+1}. {s.text()}" for i, s in enumerate(entry.senses)])
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO favorites (word, reading, definition) VALUES (?, ?, ?)", (word, reading, definition))
        conn.commit()
        st.toast(f"'{word}' 已添加到收藏夹！")
        st.rerun()
    except sqlite3.IntegrityError:
        st.toast(f"'{word}' 已在收藏夹中。")
    except Exception as e:
        st.error(f"添加失败: {e}")

def get_favorites(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT word, reading, definition FROM favorites ORDER BY id DESC")
    return cursor.fetchall()

def remove_from_favorites(conn, word, definition):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE word = ? AND definition = ?", (word, definition))
        conn.commit()
        st.toast(f"'{word}' 已从收藏夹移除。")
        st.rerun()
    except Exception as e:
        st.error(f"移除失败: {e}")

# --- 4. Streamlit 用户界面 ---
st.set_page_config(page_title="我的智能日语词典", layout="wide")

# 加载实例和数据
jmd = get_jamdict_instance()
fav_conn = get_favorites_db_connection()

# --- 侧边栏：显示收藏夹 ---
with st.sidebar:
    st.title("⭐ 收藏夹")
    favorites = get_favorites(fav_conn)
    if not favorites:
        st.info("这里还没有收藏的单词。")
    
    for fav in favorites:
        word, reading, definition = fav
        with st.container(border=True):
            st.markdown(f"**{word}** `{reading}`")
            st.caption(definition.replace("; ", "\n- "))
            if st.button("移除", key=f"del_{word}_{definition}"):
                remove_from_favorites(fav_conn, word, definition)

# --- 主界面 ---
st.title("📖 我的智能日语词典")
st.markdown("支持简繁体中文自动转换，并采用智能排序。")

# 搜索框
search_query = st.text_input("输入日语、假名或简/繁体汉字进行搜索：", "")

if search_query and jmd:
    # 执行搜索和排序
    raw_results = search_word(jmd, search_query)
    sorted_results = custom_sort(raw_results, search_query)

    st.divider()
    
    if not sorted_results:
        st.warning(f"找不到与 '{search_query}' 相关的结果。")
    else:
        st.success(f"找到 {len(sorted_results)} 条结果：")
        
        # 显示结果
        for entry in sorted_results:
            word_display = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
            reading_display = entry.kana_forms[0].text if entry.kana_forms else ""
            
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"{word_display} `{reading_display}`")
                    for i, sense in enumerate(entry.senses):
                        st.markdown(f"**{i+1}.** {sense.text()}")
                
                with col2:
                    if st.button("⭐ 收藏", key=f"add_{entry.idseq}"):
                        add_to_favorites(fav_conn, entry)

elif not jmd:
    st.error("词典数据未能成功加载，请检查控制台错误信息。")
