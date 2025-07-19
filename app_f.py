import streamlit as st
import sqlite3
from jamdict import Jamdict
import os

# --- 1. 初始化与配置 ---

# 获取app.py文件所在的绝对路径
# 这使得应用无论从哪里运行，都能找到正确的文件
APP_DIR = os.path.dirname(os.path.abspath(__file__))
JMD_XML_PATH = os.path.join(APP_DIR, 'JMdict.xml')
JMD_DB_PATH = os.path.join(APP_DIR, 'JMdict.db')
FAV_DB_PATH = os.path.join(APP_DIR, 'favorites.db')

def get_jamdict_instance():
    # 明确检查我们期望路径下的 XML 文件
    if not os.path.exists(JMD_XML_PATH):
        st.error(f"错误：找不到 '{JMD_XML_PATH}' 文件。请确保已下载该文件并放置在应用根目录。")
        return None

    try:
        # 使用绝对路径来初始化Jamdict，强制它在我们指定的文件夹中创建和使用数据库
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

# SQLite数据库连接，用于收藏夹
@st.cache_resource
def get_db_connection():
    # 使用绝对路径连接收藏夹数据库，确保它在应用文件夹内创建
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

# SQLite数据库连接，用于收藏夹
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect('favorites.db', check_same_thread=False)
    # 创建收藏表（如果不存在）
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites
        (id INTEGER PRIMARY KEY,
        word TEXT NOT NULL,
        reading TEXT,
        definition TEXT NOT NULL,
        UNIQUE(word, definition));
    ''')
    return conn

# --- 2. 核心功能：搜索与排序 ---
def search_word(jmd, query):
    """使用Jamdict进行搜索"""
    if not jmd or not query:
        return []
    # lookup()方法返回一个结果对象
    result = jmd.lookup(query, strict_lookup=False)
    return result.entries

def custom_sort(entries, query):
    """
    自定义排序逻辑。
    这是您施展才华的核心区域！
    """
    if not entries:
        return []

    def calculate_score(entry):
        score = 0
        # 规则1: 完全匹配查询字符串的条目优先级最高
        # entry.kanji有多个写法，entry.kana有多个读法
        kanji_forms = [k.text for k in entry.kanji_forms]
        kana_forms = [k.text for k in entry.kana_forms]
        if query in kanji_forms or query in kana_forms:
            score += 1000

        # 规则2: 常用词（比如 'ichi1', 'news1', 'spec1' 等）加分
        # entry.senses[0].misc 包含了词性、领域等信息
        if entry.senses:
            misc_info = " ".join(entry.senses[0].misc)
            if 'ichi1' in misc_info or 'news1' in misc_info or 'spec1' in misc_info:
                score += 500
        
        # 规则3: 汉字写法更少的词可能更基础，稍微加分
        score -= len(kanji_forms) * 10

        # 规则4: (示例) 如果汉字与查询词相同，提高优先级
        if query in kanji_forms:
             score += 200

        # <<< 在这里添加更多您自己的中文用户习惯规则 >>>
        # 例如：
        # - 如果词的汉字写法与简体中文一致，加分
        # - 如果是动词，根据不同活用类型调整分数
        # - ...

        return score

    # 使用sorted函数和我们计算的分数进行降序排序
    sorted_entries = sorted(entries, key=calculate_score, reverse=True)
    return sorted_entries

# --- 3. 收藏夹数据库操作 ---
def add_to_favorites(conn, entry):
    """将词条添加到收藏夹"""
    word = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
    reading = entry.kana_forms[0].text if entry.kana_forms else ""
    # 将所有释义合并成一个字符串
    definition = "; ".join([f"{i+1}. {s.text()}" for i, s in enumerate(entry.senses)])
    
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO favorites (word, reading, definition) VALUES (?, ?, ?)", 
                       (word, reading, definition))
        conn.commit()
        st.toast(f"'{word}' 已添加到收藏夹！")
        # 添加这一行来强制刷新界面
        st.rerun() 
    except sqlite3.IntegrityError:
        st.toast(f"'{word}' 已在收藏夹中。")
    except Exception as e:
        st.error(f"添加失败: {e}")


def get_favorites(conn):
    """从数据库获取所有收藏"""
    cursor = conn.cursor()
    cursor.execute("SELECT word, reading, definition FROM favorites ORDER BY id DESC")
    return cursor.fetchall()

def remove_from_favorites(conn, word, definition):
    """从收藏夹移除词条"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE word = ? AND definition = ?", (word, definition))
        conn.commit()
        st.toast(f"'{word}' 已从收藏夹移除。")
        # 使用 rerun 来强制刷新界面状态
        st.rerun()
    except Exception as e:
        st.error(f"移除失败: {e}")


# --- 4. Streamlit 用户界面 ---
st.set_page_config(page_title="我的日语词典", layout="wide")

# 加载实例
jmd = get_jamdict_instance()
conn = get_db_connection()

# --- 侧边栏：显示收藏夹 ---
with st.sidebar:
    st.title("⭐ 收藏夹")
    favorites = get_favorites(conn)
    if not favorites:
        st.info("这里还没有收藏的单词。")
    
    for fav in favorites:
        word, reading, definition = fav
        with st.container(border=True):
            st.markdown(f"**{word}** `{reading}`")
            st.caption(definition.replace("; ", "\n- "))
            # 为每个收藏项创建一个唯一的key，以便正确处理删除操作
            if st.button("移除", key=f"del_{word}_{definition}"):
                remove_from_favorites(conn, word, definition)

# --- 主界面 ---
st.title("📖 我的定制日语词典")
st.markdown("一个基于 `Python` + `Streamlit` 构建，可自定义排序的日语词典。")

# 搜索框
search_query = st.text_input("输入日语单词、假名或汉字进行搜索：", "")

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
            # 为了简化，我们只取第一个汉字和假名形式
            word_display = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
            reading_display = entry.kana_forms[0].text if entry.kana_forms else ""
            
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"{word_display} `{reading_display}`")
                    # 显示所有释义
                    for i, sense in enumerate(entry.senses):
                        st.markdown(f"**{i+1}.** {sense.text()}")
                
                with col2:
                    # 添加到收藏夹的按钮
                    if st.button("⭐ 收藏", key=f"add_{word_display}_{reading_display}_{entry.idseq}"):
                        add_to_favorites(conn, entry)

elif not jmd:
    st.error("词典数据未能成功加载，请检查控制台错误信息。")

