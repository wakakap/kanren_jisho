package com.wakakap.kanrenjisho.ui.composables

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.wakakap.kanrenjisho.composables.EntryItem
import com.wakakap.kanrenjisho.data.model.DictionaryEntry

/**
 * 收藏夹的UI组件
 * @param favorites 收藏的词条列表 (现在是完整的 DictionaryEntry 对象)
 * @param onFavoriteClick 点击收藏按钮的回调
 */
@Composable
fun FavoritesSheet(
    favorites: List<DictionaryEntry>,
    onFavoriteClick: (DictionaryEntry) -> Unit
) {
    // 【修改】: 移除了外层的Column和原有的标题Text及Spacer
    // 现在这个组件只负责显示列表或空状态提示
    Box(
        modifier = Modifier
            .fillMaxSize() // 让内容区填满可用空间
            .padding(16.dp)
    ) {
        if (favorites.isEmpty()) {
            Text("这里还没有收藏的单词。")
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(
                    items = favorites,
                    key = { it.idseq }
                ) { entry ->
                    EntryItem(
                        entry = entry,
                        isFavorite = true,
                        onFavoriteClick = onFavoriteClick
                    )
                }
            }
        }
    }
}

/*
 * 私有的 FavoriteItem 组件已被删除。
 * 我们现在统一使用功能更强大的 EntryItem 组件来显示词条，
 * 保证了应用内UI的一致性。
 */