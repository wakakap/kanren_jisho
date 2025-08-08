package com.wakakap.kanrenjisho.data.database

import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import com.readystatesoftware.sqliteasset.SQLiteAssetHelper
import com.wakakap.kanrenjisho.data.model.DictionaryEntry

class DictionaryDbHelper(context: Context) : SQLiteAssetHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        // 【修改】: 更新数据库文件名
        private const val DATABASE_NAME = "JMdict_new.db"
        private const val DATABASE_VERSION = 1

        // 【修改】: 使用新的表和列名常量
        private const val TABLE_ENTRIES = "entries"
        private const val COL_ID = "id"
        private const val COL_IS_COMMON = "is_common"
        private const val COL_MAIN_KANJI = "main_kanji"
        private const val COL_MAIN_KANA = "main_kana"
        private const val COL_ALL_KANJI_FORMS = "all_kanji_forms"
        private const val COL_ALL_KANA_FORMS = "all_kana_forms"
        private const val COL_ALL_SENSES = "all_senses"
    }

    fun search(query: String, searchType: SearchType): List<DictionaryEntry> {
        val db: SQLiteDatabase = readableDatabase
        val entries = mutableListOf<DictionaryEntry>()

        // 新的查询逻辑更简单，直接在主表上进行
        val selection = "$COL_MAIN_KANJI LIKE ? OR $COL_MAIN_KANA LIKE ?"
        val selectionArg = when (searchType) {
            SearchType.EXACT -> query
            SearchType.PREFIX -> "$query%"
        }
        val selectionArgs = arrayOf(selectionArg, selectionArg)

        // 查询所有需要的列
        val cursor = db.query(TABLE_ENTRIES, null, selection, selectionArgs, null, null, "$COL_IS_COMMON DESC", "50")

        cursor.use {
            while (it.moveToNext()) {
                entries.add(buildEntryFromCursor(it))
            }
        }
        return entries
    }

    fun getEntriesByIds(ids: List<Long>): List<DictionaryEntry> {
        if (ids.isEmpty()) return emptyList()

        val db: SQLiteDatabase = readableDatabase
        val entries = mutableListOf<DictionaryEntry>()

        val placeholders = ids.joinToString(",") { "?" }
        val selection = "$COL_ID IN ($placeholders)"
        val selectionArgs = ids.map { it.toString() }.toTypedArray()

        val cursor = db.query(TABLE_ENTRIES, null, selection, selectionArgs, null, null, null)

        cursor.use {
            while (it.moveToNext()) {
                entries.add(buildEntryFromCursor(it))
            }
        }

        return entries.sortedBy { ids.indexOf(it.idseq) }
    }

    /**
     * 新的核心辅助函数，从数据库游标构建一个完整的 DictionaryEntry 对象
     */
    private fun buildEntryFromCursor(cursor: Cursor): DictionaryEntry {
        // 从游标中获取原始数据
        val id = cursor.getLong(cursor.getColumnIndexOrThrow(COL_ID))
        val isCommon = cursor.getInt(cursor.getColumnIndexOrThrow(COL_IS_COMMON))
        val allKanjiFormsJson = cursor.getString(cursor.getColumnIndexOrThrow(COL_ALL_KANJI_FORMS))
        val allKanaFormsJson = cursor.getString(cursor.getColumnIndexOrThrow(COL_ALL_KANA_FORMS))
        val allSensesJson = cursor.getString(cursor.getColumnIndexOrThrow(COL_ALL_SENSES))

        // 调用我们的映射函数来完成复杂的转换工作
        return mapRowToDictionaryEntry(
            id, isCommon, allKanjiFormsJson, allKanaFormsJson, allSensesJson
        )
    }

    enum class SearchType {
        EXACT, PREFIX
    }
}