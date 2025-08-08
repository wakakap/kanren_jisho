package com.wakakap.kanrenjisho.data.repository

import android.content.Context
import com.wakakap.kanrenjisho.data.database.DictionaryDbHelper
import com.wakakap.kanrenjisho.data.database.FavoritesDbHelper
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.model.Favorite
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

// 数据仓库，为ViewModel提供统一的数据接口，屏蔽底层数据源（数据库）
class DictionaryRepository(context: Context) {

    private val dictionaryDbHelper = DictionaryDbHelper(context)
    private val favoritesDbHelper = FavoritesDbHelper(context)

    // 在IO线程上执行数据库查询。此函数无需更改，它现在会自动返回新结构的词条列表。
    suspend fun searchExact(query: String): List<DictionaryEntry> = withContext(Dispatchers.IO) {
        dictionaryDbHelper.search(query, DictionaryDbHelper.SearchType.EXACT)
    }

    // 此函数也无需更改。
    suspend fun searchPrefix(query: String): List<DictionaryEntry> = withContext(Dispatchers.IO) {
        dictionaryDbHelper.search(query, DictionaryDbHelper.SearchType.PREFIX)
    }

    // 此函数暂时保持不变。
    suspend fun getFavorites(): List<Favorite> = withContext(Dispatchers.IO) {
        favoritesDbHelper.getAllFavorites()
    }

    // 此函数无需更改，我们将把从 entry 中提取 idseq 的逻辑放在 FavoritesDbHelper 中。
    suspend fun addFavorite(entry: DictionaryEntry): Boolean = withContext(Dispatchers.IO) {
        favoritesDbHelper.addFavorite(entry)
    }

    //从仓库层暴露获取多个词条信息的新方法
    suspend fun getEntriesByIds(ids: List<Long>): List<DictionaryEntry> = withContext(Dispatchers.IO) {
        dictionaryDbHelper.getEntriesByIds(ids)
    }

    /**
     * 【核心修改】
     * 删掉收藏的方法。
     * 旧方法使用 word 和 definition 作为参数，这在新数据模型下是不可靠的。
     * 新方法使用唯一的、稳定的 idseq 来精确地删除一个收藏。
     *
     * @param idseq 要删除的词条的唯一ID。
     */
    suspend fun removeFavorite(idseq: Long) = withContext(Dispatchers.IO) {
        // 我们将在下一步修改 FavoritesDbHelper 使其拥有一个接受 idseq 的 removeFavorite 方法
        favoritesDbHelper.removeFavorite(idseq)
    }
}