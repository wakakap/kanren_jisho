// ==========================================
// 全局状态与初始化
// ==========================================
let searchIndex = [];
let debugLog = [];

async function init() {
    try {
        const response = await fetch('./public_dict_data/search_index.json');
        searchIndex = await response.json();
        
        const statusEl = document.getElementById('status');
        statusEl.innerText = `✅ 索引已就绪 (${searchIndex.length})`;
        statusEl.style.color = '#2e7d32';
        
        document.getElementById('searchInput').disabled = false;
        document.getElementById('searchBtn').disabled = false;
        document.getElementById('searchInput').focus();
    } catch (e) {
        const statusEl = document.getElementById('status');
        statusEl.innerText = "❌ 索引加载失败";
        statusEl.style.background = "#ffebee";
        statusEl.style.color = "#c62828";
        console.error("初始化错误:", e);
    }
}

// ==========================================
// 工具类 (OpenCC & Wanakana)
// ==========================================
let convertCnToJp = (text) => text;
if (typeof OpenCC !== 'undefined') {
    convertCnToJp = OpenCC.Converter({ from: 'cn', to: 'jp' });
}

const Utils = {
    isRomaji: (text) => /^[a-zA-Zōūāīē\s]+$/.test(text),
    toHiragana: (romaji) => wanakana.toHiragana(romaji),
    onlyKanji: (query) => (query.match(/[\u4e00-\u9faf]/g) || []).join(''),
    
    getSokuonVariants: (query) => {
        const sokuonKana = new Set([
            'か', 'き', 'く', 'け', 'こ', 'さ', 'し', 'す', 'せ', 'そ',
            'た', 'ち', 'つ', 'て', 'と', 'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ',
            'カ', 'キ', 'ク', 'ケ', 'コ', 'サ', 'シ', 'ス', 'セ', 'ソ',
            'タ', 'チ', 'ツ', 'テ', 'ト', 'パ', 'ピ', 'プ', 'ペ', 'ポ'
        ]);
        const variants = new Set();
        if (query.includes('っ')) variants.add(query.replace(/っ/g, ""));
        for (let i = 1; i < query.length; i++) {
            if (sokuonKana.has(query[i]) && query[i - 1] !== 'っ') {
                variants.add(query.slice(0, i) + 'っ' + query.slice(i));
            }
        }
        return Array.from(variants);
    }
};

const Repo = {
    searchExact: (query) => searchIndex.filter(e => e.kanji.includes(query) || e.kana.includes(query)),
    searchPrefix: (query) => searchIndex.filter(e => 
        e.kanji.some(k => k.startsWith(query)) || e.kana.some(k => k.startsWith(query))
    )
};

// ==========================================
// 核心搜索逻辑
// ==========================================
async function performSearch(query) {
    debugLog = [];
    if (!query || (query.length === 1 && !Utils.isRomaji(query) && !Utils.onlyKanji(query))) {
        return [];
    }

    debugLog.push(`**原始输入:** \`${query}\``);
    
    let processedQuery = query;
    if (Utils.isRomaji(query)) {
        processedQuery = Utils.toHiragana(query);
        debugLog.push(`**阶段:** 罗马音转换 -> \`${processedQuery}\``);
    } else {
        const jpKanji = convertCnToJp(query);
        if (jpKanji !== query) {
            processedQuery = jpKanji;
            debugLog.push(`**阶段:** 中简转日汉 -> \`${processedQuery}\``);
        } else {
            debugLog.push(`**阶段:** 识别为日文`);
        }
    }

    const foundIds = new Set();
    let indexResults = []; 

    debugLog.push(`---`);
    debugLog.push(`**[Tier 1] 完全匹配**`);
    let tier1 = Repo.searchExact(processedQuery);
    tier1.forEach(e => { if(!foundIds.has(e.id)) { indexResults.push(e); foundIds.add(e.id); }});
    debugLog.push(`-> 命中 \`${tier1.length}\` 条`);

    debugLog.push(`---`);
    debugLog.push(`**[建议] 促音容错**`);
    const variants = Utils.getSokuonVariants(processedQuery);
    let sugCount = 0;
    for (const v of variants) {
        Repo.searchExact(v).forEach(e => {
            if(!foundIds.has(e.id)) { indexResults.push(e); foundIds.add(e.id); sugCount++; }
        });
    }
    debugLog.push(`-> 命中 \`${sugCount}\` 条`);

    debugLog.push(`---`);
    debugLog.push(`**[Tier 2] 前缀匹配**`);
    let tier2 = Repo.searchPrefix(processedQuery);
    let tier2Count = 0;
    tier2.forEach(e => {
        if(!foundIds.has(e.id)) { indexResults.push(e); foundIds.add(e.id); tier2Count++; }
    });
    debugLog.push(`-> 命中 \`${tier2Count}\` 条`);

    if (tier1.length === 0 && tier2Count === 0) {
        debugLog.push(`---`);
        debugLog.push(`**[Tier 3] 提取容错匹配**`);
        const tolerantQueries = new Set(variants);
        if (processedQuery.length > 2) tolerantQueries.add(processedQuery.slice(0, -1));
        const kanjiOnly = Utils.onlyKanji(processedQuery);
        if (kanjiOnly && kanjiOnly !== processedQuery) tolerantQueries.add(kanjiOnly);
        
        const queriesArr = Array.from(tolerantQueries);
        debugLog.push(`-> 生成容词: \`${queriesArr.length > 0 ? queriesArr.join(', ') : '无'}\``);
        
        let tier3Count = 0;
        for (const tq of tolerantQueries) {
            if(!tq) continue;
            Repo.searchPrefix(tq).forEach(e => {
                if(!foundIds.has(e.id)) { indexResults.push(e); foundIds.add(e.id); tier3Count++; }
            });
        }
        debugLog.push(`-> 命中 \`${tier3Count}\` 条`);
    }

    debugLog.push(`---`);
    debugLog.push(`**开始拉取 Json 块并打分...**`);

    const limitedResults = indexResults.slice(0, 50);
    return await fetchChunksAndScore(limitedResults, processedQuery);
}

async function fetchChunksAndScore(indexItems, query) {
    if (indexItems.length === 0) return [];
    const chunksNeeded = [...new Set(indexItems.map(item => item.chunk))];
    const chunksData = {};

    for (const chunkFile of chunksNeeded) {
        try {
            const res = await fetch(`./public_dict_data/chunks/${chunkFile}`);
            chunksData[chunkFile] = await res.json();
        } catch (e) {
            console.error(`拉取 ${chunkFile} 失败:`, e);
        }
    }

    const scoredEntries = indexItems.map(item => {
        const fullEntry = chunksData[item.chunk]?.[item.id];
        if (!fullEntry) return null;

        let score = 0;
        const mainPos = fullEntry.sense?.[0]?.partOfSpeech?.[0] || "";
        if (mainPos.startsWith("v")) score += 2000;
        else if (mainPos.startsWith("adj-i")) score += 1800;
        else if (mainPos.startsWith("adj-na")) score += 1700;

        const primaryKanji = fullEntry.kanji?.[0]?.text;
        const primaryKana = fullEntry.kana?.[0]?.text || "";

        if (primaryKanji === query) score += 1000;
        if (primaryKanji && primaryKanji.startsWith(query)) score += 500;
        if (primaryKana.startsWith(query)) score += 500;

        if (fullEntry.kanji?.[0]?.common || fullEntry.kana?.[0]?.common) score += 100;
        score -= primaryKana.length;

        fullEntry._rankingScore = score;
        return fullEntry;
    }).filter(e => e !== null);

    return scoredEntries.sort((a, b) => b._rankingScore - a._rankingScore);
}

// ==========================================
// UI 渲染与事件绑定
// ==========================================

// 将日志数组渲染为漂亮的 HTML
function renderDebugLog() {
    const logDiv = document.getElementById('debugLog');
    const html = debugLog.map(line => {
        if (line === '---') return `<div class="debug-divider"></div>`;
        
        // 解析 markdown 格式的加粗和代码块为高亮样式
        let formatted = line
            .replace(/\*\*(.*?)\*\*/g, '<span class="debug-highlight">$1</span>')
            .replace(/`(.*?)`/g, '<span class="debug-value">$1</span>');
            
        return `<div class="debug-step">${formatted}</div>`;
    }).join('');
    
    logDiv.innerHTML = html;
}

document.getElementById('searchBtn').addEventListener('click', async () => {
    const query = document.getElementById('searchInput').value.trim();
    const resultsDiv = document.getElementById('results');
    
    if (!query) return;

    // 如果在手机端，点击搜索后自动折叠（或确保可见）Debug面板逻辑可在这里扩展
    // 目前默认保持原生 details 的行为

    resultsDiv.innerHTML = '<div class="empty-state">正在查询...</div>';
    document.getElementById('debugLog').innerHTML = '<div class="debug-step">执行中...</div>';
    
    const results = await performSearch(query);
    renderDebugLog();

    if (results.length === 0) {
        resultsDiv.innerHTML = '<div class="empty-state">没有找到相关词条 🥺</div>';
        return;
    }

    resultsDiv.innerHTML = results.map(entry => {
        const kanji = entry.kanji?.[0]?.text || entry.kana?.[0]?.text || '未知';
        const kana = entry.kana?.[0]?.text || '';
        
        const sensesHtml = (entry.sense || []).map(s => {
            const pos = s.partOfSpeech?.join(', ') || '词性未知';
            // 将英文释义拼接
            const gloss = s.gloss?.map(g => g.text).join('; ') || '无释义';
            return `
                <li class="sense-item">
                    <span class="pos-tag">${pos}</span>
                    <span class="gloss">${gloss}</span>
                </li>`;
        }).join('');

        return `
            <div class="entry-card">
                <div class="entry-header">
                    <span class="kanji">${kanji}</span>
                    <span class="kana">【${kana}】</span>
                </div>
                <ul class="sense-list">
                    ${sensesHtml}
                </ul>
                <div class="score-info">Algorithm Score: ${entry._rankingScore}</div>
            </div>
        `;
    }).join('');
});

document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('searchBtn').click();
    }
});

// 启动！
init();