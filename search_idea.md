搜索输入为：s

转换函数
- convert_to_japanese_char(x)
- only_kanji(x) 去掉x中的所有非汉字字符，返回结果
- cut_tolerant_convert(x) 返回x去掉最后一个字符（不为空）
- special_tolerant_convert(x) 针对日文长音促音的优化，返回x的另外几种可能的列表

搜索函数：
- perfect_search(x) 完全匹配x，返回结果
- startwith_search(x) 以字符x开头的搜索，返回结果
- include_search(x) 含有字符x开头的搜索，返回结果


排序函数：
- 比s多出的字符数量少的优先
- 常用等级排序
- 动词优先（最后一个字符是る）

核心逻辑：
- 如果输入有英文，使用默认搜索
- 如果输入不包含英文，执行以下逻辑
  - 如果输入没有平假名或片假名：用convert_to_japanese_char(x) 进行perfect_search startwith_search两种搜索，排序后返回列表。
  - 如果输入有汉字也有假名：用convert_to_japanese_char(x) 进行perfect_search，如果perfect_search为空则用only_kanji(x)进行startwith_search搜索返回列表。
  - 如果输入仅有假名：先perfect_search，如果为空，则用 cut_tolerant_convert(x)进行startwith_search ,如果还是为空，则再进行cut_tolerant_convert后再搜索，直到结果不为空停下，返回那个列表。

------------

综合以上分析，我为您梳理一个更完善的逻辑流程：

1.  **输入预处理 (Input Pre-processing)**:
    * 接收用户输入 `s`。
    * 将 `s` 中的中文汉字通过 `convert_to_japanese_char` 转换为日文汉字。
    * **（建议新增）** 检测 `s` 是否为罗马音。如果是，则将其转换为假名。

2.  **分层搜索 (Tiered Searching)**:
    * **第一层 (Tier 1): 精确匹配**
        * 对处理后的 `s` 进行完美匹配 (`perfect_search`)。
    * **第二层 (Tier 2): 前缀匹配**
        * 对处理后的 `s` 进行前缀匹配 (`startwith_search`)。
    * **第三层 (Tier 3): 容错匹配**
        * 如果 `s` 是假名或含假名，使用 `special_tolerant_convert` 生成变体列表，对每个变体进行前缀/完美匹配。
        * 如果结果仍然很少或没有，使用 `cut_tolerant_convert` 进行砍尾前缀匹配。
        * 如果 `s` 是汉字假名混合，使用 `only_kanji` 提取汉字进行前缀匹配。
    * **关键**: 将所有层级搜索到的结果**合并**到一个大列表中，并为每个结果**标记它来自哪个层级**（Tier 1, 2, or 3）。

3.  **多维排序 (Multi-factor Sorting)**:
    * 现在对合并后的大列表 `results` 进行排序，排序规则依次为：
        1.  **按搜索层级排序**: Tier 1 的结果永远在最前面，其次是 Tier 2，最后是 Tier 3。
        2.  **按常用度排序**: 在同一层级内，根据您设定的常用度分数，从高到低排序。
        3.  **按长度相关性排序**: 在常用度分数相同的情况下，`len(result) - len(query)` 差值越小越靠前。
        4.  **按词性排序**: 在以上都相同的情况下，按 “动词 -> 形容词 -> 其他” 的顺序排序。

----------------------