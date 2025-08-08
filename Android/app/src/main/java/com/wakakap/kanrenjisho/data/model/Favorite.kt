package com.wakakap.kanrenjisho.data.model

/**
 * 代表一个收藏记录。
 * 只存储所收藏词条的唯一ID (idseq)，作为一个指向主词典数据库的引用。
 */
data class Favorite(
    val entry_idseq: Long
)