import json
import os

# 1. 替换为你实际解压出来的文件名
SOURCE_FILE = 'jmdict-eng-common-3.6.2.json' 
OUTPUT_DIR = './public_dict_data'
CHUNKS_DIR = f'{OUTPUT_DIR}/chunks'
CHUNK_SIZE = 1000  # 每 1000 个词条打包成一个 chunk

def main():
    # 创建输出目录
    os.makedirs(CHUNKS_DIR, exist_ok=True)

    print(f'正在读取原始 JSON 文件 ({SOURCE_FILE})，请稍候...')
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            dict_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {SOURCE_FILE}，请确认文件名是否正确并放在同级目录。")
        return

    words = dict_data.get('words', [])
    total_words = len(words)
    print(f'成功读取！共包含 {total_words} 个词条。正在生成索引和分块文件...')

    search_index = []

    # 按照 CHUNK_SIZE 对词条进行步长切片
    for i in range(0, total_words, CHUNK_SIZE):
        chunk_index = i // CHUNK_SIZE
        chunk_file_name = f'chunk_{chunk_index}.json'
        
        chunk_data = words[i:i + CHUNK_SIZE]
        
        # 将列表转换为字典，以 id 为键，方便前端通过 id 直接读取 O(1)
        chunk_map = {}
        
        for word in chunk_data:
            word_id = word['id']
            
            # 提取所有汉字和假名的文本
            kanji_list = [k['text'] for k in word.get('kanji', [])]
            kana_list = [k['text'] for k in word.get('kana', [])]
            
            # 存入前台极速匹配所需的瘦身版索引
            search_index.append({
                'id': word_id,
                'kanji': kanji_list,
                'kana': kana_list,
                'chunk': chunk_file_name
            })
            
            # 将完整的词条信息存入对应的 chunk 映射中
            chunk_map[word_id] = word
            
        # 写入单独的分块文件 (使用 separators 去除多余空格以极限压缩体积)
        chunk_path = os.path.join(CHUNKS_DIR, chunk_file_name)
        with open(chunk_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_map, f, ensure_ascii=False, separators=(',', ':'))

    # 写入全局搜索索引文件
    index_path = os.path.join(OUTPUT_DIR, 'search_index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False, separators=(',', ':'))

    total_chunks = (total_words + CHUNK_SIZE - 1) // CHUNK_SIZE
    print(f'✅ 处理完成！')
    print(f'- 生成了全局索引: search_index.json')
    print(f'- 生成了详细数据分块: 共 {total_chunks} 个文件保存在 {CHUNKS_DIR}/ 目录下')

if __name__ == '__main__':
    main()