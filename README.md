# Kanrenjisho Web (関連辞書 网页测试版)

这是一个纯前端、纯静态的日语词典 Web 测试项目，用于在浏览器环境下测试和验证渐进式多级搜索、容错算法以及词条打分排序逻辑。

可运行页面：https://wareomou.vercel.app/kanrenjisho.html

**以下说明来自于AI对代码的总结，可能有微小错误的存在。**

## 📚 数据来源与依赖声明
本项目的核心数据与转换功能离不开以下优秀的开源项目：
* **词典数据来源**: [JMdict-simplified](https://github.com/scriptin/jmdict-simplified) (基于 JMdict 提取的 JSON 简化版数据)。
* **假名转换支持**: [WanaKana](https://github.com/WaniKani/WanaKana) (用于实现罗马音到平假名的极速转换)。
* **汉字繁简转换**: [OpenCC-js](https://github.com/BYVoid/OpenCC) (用于实现大陆简体中文到日文新字体汉字的自动映射)。

## 📦 数据切片与性能优化 (Data Chunking)
由于原始的 JMdict JSON 文件体积巨大，如果直接在静态网页中利用 `fetch` 一次性加载，会导致浏览器内存暴涨、页面严重卡顿，同时也容易触发 GitHub Pages 的单文件大小限制。

为了在纯静态环境下实现**毫秒级秒开**，本项目在部署前采用了**数据预切片处理 (Data Slicing)** 策略：

1. **执行切片脚本**: 开发者需在本地运行内置的 Python 脚本 (`conversion script/slice_dict.py`)，读取庞大的源 JSON。
2. **生成轻量级索引 (`search_index.json`)**: 脚本会提取所有词条的 ID、汉字和假名，生成一个仅有几兆大小的精简索引。网页在初始化时只需加载该索引，即可在内存中实现极速的正则匹配与前缀检索。
3. **分块按需加载 (`chunks/` 目录)**: 词条的详细释义、词性、例句等沉重数据，被以 1000 词为单位打包成数百个小型的 `chunk_xxx.json` 文件。只有当系统通过索引锁定目标词条后，才会**按需动态拉取 (Lazy Load)** 对应的分块文件进行详细信息的渲染。

## ⚙️ 核心搜索架构 (Tier-System)
为了在无后端的情况下实现极速且精准的搜索，本项目采用了 **“精简索引加载 + 详情分块按需拉取”** 的策略，并执行严格的**三级渐进式搜索 (Tiered Search)**：

1. **Tier 1 (完全匹配)**：优先查找汉字或假名与输入词完全一致的词条。
2. **Suggestions (建议匹配)**：针对日语输入特性的促音容错检索。
3. **Tier 2 (前缀匹配)**：查找以输入词开头的词条。
4. **Tier 3 (容错提取/Fallback)**：仅在 Tier 1 和 Tier 2 均无结果时触发，对输入词进行降级处理（如提取纯汉字或去除尾缀）后再次进行前缀搜索。

> 💡 **动态打分机制 (Ranking Score)**：所有检索到的词条会根据**词性 (动词/形容词优先)**、**匹配度 (完全/前缀)**、**常用度 (Common 标记)** 以及 **假名长度** 进行综合加权打分，并按分数降序排列，确保最符合用户预期的词条排在最前面。

## ✨ 特色算法与场景演示

本项目包含了针对日语学习者高度定制的辅助算法，以下是几个特色场景的演示：

### 1. 罗马音无缝直搜
* **逻辑**: 自动拦截英文字母输入，在搜索前将其转化为平假名。
* **演示**: 输入 `taberu` ➡️ 系统自动转为 `たべる` ➡️ 命中【食べる】。

### 2. 中文简体自动映射日文汉字
* **逻辑**: 许多日语词典不支持直接搜中文简体字。本算法引入 OpenCC，在搜索前自动将大陆简体转换为日文标准汉字。
* **演示**: 输入 `动词` ➡️ 系统自动转为 `動詞` ➡️ 瞬间命中对应词条。

### 3. 促音 (っ) 智能容错
* **逻辑**: 针对初学者容易漏打、多打促音的情况，算法会自动遍历字符串，在特定的假名前面生成带有促音的“变体搜索词”进行兜底检索。
* **演示**: 输入 `がこう` (漏打促音) ➡️ 系统自动生成变体 `がっこう` ➡️ 成功命中【学校】。

### 4. 脏数据清洗与纯汉字回退检索
* **逻辑**: 当用户粘贴了一段包含多余数字或乱码的文本时（且前两级搜索未命中），系统会利用正则 `[\u4e00-\u9faf]` 提取其中的纯汉字，作为终极容错手段重新检索。
* **演示**: 输入 `食べる123` ➡️ 未命中 ➡️ 触发 Tier 3 容错，提取出纯汉字 `食` ➡️ 以前缀匹配命中【食べる】、【食事】等词。

----

# Kanrenjisho Android (関連辞書 安卓)

本项目采用 **MVVM 架构** 与 **Jetpack Compose** 声明式 UI，结合本地 SQLite 数据库，实现了毫秒级的离线日语查词体验。

## 📚 数据来源与开源组件
* **数据驱动**: 基于 [JMdict-simplified](https://github.com/scriptin/jmdict-simplified) 项目编译而成的本地 SQLite 数据库 (`JMdict_new.db`)。
  - 利用 `conversion script\json_convert_to_db.py` 把下载的 `jmdict-examples-eng-3.6.1.json` 转换为 `JMdict_new.db`。
* **语言处理组件**:
  * [WanaKana (Java)](https://github.com/esnaultdev/wanakana-java) - 罗马音/假名互转。
  * [OpenCC4j](https://github.com/houbb/opencc4j) - 简繁体与日文汉字转换。

## 🏗 项目结构图解

本项目的代码结构遵循严格的职责分离原则：

```text
app/src/main/
├── assets/databases/       # 静态资源
│   └── JMdict_new.db       # 预打包的核心词典只读数据库
├── java/com/wakakap/kanrenjisho/
│   ├── composables/        # 【UI层】Jetpack Compose 界面组件
│   │   ├── EntryItem.kt    # 单个词条的卡片 UI 渲染
│   │   ├── FavoritesSheet.kt # 收藏夹底部弹出面板 UI
│   │   └── SearchScreen.kt # 核心搜索页面的 UI 布局
│   ├── data/               # 【数据层】负责数据的获取与持久化
│   │   ├── database/       
│   │   │   ├── DictionaryDbHelper.kt # 主词典 DB 操作 (查询构建、Cursor 解析)
│   │   │   ├── FavoritesDbHelper.kt  # 用户收藏夹 DB 操作 (增删查)
│   │   │   └── JsonMapping.kt        # 负责将 DB 中存储的 JMdict JSON 字符串反序列化为 Kotlin 对象
│   │   ├── model/          # 数据实体类 (DictionaryEntry, Sense, Example, Favorite)
│   │   └── repository/     
│   │       └── DictionaryRepository.kt # 数据仓库，封装底层 DB 操作，向 ViewModel 提供统一接口并调度协程 (Dispatchers.IO)
│   ├── ui/theme/           # 【主题层】Compose 的颜色、字体与全局主题配置
│   ├── util/               # 【工具层】纯函数算法与业务处理
│   │   ├── ConversionUtils.kt # 处理罗马音转换、中文转日文汉字
│   │   └── SearchUtils.kt     # 处理提取纯汉字、促音容错生成算法
│   ├── viewmodel/          # 【表现层】逻辑控制枢纽
│   │   └── DictionaryViewModel.kt # 管理 UI 状态 (StateFlow)、执行多级搜索调度、计算打分排序
│   └── MainActivity.kt     # Android 应用程序入口，承载 Compose 内容
```

## 待解决问题

- 容错和联想的促音只能处理缺少一个促音的情况。