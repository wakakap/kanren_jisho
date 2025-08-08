package com.wakakap.kanrenjisho.data.database

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.model.Favorite

// 标准的 SQLiteOpenHelper，用于管理用户收藏
class FavoritesDbHelper(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        private const val DATABASE_NAME = "favorites.db"
        // 提示: 如果你想确保旧数据被清除，可以增加 DATABASE_VERSION
        private const val DATABASE_VERSION = 2
        private const val TABLE_NAME = "favorites"

        // 【核心修改】: 表结构完全改变，只存储一个指向主词典的ID
        private const val COL_ID = "id" // 主键
        private const val COL_ENTRY_IDSEQ = "entry_idseq" // 收藏的词条ID
    }

    override fun onCreate(db: SQLiteDatabase) {
        // 【核心修改】: 创建一个新的、更简单的表
        // 只包含一个自增主键和一个用于存储词条ID的列
        // entry_idseq 列是唯一的，防止重复收藏同一个词条
        val createTable = "CREATE TABLE $TABLE_NAME (" +
                "$COL_ID INTEGER PRIMARY KEY AUTOINCREMENT," +
                "$COL_ENTRY_IDSEQ INTEGER NOT NULL UNIQUE)"
        db.execSQL(createTable)
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // 简单的升级策略：删除旧表，创建新表。用户的旧收藏会丢失。
        db.execSQL("DROP TABLE IF EXISTS $TABLE_NAME")
        onCreate(db)
    }

    /**
     * 【核心修改】: 添加收藏的逻辑
     * 从 DictionaryEntry 对象中提取唯一的 idseq 并存入数据库。
     */
    fun addFavorite(entry: DictionaryEntry): Boolean {
        val db = writableDatabase
        val values = ContentValues().apply {
            put(COL_ENTRY_IDSEQ, entry.idseq)
        }
        val result = db.insert(TABLE_NAME, null, values)
        return result != -1L
    }

    /**
     * 【核心修改】: 删除收藏的逻辑
     * 根据传入的 idseq 精确删除。
     */
    fun removeFavorite(idseq: Long) {
        val db = writableDatabase
        db.delete(TABLE_NAME, "$COL_ENTRY_IDSEQ = ?", arrayOf(idseq.toString()))
    }

    /**
     * 【核心修改】: 获取所有收藏记录的逻辑
     * 从数据库中读取所有收藏的 idseq，并包装成 Favorite 对象列表返回。
     */
    fun getAllFavorites(): List<Favorite> {
        val favorites = mutableListOf<Favorite>()
        val db = readableDatabase
        // 按收藏顺序倒序排列（新收藏的在前）
        val cursor = db.query(TABLE_NAME, null, null, null, null, null, "$COL_ID DESC")

        cursor.use {
            while (it.moveToNext()) {
                favorites.add(
                    Favorite(
                        entry_idseq = it.getLong(it.getColumnIndexOrThrow(COL_ENTRY_IDSEQ))
                    )
                )
            }
        }
        return favorites
    }
}