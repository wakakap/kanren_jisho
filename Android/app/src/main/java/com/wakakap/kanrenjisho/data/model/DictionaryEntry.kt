//package com.wakakap.kanrenjisho.data.model
//
//// 定义一个词条的数据结构，使其在整个应用中保持一致
//data class DictionaryEntry(
//    val id: Long,               // 数据库中的唯一ID
//    val kanji: String?,         // 汉字表示 (可能为空，如只有假名的词)
//    val reading: String,        // 假名读音
//    val gloss: String           // 词义解释
//)

package com.wakakap.kanrenjisho.data.model

/**
 * 代表一个完整的词条，对应数据库中的一个'entry'。
 * 这个结构能够完整地反映一个词条的所有信息，包括多种写法、读音和详细的词义。
 *
 * @property idseq 词条的唯一ID，对应 'entries' 表中的 'idseq'。
 * @property kanjiForms 词条所有可能的汉字写法列表。来自 'forms' 表 (type='kanji')。
 * @property readingForms 词条所有可能的假名读音列表。来自 'forms' 表 (type='reading')。
 * @property senses 词条的词义列表，每个 'Sense' 对象代表一个独立的含义。
 */
data class DictionaryEntry(
    val idseq: Long,
    val kanjiForms: List<String>,
    val readingForms: List<String>,
    val senses: List<Sense>,
    val priority: Int,
    val rankingScore: Int = 0,
)

/**
 * 代表词条的一个独立词义，对应 'senses' 表中的一条记录。
 *
 * @property partOfSpeech 词性 (e.g., "Noun", "v1", "adj-i")。对应 'pos' 字段。
 * @property gloss 该词义下的英文解释。对应 'gloss' 字段。
 * @property info 补充说明信息 (e.g., "usually written using kana alone")。对应 'info' 字段。
 * @property examples 与该词义相关的例句列表。
 */
data class Sense(
    val partOfSpeech: String,
    val gloss: String,
    val info: String?,
    val examples: List<Example>
)

/**
 * 代表一条日英双语例句，对应 'examples' 表中的一条记录。
 *
 * @property japanese 日文例句。对应 'jpn_sentence' 字段。
 * @property english 对应的英文翻译。对应 'eng_sentence' 字段。
 */
data class Example(
    val japanese: String,
    val english: String
)