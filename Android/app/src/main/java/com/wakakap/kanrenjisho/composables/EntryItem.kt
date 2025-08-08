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
        Box {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    EntryHeader(entry)

                    AnimatedVisibility(visible = isExpanded) {
                        // 我们只保留这个外层Column用于动画
                        Column {
                            // 为了头部和释义之间有呼吸感，保留一个Spacer
                            Spacer(modifier = Modifier.height(12.dp))
                            SensesSection(entry.senses)
                        }
                    }
                }

                IconButton(onClick = { onFavoriteClick(entry) }) {
                    Icon(
                        imageVector = if (isFavorite) Icons.Default.Star else Icons.Default.StarOutline,
                        contentDescription = if (isFavorite) "取消收藏" else "收藏",
                        tint = if (isFavorite) MaterialTheme.colorScheme.primary else LocalContentColor.current
                    )
                }
            }

            Text(
                text = entry.rankingScore.toString(),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(top = 4.dp, end = 4.dp)
                    .background(color = MaterialTheme.colorScheme.primary, shape = CircleShape)
                    .padding(horizontal = 6.dp, vertical = 2.dp)
            )
        }
    }
}

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
@Composable
private fun SensesSection(senses: List<Sense>) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        senses.forEachIndexed { index, sense ->
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                val prefix = if (senses.size > 1) "${index + 1}. " else ""
                Text(
                    text = "$prefix(${sense.partOfSpeech}) ${sense.gloss}",
                    style = MaterialTheme.typography.bodyLarge
                )
                // 2. 補足情報 (存在する場合)
//                sense.info?.let {
//                    Text(
//                        text = it,
//                        style = MaterialTheme.typography.bodySmall,
//                        fontStyle = FontStyle.Italic,
//                        modifier = Modifier.alpha(0.8f)
//                    )
//                }
                // 3. すべての例文
                sense.examples.forEach { example ->
                    // 日本語の例文
                    Text(
                        text = "例：${example.japanese}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    // 英語の例文
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