## 数据库文件结构 (Markdown)

这是一个基于`JMdict_detailed.db`的结构描述。

* **`entries` 表 (词条主表)**
    * `idseq`: INTEGER (例: `1234560`) - 词条的唯一主键ID。
    * `main_kanji`: TEXT (例: `食べる`) - 词条的主要汉字形式。
    * `main_reading`: TEXT, NOT NULL (例: `たべる`) - 词条的主要读音。

* **`forms` 表 (词形表)**
    * `id`: INTEGER (例: `101`) - 该词形记录的唯一ID。
    * `entry_idseq`: INTEGER, NOT NULL (例: `1234560`) - 关联到`entries`表的`idseq`，表示这是哪个词条的词形。
    * `text`: TEXT, NOT NULL (例: `食べる`) - 具体的文本形式。
    * `type`: TEXT, NOT NULL (例: `kanji`) - 词形类型，如`kanji` (汉字) 或 `reading` (读音)。
    * `priorities`: TEXT (例: `ichi1,news1`) - 常用度标签，用于计算优先级。

* **`senses` 表 (释义表)**
    * `id`: INTEGER (例: `771`) - 该释义的唯一ID。
    * `entry_idseq`: INTEGER, NOT NULL (例: `1234560`) - 关联到`entries`表的`idseq`，表示这是哪个词条的释义。
    * `pos`: TEXT (例: `Ichidan verb,transitive verb`) - 词性 (Part of Speech)。
    * `gloss`: TEXT, NOT NULL (例: `to eat`) - 英文释义。
    * `info`: TEXT (例: `(Usually written using kana alone)`) - 补充说明信息。

* **`examples` 表 (例句表)**
    * `id`: INTEGER (例: `9001`) - 该例句的唯一ID。
    * `sense_id`: INTEGER, NOT NULL (例: `771`) - 关联到`senses`表的`id`，表示这是哪个释义的例句。
    * `jpn_sentence`: TEXT (例: `もっと果物を食べるべきです。`) - 日文例句。
    * `eng_sentence`: TEXT (例: `You should eat more fruit.`) - 英文例句。

---

### 各部分如何互相调用总结

上面这个结构是一个典型的**关系型数据库**设计，它的核心思想是通过ID（键）将分散在不同表中的数据关联起来，避免数据冗余，使结构更清晰。

调用流程可以这样理解：

1.  **起点 (`forms` 表)**: 当用户搜索一个词，比如“食べる”时，程序首先在 `forms` 表的 `text` 列中查找。找到后，它会获得一个非常关键的ID：`entry_idseq` (在我们的例子中是 `1234560`)。这个ID就像一把“万能钥匙”，可以用来解锁所有与“食べる”这个词条相关的信息。

2.  **关联到词条本身 (`entries` 表)**: 这把“万能钥匙” (`entry_idseq`) 对应着 `entries` 表中的主键 `idseq`。`entries` 表可以看作是这个词条的“户口本”，定义了最核心的信息。

3.  **获取所有释义 (`senses` 表)**: 程序使用这把钥匙 (`entry_idseq` = `1234560`) 去 `senses` 表中查找所有匹配的行。因为一个词可以有多个意思，所以可能会找到多条记录（比如「食べる」就有两个意思）。这是一个**一对多**的关系。程序会记下每条释义的唯一ID `id` (例: `771` 和 `772`)。

4.  **为每个释义匹配例句 (`examples` 表)**: 接着，对于上一步中找到的**每一条释义**，程序会用该释义的ID (`id`) 去 `examples` 表中进行匹配。它会查找 `examples` 表中 `sense_id` 列与该释义ID相等的所有行。这样，每个意思就能准确地和它自己的例句关联起来。这也是一个**一对多**的关系（一个意思可以有多个例句）。

**总结来说**，整个调用过程是一个**链式查询**：通过 `forms` 找到词条的“万能钥匙” `entry_idseq`，然后用这把钥匙去 `senses` 表打开所有“释义”的门，再用每个“释义”自己的钥匙 `id` 去 `examples` 表打开所有“例句”的门。最后，程序将从各个表中获取到的碎片化信息在内存中组装成一个完整的、包含所有信息的词条对象，最终呈现给用户。