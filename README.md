# kanren_jisho
japanese jisho for kanji people

## 开发记录

- 250720: `app_f.py` 最基础的功能，日文搜索必须完全匹配，英文搜索会有很多项目，中文汉字会搜不到。`app_STJ.py` 加入转换函数，最开始考虑直接读取某个做好的map，但发现只用考虑从「简」「繁」到「日」的转换，map还要考虑多对1的情况比较麻烦。所以直接用转换函数。效果不错，例如搜索「泽」可以得到「沢」。但还没有做模糊搜索和动词等优先级问题的功能。

## 参考

[「一般の社会生活における、現代国語表記上の漢字使用の目安」として、1981年10月1日に内閣告示された、「常用漢字表」に盛り込まれた1945字。](https://www.aozora.gr.jp/kanji_table/)

[2010年、常用漢字が改定されました。2,136 新常用漢字とその音訓のリストです。](https://www.coscom.co.jp/japanesekanji/joyokanji01.html) , [pdf](https://www.coscom.co.jp/japanesekanji/joyokanji_list.pdf)

