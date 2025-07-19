
# 骑术 騎術 qi2 shu4] /equestrianism/horsemanship
with open("./dic/cedict_ts.u8", encoding="utf-8") as f:
    temp = 1
    for line in f:
        if line.startswith("#"):
            continue
        parts = line.strip().split(" ")
        traditional, simplified = parts[0], parts[1]
        pinyin = parts[2].strip("[]")
        meanings = " ".join(parts[3:]).strip("/")
        print(simplified, traditional, pinyin, meanings)
        temp=temp + 1
        if temp >= 350:
            break