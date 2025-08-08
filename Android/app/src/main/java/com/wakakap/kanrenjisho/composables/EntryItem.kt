package com.wakakap.kanrenjisho.composables

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.StarOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wakakap.kanrenjisho.data.model.DictionaryEntry
import com.wakakap.kanrenjisho.data.model.Sense

@Composable
fun EntryItem(
    entry: DictionaryEntry,
    isFavorite: Boolean,
    onFavoriteClick: (DictionaryEntry) -> Unit,
    modifier: Modifier = Modifier
) {
    var isExpanded by remember { mutableStateOf(false) }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .clickable { isExpanded = !isExpanded },
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        // 【修改】: 使用Box布局，方便将priority数字覆盖在右上角
        Box {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.Top
            ) {
                // 左侧主要内容区域
                Column(modifier = Modifier.weight(1f)) {
                    // 日文头部，始终显示
                    EntryHeader(entry)

                    // 只有在 isExpanded 为 true 时，这个区块才会显示
                    AnimatedVisibility(visible = isExpanded) {
                        Column {
                            Spacer(modifier = Modifier.height(12.dp))
                            SensesSection(entry.senses)
                        }
                    }
                }

                // 右侧收藏按钮
                IconButton(onClick = { onFavoriteClick(entry) }) {
                    Icon(
                        imageVector = if (isFavorite) Icons.Default.Star else Icons.Default.StarOutline,
                        contentDescription = if (isFavorite) "取消收藏" else "收藏",
                        tint = if (isFavorite) MaterialTheme.colorScheme.primary else LocalContentColor.current
                    )
                }
            }

            // 【新增】: 在右上角显示我们计算出的priority数字，用于测试
            Text(
                text = entry.rankingScore.toString(),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier
                    .align(Alignment.TopEnd) // 定位到右上角
                    .padding(top = 4.dp, end = 4.dp)
                    .background(color = MaterialTheme.colorScheme.primary, shape = CircleShape)
                    .padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
    }
}

/**
 * 词条头部：显示汉字和读音 (无需修改)
 */
@Composable
private fun EntryHeader(entry: DictionaryEntry) {
    val primaryKanji = entry.kanjiForms.firstOrNull()
    val primaryReading = entry.readingForms.firstOrNull()

    Row(verticalAlignment = Alignment.CenterVertically) {
        if (primaryKanji != null) {
            Text(text = primaryKanji, style = MaterialTheme.typography.titleLarge)
            primaryReading?.let {
                Text(
                    text = "[$it]",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(start = 8.dp).alpha(0.7f)
                )
            }
        } else {
            primaryReading?.let {
                Text(text = it, style = MaterialTheme.typography.titleLarge)
            }
        }
    }
}

/**
 * 词条核心：显示所有释义
 * 【修改】: 移除了 isExpanded 参数和内部的 AnimatedVisibility
 * 因为它现在只会在展开状态下被调用，所以直接显示所有内容即可。
 */
@Composable
private fun SensesSection(senses: List<Sense>) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        senses.forEachIndexed { index, sense ->
            val prefix = if (senses.size > 1) "${index + 1}. " else ""

            Text(
                text = "$prefix(${sense.partOfSpeech}) ${sense.gloss}",
                style = MaterialTheme.typography.bodyLarge,
                lineHeight = MaterialTheme.typography.bodyLarge.lineHeight * 1.2
            )

            // 直接显示补充信息和例句
            Column(modifier = Modifier.padding(start = 16.dp, top = 6.dp)) {
                sense.info?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        fontStyle = FontStyle.Italic,
                        modifier = Modifier.alpha(0.8f)
                    )
                }
                sense.examples.forEach { example ->
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "・ ${example.japanese}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        text = example.english,
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(start = 12.dp).alpha(0.7f)
                    )
                }
            }
        }
    }
}