package com.wakakap.kanrenjisho.ui.composables

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.wakakap.kanrenjisho.composables.EntryItem
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.ui.viewmodel.DictionaryViewModel
import com.wakakap.kanrenjisho.ui.viewmodel.SearchResult
import com.wakakap.kanrenjisho.ui.viewmodel.SearchUiState
import kotlinx.coroutines.delay

private enum class CurrentScreen {
    Search, Favorites
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(viewModel: DictionaryViewModel) {
    var currentScreen by remember { mutableStateOf(CurrentScreen.Search) }
    var text by remember { mutableStateOf("") }

    val uiState by viewModel.uiState.collectAsState()
    val favorites by viewModel.favorites.collectAsState()

    LaunchedEffect(text) {
        delay(1000L)
        if (currentScreen == CurrentScreen.Search) {
            viewModel.search(text)
        }
    }

    Scaffold(
        topBar = {
            when (currentScreen) {
                CurrentScreen.Search -> {
                    TopAppBar(
                        title = { Text("漢連辞書") },
                        actions = {
                            IconButton(onClick = { currentScreen = CurrentScreen.Favorites }) {
                                Icon(imageVector = Icons.Default.Star, contentDescription = "打开收藏夹")
                            }
                        }
                    )
                }
                CurrentScreen.Favorites -> {
                    TopAppBar(
                        title = { Text("⭐ 收藏夹") },
                        navigationIcon = {
                            IconButton(onClick = { currentScreen = CurrentScreen.Search }) {
                                Icon(imageVector = Icons.Default.ArrowBack, contentDescription = "返回搜索页面")
                            }
                        }
                    )
                }
            }
        }
    ) { paddingValues ->
        when (currentScreen) {
            CurrentScreen.Search -> {
                SearchContent(
                    modifier = Modifier.padding(paddingValues),
                    text = text,
                    onTextChange = { newText -> text = newText },
                    uiState = uiState,
                    favorites = favorites,
                    onFavoriteClick = { entry, isFavorite ->
                        if (isFavorite) viewModel.removeFavorite(entry) else viewModel.addFavorite(entry)
                    },
                    onSuggestionClick = { suggestionText ->
                        // 当点击建议词时，更新搜索框文本，这会自动触发新的防抖搜索
                        text = suggestionText
                    }
                )
            }
            CurrentScreen.Favorites -> {
                Box(modifier = Modifier.padding(paddingValues)) {
                    FavoritesSheet(
                        favorites = favorites,
                        onFavoriteClick = { entry ->
                            viewModel.removeFavorite(entry)
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun SearchContent(
    modifier: Modifier = Modifier,
    text: String,
    onTextChange: (String) -> Unit,
    uiState: SearchUiState,
    favorites: List<DictionaryEntry>,
    onFavoriteClick: (DictionaryEntry, Boolean) -> Unit,
    onSuggestionClick: (String) -> Unit
) {
    Row(
        modifier = modifier
            .fillMaxSize()
            .padding(8.dp)
    ) {
        // 左侧：搜索和结果
        Column(modifier = Modifier.weight(2f)) {
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                label = { Text("输入日语、假名、罗马音或汉字...") },
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(8.dp))

            when (val state = uiState) {
                is SearchUiState.Idle -> {}
                is SearchUiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
                is SearchUiState.Error -> {
                    Text("错误: ${state.message}", color = MaterialTheme.colorScheme.error)
                }
                is SearchUiState.Success -> {
                    if (state.results.tier1Entries.isEmpty() && state.results.tier2Entries.isEmpty() &&
                        state.results.tier3Entries.isEmpty() && state.results.suggestions.isEmpty()
                    ) {
                        if (text.isNotEmpty()) {
                            Text("找不到与 '$text' 相关的结果。")
                        }
                    } else {
                        ResultsList(
                            results = state.results,
                            favorites = favorites,
                            onFavoriteClick = onFavoriteClick,
                            onSuggestionClick = onSuggestionClick
                        )
                    }
                }
            }
        }
        // 右侧：调试日志
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(start = 8.dp)
        ) {
            Text("⚙️ 搜索过程分析", style = MaterialTheme.typography.titleMedium)
            Divider(modifier = Modifier.padding(vertical = 4.dp))
            LazyColumn {
                val log = when (val state = uiState) {
                    is SearchUiState.Success -> state.results.debugLog
                    else -> emptyList()
                }
                items(log) { logItem ->
                    Text(logItem, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}


@Composable
private fun ResultsList(
    results: SearchResult,
    favorites: List<DictionaryEntry>,
    onFavoriteClick: (entry: DictionaryEntry, isFavorite: Boolean) -> Unit,
    onSuggestionClick: (String) -> Unit
) {
    val favoriteIds = remember(favorites) { favorites.map { it.idseq }.toSet() }

    LazyColumn(
        contentPadding = PaddingValues(vertical = 8.dp)
    ) {
//        // 建议词（恢复了原来的按钮样式）
//        if (results.suggestions.isNotEmpty()) {
//            item {
//                Text("您是不是想找：", style = MaterialTheme.typography.titleMedium)
//                LazyRow(
//                    horizontalArrangement = Arrangement.spacedBy(8.dp),
//                    contentPadding = PaddingValues(vertical = 4.dp)
//                ) {
//                    items(results.suggestions) { suggestion ->
//                        val suggestionText = suggestion.kanjiForms.firstOrNull() ?: suggestion.readingForms.first()
//                        Button(onClick = { onSuggestionClick(suggestionText) }) {
//                            Text(suggestionText)
//                        }
//                    }
//                }
//                Divider(modifier = Modifier.padding(vertical = 8.dp))
//            }
//        }

        // 封装的渲染函数
        fun renderTier(title: String, entries: List<DictionaryEntry>) {
            if (entries.isNotEmpty()) {
                item {
                    Text(title, style = MaterialTheme.typography.titleMedium)
                }
                items(entries, key = { "tier_${it.idseq}" }) { entry ->
                    val isFavorite = entry.idseq in favoriteIds
                    EntryItem(
                        entry = entry,
                        isFavorite = isFavorite,
                        onFavoriteClick = { onFavoriteClick(entry, isFavorite) }
                    )
                }
                item { Spacer(modifier = Modifier.height(16.dp)) }
            }
        }

        // 渲染所有层级
        renderTier("精确匹配结果", results.tier1Entries)
        renderTier("促音模糊结果", results.suggestions)
        renderTier("前缀匹配结果", results.tier2Entries)
        renderTier("容错匹配结果", results.tier3Entries)
    }
}