package com.wakakap.kanrenjisho.util

import java.util.regex.Pattern

object SearchUtils {

    private val kanjiPattern = Pattern.compile("[\\u4e00-\\u9faf]")

    fun onlyKanji(query: String): String {
        val matcher = kanjiPattern.matcher(query)
        val builder = StringBuilder()
        while (matcher.find()) {
            builder.append(matcher.group())
        }
        return builder.toString()
    }

    // 👇👇👇【修正】: 集合的类型改为 Set<Char>，并只包含单字符假名。
    private val SOKUON_KANA: Set<Char> = setOf(
        'か', 'き', 'く', 'け', 'こ',
        'さ', 'し', 'す', 'せ', 'そ',
        'た', 'ち', 'つ', 'て', 'と',
        'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ',
        'カ', 'キ', 'ク', 'ケ', 'コ',
        'サ', 'シ', 'ス', 'セ', 'ソ',
        'タ', 'チ', 'ツ', 'テ', 'ト',
        'パ', 'ピ', 'プ', 'ペ', 'ポ'
    )

    fun getSokuonVariants(query: String): Set<String> {
        val variants = mutableSetOf<String>()

        if (query.contains('っ')) {
            variants.add(query.replace("っ", ""))
        }

        for (i in 1 until query.length) {
            // 👇👇👇【修正】: 现在这里的逻辑是正确的，因为 query[i] 是 Char 类型
            if (query[i] in SOKUON_KANA && query[i - 1] != 'っ') {
                val newVariant = query.substring(0, i) + 'っ' + query.substring(i)
                variants.add(newVariant)
            }
        }
        return variants
    }
}