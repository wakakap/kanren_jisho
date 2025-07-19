# tw2t.json Traditional Chinese (Taiwan standard) --> Traditional Chinese
# s2t.json Simplified Chinese --> Traditional Chinese 
# hk2t.json Traditional Chinese (Hong Kong variant) --> Traditional Chinese
# ----
# t2jp.json Traditional Chinese Characters (Kyūjitai) --> New Japanese Kanji (Shinjitai) 

import opencc

def convert_to_japanese_char(input_char, area = 'Simplified'):
    if area == 'Simplified':
        converter1 = opencc.OpenCC('s2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        out_char = converter2.convert(converter1.convert(input_char))
    elif area == 'Traditional':
        converter1 = opencc.OpenCC('hk2t.json')
        out_char = converter1.convert(input_char)
    elif area == 'Taiwan Traditional':
        converter1 = opencc.OpenCC('tw2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        out_char = converter2.convert(converter1.convert(input_char))
    elif area == 'Hong Kong variant':
        converter1 = opencc.OpenCC('hk2t.json')
        converter2 = opencc.OpenCC('t2jp.json')
        out_char = converter2.convert(converter1.convert(input_char))
    else:
        out_char ="converter select error"
    
    return out_char

# Test cases
test_chars = ['沢泽，明天我要去野餐，做一个机械椅子，然后做实验，检测一下']  # Simplified, Traditional, HK Traditional, Simplified
for char in test_chars:
    result = convert_to_japanese_char(char, area = 'Simplified')
    print(f"Input: {char} -> Output: {result}")