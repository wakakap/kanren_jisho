package com.wakakap.kanrenjisho.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.repository.DictionaryRepository
import com.wakakap.kanrenjisho.util.ConversionUtils
import com.wakakap.kanrenjisho.util.SearchUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class SearchUiState {
    object Idle : SearchUiState()
    object Loading : SearchUiState()
    data class Success(val results: SearchResult) : SearchUiState()
    data class Error(val message: String) : SearchUiState()
}

data class SearchResult(
    val tier1Entries: List<DictionaryEntry> = emptyList(),
    val suggestions: List<DictionaryEntry> = emptyList(),
    val tier2Entries: List<DictionaryEntry> = emptyList(),
    val tier3Entries: List<DictionaryEntry> = emptyList(),
    val debugLog: List<String> = emptyList()
)

class DictionaryViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = DictionaryRepository(application)

    private val _uiState = MutableStateFlow<SearchUiState>(SearchUiState.Idle)
    val uiState = _uiState.asStateFlow()

    private val _favorites = MutableStateFlow<List<DictionaryEntry>>(emptyList())
    val favorites = _favorites.asStateFlow()

    init {
        loadFavorites()
    }

    private fun sortResults(entries: List<DictionaryEntry>, query: String): List<DictionaryEntry> {
        val verbBonus = 2000
        val adjIBonus = 1800
        val adjNaBonus = 1700
        val exactMatchBonus = 1000
        val prefixMatchBonus = 500

        // 步骤1: 使用 map 为每个词条计算分数，并用 copy() 创建带有分数的新对象
        val scoredEntries = entries.map { entry ->
            var score = 0

            // 1. 词性权重
            val mainPos = entry.senses.firstOrNull()?.partOfSpeech ?: ""
            when {
                mainPos.startsWith("v") -> score += verbBonus
                mainPos.startsWith("adj-i") -> score += adjIBonus
                mainPos.startsWith("adj-na") -> score += adjNaBonus
            }

            // 2. 查询词匹配权重
            val primaryKanji = entry.kanjiForms.firstOrNull()
            val primaryReading = entry.readingForms.firstOrNull() ?: ""

            if (primaryKanji == query) {
                score += exactMatchBonus
            }
            if (primaryKanji?.startsWith(query) == true) {
                score += prefixMatchBonus
            }
            if (primaryReading.startsWith(query)) {
                score += prefixMatchBonus
            }

            // 3. 基础常用度分数
            score += entry.priority

            // 4. 长度惩罚
            score -= primaryReading.length

            // 【核心】: 使用copy()创建一个新的entry实例，并把计算出的分数存入rankingScore字段
            entry.copy(rankingScore = score)
        }

        // 步骤2: 根据我们刚刚存入的 rankingScore 字段进行降序排序
        return scoredEntries.sortedByDescending { it.rankingScore }
    }
    fun search(query: String) {
        if (query.isBlank() || (query.length == 1 && !ConversionUtils.isRomaji(query) && SearchUtils.onlyKanji(query).isEmpty())) {
            _uiState.value = SearchUiState.Idle
            return
        }

        viewModelScope.launch {
            _uiState.value = SearchUiState.Loading
            val debugLog = mutableListOf<String>()

            try {
                // 1. 预处理查询词 (逻辑不变)
                debugLog.add("**原始输入:** `$query`")
                val processedQuery = if (ConversionUtils.isRomaji(query)) {
                    val hira = ConversionUtils.toHiragana(query)
                    debugLog.add("**判断:** 罗马音 -> `$hira`")
                    hira
                } else {
                    val jpKanji = ConversionUtils.convertChineseToJapaneseKanji(query)
                    if (jpKanji != query) debugLog.add("**判断:** 中文 -> `$jpKanji`")
                    else debugLog.add("**判断:** 日文")
                    jpKanji
                }

                val foundIds = mutableSetOf<Long>()

                // 2. Tier 1: 完全匹配
                debugLog.add("\n---\n**层级 1: 完全匹配**\n---")
                var tier1Results = repository.searchExact(processedQuery)
                tier1Results = sortResults(tier1Results,processedQuery) // 【修改】: 在这里调用排序
                tier1Results.forEach { foundIds.add(it.idseq) }
                debugLog.add("找到 ${tier1Results.size} 个新结果")

                // 3. Suggestions: 促音容错建议
                debugLog.add("\n---\n**促音容错**\n---")
                val sokuonVariants = SearchUtils.getSokuonVariants(processedQuery)
                val suggestionsMutable = mutableListOf<DictionaryEntry>()
                for (variant in sokuonVariants) {
                    repository.searchExact(variant).forEach {
                        if (it.idseq !in foundIds) {
                            suggestionsMutable.add(it)
                            foundIds.add(it.idseq)
                        }
                    }
                }
                val suggestions = sortResults(suggestionsMutable,processedQuery) // 【修改】: 在这里调用排序
                debugLog.add("找到 ${suggestions.size} 个建议词")

                // 4. Tier 2: 前缀匹配
                debugLog.add("\n---\n**层级 2: 前缀匹配**\n---")
                var tier2Results = repository.searchPrefix(processedQuery)
                    .filter { it.idseq !in foundIds }
                tier2Results = sortResults(tier2Results,processedQuery) // 【修改】: 在这里调用排序
                tier2Results.forEach { foundIds.add(it.idseq) }
                debugLog.add("找到 ${tier2Results.size} 个新结果")

                // 5. Tier 3: 容错匹配
                var tier3Results = emptyList<DictionaryEntry>()
                // 【优化】: 将 || (或) 改为 && (与)，仅在Tier1和Tier2都没有结果时才进行容错搜索
                if (tier1Results.isEmpty() && tier2Results.isEmpty()) {
                    debugLog.add("\n---\n**层级 3: 容错匹配**\n---")
                    val tolerantQueries = mutableSetOf<String>()
                    tolerantQueries.addAll(sokuonVariants)
                    if (processedQuery.length > 2) tolerantQueries.add(processedQuery.dropLast(1))
                    val kanjiOnly = SearchUtils.onlyKanji(processedQuery)
                    if (kanjiOnly.isNotEmpty() && kanjiOnly != processedQuery) tolerantQueries.add(kanjiOnly)

                    debugLog.add("生成容错搜索词: `$tolerantQueries`")
                    val tolerantResultsTemp = mutableListOf<DictionaryEntry>()
                    for (tQuery in tolerantQueries) {
                        if (tQuery.isBlank()) continue
                        repository.searchPrefix(tQuery).forEach {
                            if (it.idseq !in foundIds) {
                                tolerantResultsTemp.add(it)
                                foundIds.add(it.idseq)
                            }
                        }
                    }
                    tier3Results = sortResults(tolerantResultsTemp,processedQuery) // 【修改】: 在这里调用排序
                    debugLog.add("找到 ${tier3Results.size} 个新结果")
                }

                debugLog.add("\n---\n**所有搜索已完成**\n---")

                // 最终将排好序的结果传递给UI状态
                _uiState.value = SearchUiState.Success(
                    SearchResult(
                        tier1Entries = tier1Results,
                        suggestions = suggestions,
                        tier2Entries = tier2Results,
                        tier3Entries = tier3Results,
                        debugLog = debugLog
                    )
                )

            } catch (e: Exception) {
                _uiState.value = SearchUiState.Error("搜索过程中发生错误: ${e.message}")
            }
        }
    }

    // --- 收藏夹相关操作 (保持不变) ---
    fun loadFavorites() {
        viewModelScope.launch {
            val favoriteIds = repository.getFavorites().map { it.entry_idseq }
            if (favoriteIds.isNotEmpty()) {
                try {
                    val favoriteEntries = repository.getEntriesByIds(favoriteIds)
                    _favorites.value = favoriteEntries
                } catch (e: Exception) {
                    _favorites.value = emptyList()
                }
            } else {
                _favorites.value = emptyList()
            }
        }
    }

    fun addFavorite(entry: DictionaryEntry) {
        viewModelScope.launch {
            val success = repository.addFavorite(entry)
            if (success) {
                loadFavorites()
            }
        }
    }

    fun removeFavorite(entry: DictionaryEntry) {
        viewModelScope.launch {
            repository.removeFavorite(entry.idseq)
            loadFavorites()
        }
    }
}