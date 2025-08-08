package com.wakakap.kanrenjisho.data.database

import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import com.google.gson.reflect.TypeToken
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.model.Example
import com.wakakap.kanrenjisho.data.model.Sense

// --- 这些数据类现在精确匹配 jmdict-simplified 的JSON结构 ---

data class JsonKanji(val text: String?, val common: Boolean?)
data class JsonKana(val text: String?, val common: Boolean?)
data class JsonGloss(val lang: String?, val text: String?)

/**
 * 【新增】: 对应最内层的例句对象: {"land":"jpn", "text":"..."}
 * 使用 @SerializedName 来兼容 "land" 和 "lang" 两种可能的键名
 */
data class JsonSentence(
    @SerializedName("land", alternate = ["lang"]) val lang: String?,
    val text: String?
)

/**
 * 【新增】: 对应外层的“例句组”对象
 */
data class JsonExampleGroup(
    val sentences: List<JsonSentence>?
)

data class JsonSense(
    val partOfSpeech: List<String>?,
    val gloss: List<JsonGloss>?,
    val info: List<String>?,
    // 【修改】: sense中的examples现在是“例句组”的列表
    val examples: List<JsonExampleGroup>?
)

// --- 数据映射核心函数 ---

private val gson = Gson()

fun mapRowToDictionaryEntry(
    id: Long,
    isCommon: Int,
    allKanjiFormsJson: String,
    allKanaFormsJson: String,
    allSensesJson: String
): DictionaryEntry {
    val kanjiListType = object : TypeToken<List<JsonKanji>>() {}.type
    val kanaListType = object : TypeToken<List<JsonKana>>() {}.type
    val senseListType = object : TypeToken<List<JsonSense>>() {}.type

    val jsonKanjiList: List<JsonKanji> = gson.fromJson(allKanjiFormsJson, kanjiListType)
    val jsonKanaList: List<JsonKana> = gson.fromJson(allKanaFormsJson, kanaListType)
    val jsonSenseList: List<JsonSense> = gson.fromJson(allSensesJson, senseListType)

    val kanjiForms = jsonKanjiList.mapNotNull { it.text }
    val readingForms = jsonKanaList.mapNotNull { it.text }
    val senses = jsonSenseList.map { jsonSense ->

        // 【核心修改】: 全新的例句转换逻辑，用于处理嵌套结构
        val mappedExamples = jsonSense.examples?.flatMap { exampleGroup ->
            // 从一个例句组的 "sentences" 列表中，找出对应的日英句子
            val jpnSentence = exampleGroup.sentences?.find { it.lang == "jpn" }?.text
            val engSentence = exampleGroup.sentences?.find { it.lang == "eng" }?.text

            // 只有在日英句子都存在时，才创建一个有效的 Example 对象
            if (jpnSentence != null && engSentence != null) {
                listOf(Example(japanese = jpnSentence, english = engSentence))
            } else {
                emptyList()
            }
        } ?: emptyList()

        Sense(
            partOfSpeech = jsonSense.partOfSpeech?.filterNotNull()?.joinToString(", ") ?: "unk",
            gloss = jsonSense.gloss?.firstOrNull { it.lang == "eng" }?.text ?: "",
            info = jsonSense.info?.filterNotNull()?.joinToString(", "),
            examples = mappedExamples // 使用我们从复杂结构中提取出的干净例句列表
        )
    }

    val priority = if (isCommon == 1) 100 else 0

    return DictionaryEntry(
        idseq = id,
        kanjiForms = kanjiForms,
        readingForms = readingForms,
        senses = senses,
        priority = priority,
        rankingScore = 0
    )
}