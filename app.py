import streamlit as st
import sqlite3
from jamdict import Jamdict
import os
import opencc
import re
from pykakasi import kakasi

# --- 1. 初始化与配置 (与之前相同) ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
JMD_XML_PATH = os.path.join(APP_DIR, 'JMdict.xml')
JMD_DB_PATH = os.path.join(APP_DIR, 'JMdict.db')
FAV_DB_PATH = os.path.join(APP_DIR, 'favorites.db')

COMMONALITY_SCORES = {
    'ichi1': 25, 'ichi2': 15, 'news1': 20, 'news2': 10,
    'gai1': 18, 'gai2': 8, 'spec1': 12, 'spec2': 5,
}
POS_SCORES = {'v': 10, 'adj': 8, 'adv': 6, 'n': 5}
RESULT_LIMIT = 30

# --- 2. 资源加载 (与之前相同) ---
# @st.cache_resource
def get_jamdict_instance():
    if not os.path.exists(JMD_XML_PATH):
        st.error(f"错误：找不到 '{JMD_XML_PATH}' 文件。")
        st.stop()
    try:
        return Jamdict(db_file=JMD_DB_PATH, jmd_xml_file=JMD_XML_PATH, connect_args={'check_same_thread': False})
    except Exception as e:
        st.error(f"加载词典数据时发生错误: {e}")
        st.stop()

@st.cache_resource
def get_kakasi_instance():
    return kakasi()

# --- 3. 核心功能 (与之前相同) ---
def is_romaji(text):
    return bool(re.match(r"^[a-zA-Zōūāīē]+$", text))

@st.cache_data
def convert_to_japanese_char(input_char, area='Simplified'):
    if area == 'Simplified':
        converter1 = opencc.OpenCC('s2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        return converter2.convert(converter1.convert(input_char))
    return input_char

def replace_zh_to_jp(query):
    return "".join([convert_to_japanese_char(char) for char in query])

def only_kanji(query):
    return "".join(re.findall(r'[\u4e00-\u9faf]', query))

def special_tolerant_convert(query):
    """
    (已更新) 更智能的特殊音变容错函数。
    1. 移除或添加促音 `っ`。
    2. 对片假名的长音 `ー` 容错。
    """
    variants = set()

    # --- 1. 促音 `っ` 的插入与删除 ---

    # 规则1: 如果存在促音，生成一个将其移除的版本
    if 'っ' in query:
        variants.add(query.replace('っ', ''))

    # 规则2: 在所有发音合法的位置尝试插入促音
    # 定义可以接在促音后面的假名 (k, s, t, p行)
    SOKUON_KANA = {
        'か', 'き', 'く', 'け', 'こ', 'きゃ', 'きゅ', 'きょ',
        'さ', 'し', 'す', 'せ', 'そ', 'しゃ', 'しゅ', 'しょ',
        'た', 'ち', 'つ', 'て', 'と', 'ちゃ', 'ちゅ', 'ちょ',
        'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ', 'ぴゃ', 'ぴゅ', 'ぴょ',
        'カ', 'キ', 'ク', 'ケ', 'コ', 'キャ', 'キュ', 'キョ',
        'サ', 'シ', 'ス', 'セ', 'ソ', 'シャ', 'シュ', 'ショ',
        'タ', 'チ', 'ツ', 'テ', 'ト', 'チャ', 'チュ', 'チョ',
        'パ', 'ピ', 'プ', 'ペ', 'ポ', 'ピャ', 'ピュ', 'ピョ'
    }
    for i in range(1, len(query)):
        # 如果当前位置的假名可以接在促音后，并且它前面不是一个促音
        if query[i] in SOKUON_KANA and query[i-1] != 'っ':
            # 生成插入促音后的新词
            new_variant = query[:i] + 'っ' + query[i:]
            variants.add(new_variant)
            
    return list(variants)

def get_commonality_score(entry):
    all_priorities = set()
    for form in entry.kanji_forms: all_priorities.update(form.pri)
    for form in entry.kana_forms: all_priorities.update(form.pri)
    return sum(COMMONALITY_SCORES.get(p, 0) for p in all_priorities)

def get_pos_score(entry):
    max_score = 0
    for sense in entry.senses:
        for pos in sense.pos:
            score = POS_SCORES.get(pos.split('-')[0], 1)
            if score > max_score: max_score = score
    return max_score

# --- 4. 数据库与UI辅助函数 (display_entries 有小调整) ---
def add_to_favorites(entry):
    word = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
    reading = entry.kana_forms[0].text if entry.kana_forms else ""
    definition = "; ".join([f"{i+1}. {s.text()}" for i, s in enumerate(entry.senses)])
    
    conn = sqlite3.connect(FAV_DB_PATH, check_same_thread=False)
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
    finally:
        conn.close()

def get_favorites():
    conn = sqlite3.connect(FAV_DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT word, reading, definition FROM favorites ORDER BY id DESC")
        return cursor.fetchall()
    finally:
        conn.close()

def remove_from_favorites(word, definition):
    conn = sqlite3.connect(FAV_DB_PATH, check_same_thread=False)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE word = ? AND definition = ?", (word, definition))
        conn.commit()
        st.toast(f"'{word}' 已从收藏夹移除。")
        st.rerun()
    except Exception as e:
        st.error(f"移除失败: {e}")
    finally:
        conn.close()
def set_search_query(query):
    """(新增) 用于建议词按钮的回调函数，设置新的搜索词"""
    st.session_state.next_search_query = query

def display_suggestions(entries):
    """(新增) 在指定容器中横向渲染建议词"""
    st.markdown("---")
    st.write("您是不是想找：")
    
    # 每行最多显示5个建议词
    cols = st.columns(5)
    col_idx = 0
    for entry in entries:
        word = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
        reading = entry.kana_forms[0].text if entry.kana_forms else ""
        
        # 使用回调函数来更新搜索框内容
        cols[col_idx].button(
            label=f"{word} `{reading}`", 
            key=f"sug_{entry.idseq}",
            on_click=set_search_query,
            args=(word,) # 将词语本身作为参数传递给回调
        )
        col_idx = (col_idx + 1) % 5

def find_sokuon_suggestions(jmd, query, exclude_ids):
    """(新增) 查找促音容错的建议词"""
    suggestion_entries = []
    found_sug_ids = set()

    # 生成促音容错的变体
    variants = special_tolerant_convert(query)
    
    for variant in variants:
        # 建议词不需要太多，限制一下数量
        if len(suggestion_entries) >= 5:
            break
        
        # 精确匹配这些变体
        lookup_result = jmd.lookup(variant)
        for entry in lookup_result.entries:
            # 确保不与主结果重复，并且建议结果自身不重复
            if entry.idseq not in exclude_ids and entry.idseq not in found_sug_ids:
                suggestion_entries.append(entry)
                found_sug_ids.add(entry.idseq)
                if len(suggestion_entries) >= 5:
                    break
    
    return suggestion_entries

def display_entries(entries):
    """(已修正) 在当前环境中绘制词条列表"""
    # with container: 被移除
    for entry in entries:
        word_display = entry.kanji_forms[0].text if entry.kanji_forms else entry.kana_forms[0].text
        reading_display = entry.kana_forms[0].text if entry.kana_forms else ""
        
        with st.container(border=True):
            res_col1, res_col2 = st.columns([4, 1])
            with res_col1:
                st.subheader(f"{word_display} `{reading_display}`")
                for i, sense in enumerate(entry.senses):
                    st.markdown(f"**{i+1}.** {sense.text()}")
            with res_col2:
                if st.button("⭐ 收藏", key=f"add_{entry.idseq}"):
                    add_to_favorites(entry)


# --- 5. Streamlit 用户界面 (核心修改区域) ---
st.set_page_config(page_title="我的智能日语词典", layout="wide")

jmd = get_jamdict_instance()
kks = get_kakasi_instance()

# 初始化会话状态
if 'search_status' not in st.session_state:
    st.session_state.search_status = 'INIT'
    st.session_state.search_query_input = ""
    st.session_state.search_query = ""
    st.session_state.processed_query = ""
    st.session_state.tier1_entries = []
    st.session_state.sokuon_suggestions = []
    st.session_state.tier2_entries = []
    st.session_state.tier3_entries = []
    st.session_state.found_ids = set()
    st.session_state.debug_log = []
    
# 这个逻辑必须在所有UI组件（尤其是st.text_input）被创建之前运行
if 'next_search_query' in st.session_state:
    st.session_state.search_query_input = st.session_state.next_search_query
    del st.session_state.next_search_query

# --- 侧边栏 (保持不变) ---
with st.sidebar:
    st.title("⭐ 收藏夹")
    favorites = get_favorites()
    if not favorites: st.info("这里还没有收藏的单词。")
    for fav in favorites:
        word, reading, definition = fav
        with st.container(border=True):
            st.markdown(f"**{word}** `{reading}`")
            st.caption(definition.replace("; ", "\n- "))
            if st.button("移除", key=f"del_{word}_{definition}"):
                remove_from_favorites(word, definition)

# --- 主界面 ---
st.title("📖 我的智能日语词典")
st.markdown("支持简/繁体中文、假名、罗马音输入，并采用智能分层搜索与排序。")

col_main, col_debug = st.columns([2, 1])

with col_main:
    # 绑定 text_input 的值为 session_state.search_query_input
    search_query = st.text_input("输入日语、假名、罗马音或简/繁体汉字进行搜索：", 
                                 key="search_query_input", # 使用key来绑定
                                 help="例如: taberu, 食べる, がっこう, 学校")
    
    st.markdown("---")
    tier1_placeholder = st.empty()
    suggestion_placeholder = st.empty() # <--- 新增建议词的占位符
    tier2_placeholder = st.empty()
    tier3_placeholder = st.empty()
    no_results_placeholder = st.empty()


with col_debug:
    st.markdown("### ⚙️ 搜索过程分析")
    debug_placeholder = st.empty()

# --- 主要搜索逻辑 ---

# 当用户输入新的搜索词时，进行验证并准备重置状态机
if search_query and search_query != st.session_state.search_query:
    
    # --- 新增的验证逻辑 ---
    # 判断输入是否为单个非汉字字符
    is_single_non_kanji = len(search_query) == 1 and not re.match(r'[\u4e00-\u9faf]', search_query)

    if is_single_non_kanji:
        # 如果是无效的短查询，则不启动搜索，只更新状态并显示提示
        st.session_state.search_query = search_query # 更新查询词以防止重复提示
        st.session_state.search_status = 'INVALID_INPUT' # 设置一个新状态
        # 清空上一轮的结果
        st.session_state.tier1_entries = []
        st.session_state.tier2_entries = []
        st.session_state.tier3_entries = []
        st.session_state.found_ids = set()
        st.session_state.debug_log = ["为提高效率，请输入一个以上的假名/字母，或一个汉字。"]

    else:
        # 如果是有效查询，则按原计划启动搜索状态机
        st.session_state.search_status = 'SEARCHING_TIER_1'
        st.session_state.search_query = search_query
        # 清空上一轮的结果
        st.session_state.tier1_entries = []
        st.session_state.tier2_entries = []
        st.session_state.tier3_entries = []
        st.session_state.found_ids = set()
        st.session_state.debug_log = []
        # 立即重跑以启动搜索流程的第一步
        st.rerun()

# --- 渲染逻辑 (无论处于哪个状态，都先根据当前 session_state 的内容渲染) ---
# 这个模块被移动到了计算逻辑之前
if st.session_state.search_query:
    # 渲染日志
    debug_placeholder.markdown("\n".join(st.session_state.debug_log))

    # 渲染 Tier 1 结果
    if st.session_state.tier1_entries:
        with tier1_placeholder.container():
            st.subheader("精确匹配结果")
            display_entries(st.session_state.tier1_entries)

    # --- 新增：渲染建议词 ---
    if st.session_state.sokuon_suggestions:
        with suggestion_placeholder.container():
            display_suggestions(st.session_state.sokuon_suggestions)
    
    # 渲染 Tier 2 结果
    if st.session_state.tier2_entries:
        with tier2_placeholder.container():
            st.subheader("前缀匹配结果")
            display_entries(st.session_state.tier2_entries)
            
    # 渲染 Tier 3 结果
    if st.session_state.tier3_entries:
        with tier3_placeholder.container():
            st.subheader("容错匹配结果")
            display_entries(st.session_state.tier3_entries)

    # 如果搜索完成且没有任何结果，显示提示
    if st.session_state.search_status == 'DONE' and not st.session_state.found_ids:
        no_results_placeholder.warning(f"找不到与 '{st.session_state.search_query}' 相关的结果。请尝试其他关键词。")
else:
    debug_placeholder.info("输入关键词后，这里会显示搜索和排序的详细步骤。")


# --- 状态机驱动的计算逻辑 (在渲染逻辑之后执行) ---
try:
    # 状态1: 正在搜索 Tier 1
    if st.session_state.search_status == 'SEARCHING_TIER_1':
        debug_log = st.session_state.debug_log
        
        # 0. 预处理 (只在第一步执行)
        debug_log.append(f"**原始输入:** `{st.session_state.search_query}`")
        if is_romaji(st.session_state.search_query):
            processed_query = kks.convert(st.session_state.search_query)[0]['hira']
            debug_log.append(f"**类型判断:** 罗马音 -> `{processed_query}`")
        else:
            processed_query = replace_zh_to_jp(st.session_state.search_query)
            if processed_query != st.session_state.search_query: debug_log.append(f"**类型判断:** 中文 -> `{processed_query}`")
            else: debug_log.append(f"**类型判断:** 日文")
        st.session_state.processed_query = processed_query
        
        # Tier 1: 完全匹配
        debug_log.append("\n---\n**层级 1: 完全匹配**\n---")
        lookup_result = jmd.lookup(st.session_state.processed_query)
        for entry in lookup_result.entries:
            if entry.idseq not in st.session_state.found_ids:
                st.session_state.tier1_entries.append(entry)
                st.session_state.found_ids.add(entry.idseq)
        debug_log.append(f"找到 {len(st.session_state.tier1_entries)} 个新结果。")
        # --- 新增：在这里查找建议词 ---
        debug_log.append("\n---\n**建议词: 查找促音容错**\n---")
        # 查找建议词，并确保它们不和已找到的精确匹配结果重复
        suggestions = find_sokuon_suggestions(jmd, st.session_state.processed_query, st.session_state.found_ids)
        st.session_state.sokuon_suggestions = suggestions
        debug_log.append(f"找到 {len(suggestions)} 个建议词。")
        # --- 建议词查找结束 ---
        
        st.session_state.search_status = 'SEARCHING_TIER_2'
        st.rerun()

    # 状态2: 正在搜索 Tier 2
    elif st.session_state.search_status == 'SEARCHING_TIER_2':
        debug_log = st.session_state.debug_log
        processed_query = st.session_state.processed_query
        
        debug_log.append("\n---\n**层级 2: 前缀匹配**\n---")
        lookup_result = jmd.lookup(f"{processed_query}%")
        for entry in lookup_result.entries:
            if entry.idseq not in st.session_state.found_ids:
                st.session_state.tier2_entries.append(entry)
                st.session_state.found_ids.add(entry.idseq)
        debug_log.append(f"找到 {len(st.session_state.tier2_entries)} 个新结果。")

        if not st.session_state.found_ids:
            st.session_state.search_status = 'SEARCHING_TIER_3'
        else:
            st.session_state.search_status = 'DONE'
            debug_log.append("\n---\n**所有搜索已完成**\n---")
        st.rerun()

    # 状态3: 正在搜索 Tier 3
    elif st.session_state.search_status == 'SEARCHING_TIER_3':
        debug_log = st.session_state.debug_log
        processed_query = st.session_state.processed_query
        
        debug_log.append("\n---\n**层级 3: 容错匹配**\n---")
        tolerant_queries = set()
        for variant in special_tolerant_convert(processed_query): tolerant_queries.add(variant)
        if len(processed_query) > 2: tolerant_queries.add(processed_query[:-1])
        kanji_only_str = only_kanji(processed_query)
        if kanji_only_str and kanji_only_str != processed_query: tolerant_queries.add(kanji_only_str)
        debug_log.append(f"生成容错搜索词: `{list(tolerant_queries)}`")
        
        for t_query in tolerant_queries:
            if not t_query: continue
            lookup_result = jmd.lookup(f"{t_query}%")
            for entry in lookup_result.entries:
                if entry.idseq not in st.session_state.found_ids:
                    st.session_state.tier3_entries.append(entry)
                    st.session_state.found_ids.add(entry.idseq)
        debug_log.append(f"找到 {len(st.session_state.tier3_entries)} 个新结果。")

        st.session_state.search_status = 'DONE'
        debug_log.append("\n---\n**所有搜索已完成**\n---")
        st.rerun()
except Exception as e:
    # 发生任何意外时，将状态重置，避免卡在搜索中
    st.session_state.search_status = 'DONE'
    st.error(f"搜索过程中发生错误: {e}")