package com.wakakap.kanrenjisho.data.database

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import com.readystatesoftware.sqliteasset.SQLiteAssetHelper
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.model.Example
import com.wakakap.kanrenjisho.data.model.Sense

class DictionaryDbHelper(context: Context) : SQLiteAssetHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        private const val DATABASE_NAME = "JMdict_detailed.db"
        private const val DATABASE_VERSION = 1

        // --- 表名常量 ---
        private const val TABLE_ENTRIES = "entries"
        private const val TABLE_FORMS = "forms"
        private const val TABLE_SENSES = "senses"
        private const val TABLE_EXAMPLES = "examples"

        // --- 列名常量 ---
        // 'entries' table
        private const val COL_IDSEQ = "idseq" // 【新增】'entries' 表的主键

        // 'forms' table
        private const val COL_ENTRY_IDSEQ = "entry_idseq" // 'forms' 和 'senses' 表的外键
        private const val COL_TEXT = "text"
        private const val COL_TYPE = "type"
        private const val COL_PRIORITIES = "priorities" // 【新增】'forms' 表的常用度标签列

        // 'senses' table
        private const val COL_SENSE_PK = "id"
        private const val COL_POS = "pos"
        private const val COL_GLOSS = "gloss"
        private const val COL_INFO = "info"

        // 'examples' table
        private const val COL_SENSE_ID = "sense_id"
        private const val COL_JPN_SENTENCE = "jpn_sentence"
        private const val COL_ENG_SENTENCE = "eng_sentence"


        // 常用度标签计分表
        private val priorityMap = mapOf(
            // 核心高频词
            "ichi1" to 150, "news1" to 140, "spec1" to 130, "gai1" to 120,
            "ichi2" to 115, "news2" to 110, "spec2" to 105, "gai2" to 100,

            // JLPT 等级 (对学习者非常重要)
            "jlpt-n5" to 90,
            "jlpt-n4" to 80,
            "jlpt-n3" to 70,
            "jlpt-n2" to 60,
            "jlpt-n1" to 50
        )
    }

    fun search(query: String, searchType: SearchType): List<DictionaryEntry> {
        val db: SQLiteDatabase = readableDatabase
        val entryIds = findEntryIds(db, query, searchType)
        return entryIds.mapNotNull { buildEntryFromIdseq(db, it) }
    }

    fun getEntriesByIds(ids: List<Long>): List<DictionaryEntry> {
        if (ids.isEmpty()) return emptyList()
        val db: SQLiteDatabase = readableDatabase
        // 直接使用id列表构建entry对象，不再需要额外查询
        val entries = ids.mapNotNull { buildEntryFromIdseq(db, it) }
        // 保持传入ID的顺序
        return entries.sortedBy { ids.indexOf(it.idseq) }
    }

    private fun buildEntryFromIdseq(db: SQLiteDatabase, idseq: Long): DictionaryEntry? {
        val (kanjiForms, readingForms, maxPriority) = getFormsAndPriorityForEntry(db, idseq)
        val senses = getSensesForEntry(db, idseq)

        if (kanjiForms.isEmpty() && readingForms.isEmpty()) return null

        return DictionaryEntry(
            idseq = idseq,
            kanjiForms = kanjiForms,
            readingForms = readingForms,
            senses = senses,
            priority = maxPriority
        )
    }

    private fun findEntryIds(db: SQLiteDatabase, query: String, searchType: SearchType): List<Long> {
        val ids = mutableListOf<Long>()
        val selectionArg = when (searchType) {
            SearchType.EXACT -> query
            SearchType.PREFIX -> "$query%"
        }

        // 查询语句现在完全使用常量
        val sql = "SELECT DISTINCT $COL_ENTRY_IDSEQ FROM $TABLE_FORMS WHERE $COL_TEXT LIKE ? LIMIT 50"
        db.rawQuery(sql, arrayOf(selectionArg)).use { cursor ->
            while (cursor.moveToNext()) {
                ids.add(cursor.getLong(cursor.getColumnIndexOrThrow(COL_ENTRY_IDSEQ)))
            }
        }
        return ids
    }

    private fun getFormsAndPriorityForEntry(db: SQLiteDatabase, idseq: Long): Triple<List<String>, List<String>, Int> {
        val kanjiForms = mutableListOf<String>()
        val readingForms = mutableListOf<String>()
        var maxPriority = 0

        val sql = "SELECT $COL_TEXT, $COL_TYPE, $COL_PRIORITIES FROM $TABLE_FORMS WHERE $COL_ENTRY_IDSEQ = ?"
        db.rawQuery(sql, arrayOf(idseq.toString())).use { cursor ->
            while (cursor.moveToNext()) {
                val text = cursor.getString(cursor.getColumnIndexOrThrow(COL_TEXT))
                when (cursor.getString(cursor.getColumnIndexOrThrow(COL_TYPE))) {
                    "kanji" -> kanjiForms.add(text)
                    "reading" -> readingForms.add(text)
                }

                val prioritiesStr = cursor.getString(cursor.getColumnIndexOrThrow(COL_PRIORITIES))
                if (!prioritiesStr.isNullOrEmpty()) {
                    val priorities = prioritiesStr.split(',')
                    for (p in priorities) {
                        val currentScore = priorityMap[p] ?: 0
                        if (currentScore > maxPriority) {
                            maxPriority = currentScore
                        }
                    }
                }
            }
        }
        return Triple(kanjiForms, readingForms, maxPriority)
    }

    private fun getSensesForEntry(db: SQLiteDatabase, idseq: Long): List<Sense> {
        val senses = mutableListOf<Sense>()
        val sql = "SELECT $COL_SENSE_PK, $COL_POS, $COL_GLOSS, $COL_INFO FROM $TABLE_SENSES WHERE $COL_ENTRY_IDSEQ = ?"
        db.rawQuery(sql, arrayOf(idseq.toString())).use { cursor ->
            while (cursor.moveToNext()) {
                val senseId = cursor.getLong(cursor.getColumnIndexOrThrow(COL_SENSE_PK))
                senses.add(
                    Sense(
                        partOfSpeech = cursor.getString(cursor.getColumnIndexOrThrow(COL_POS)),
                        gloss = cursor.getString(cursor.getColumnIndexOrThrow(COL_GLOSS)),
                        info = cursor.getString(cursor.getColumnIndexOrThrow(COL_INFO)),
                        examples = getExamplesForSense(db, senseId)
                    )
                )
            }
        }
        return senses
    }

    private fun getExamplesForSense(db: SQLiteDatabase, senseId: Long): List<Example> {
        val examples = mutableListOf<Example>()
        val sql = "SELECT $COL_JPN_SENTENCE, $COL_ENG_SENTENCE FROM $TABLE_EXAMPLES WHERE $COL_SENSE_ID = ?"
        db.rawQuery(sql, arrayOf(senseId.toString())).use { cursor ->
            while (cursor.moveToNext()) {
                examples.add(
                    Example(
                        japanese = cursor.getString(cursor.getColumnIndexOrThrow(COL_JPN_SENTENCE)),
                        english = cursor.getString(cursor.getColumnIndexOrThrow(COL_ENG_SENTENCE))
                    )
                )
            }
        }
        return examples
    }

    enum class SearchType {
        EXACT, PREFIX
    }
}