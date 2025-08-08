package com.wakakap.kanrenjisho.util
//大陆简体 ==》日文
import com.github.houbb.opencc4j.util.ZhJpConverterUtil

import dev.esnault.wanakana.core.Wanakana
import java.util.regex.Pattern

object ConversionUtils {

    private val romajiPattern = Pattern.compile("^[a-zA-Zōūāīē\\s]+$")
    fun isRomaji(text: String): Boolean {
        return romajiPattern.matcher(text).matches()
    }

    // 现在 WanaKana 可以被正确识别了
    fun toHiragana(romaji: String): String {
        return Wanakana.toHiragana(romaji)
    }

    fun convertChineseToJapaneseKanji(query: String): String {
        val toJpankanji = ZhJpConverterUtil.toTraditional(query)
        return toJpankanji
    }
}