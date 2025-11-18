import os
import re
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string, request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', "AIzaSyC3_wvgtzA06HSI9Jb_hReF0rz_qQozpUA")
TIMEOUT_SHORT = 10
TIMEOUT_LONG = 30
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NeuroSync - Smart Learning Curator</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh; padding: 20px;}
    .container { max-width: 1000px; margin: 0 auto; }
    .header { text-align: center; color: white; margin-bottom: 30px; }
    .header h1 { font-size: 2.6em; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .header p { font-size: 1.1em; opacity: 0.9; }
    .search-box { background: white; padding: 24px; border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 20px; }
    .row { display: flex; gap: 10px; }
    input[type=text] { flex: 1; padding: 14px; font-size: 1em; border: 2px solid #ddd; border-radius: 8px; }
    input[type=text]:focus { outline: none; border-color: #667eea; }
    button { padding: 14px 18px; font-size: 1em; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; }
    button:hover { filter: brightness(1.03); }
    .loading, .error { text-align: center; color: white; font-size: 1.05em; padding: 10px; display: none; }
    .grid { display: grid; gap: 16px; grid-template-columns: 1fr; }
    @media (min-width: 900px) { .grid { grid-template-columns: 1fr 1fr; } }
    .card { background: linear-gradient(145deg,#fff,rgba(255,255,255,0.7)); padding: 20px; border-radius: 14px; box-shadow: 0 12px 24px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.4); backdrop-filter: blur(4px); position: relative; overflow: hidden; }
    .card:before { content: ''; position: absolute; top: -40px; right: -40px; width: 120px; height: 120px; background: rgba(118,75,162,0.12); border-radius: 50%; }
    .card h3 { color: #4c51bf; display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 1.1em; }
    .title { color: #1a202c; font-weight: 600; margin-bottom: 8px; }
    .meta { color: #4a5568; font-size: 0.92em; margin-bottom: 8px; }
    #aiCard::before { background: rgba(102,126,234,0.2); }
    #ytCard::before { background: rgba(236,88,88,0.18); }
    #gfgCard::before { background: rgba(72,187,120,0.18); }
    #ghCard::before { background: rgba(67,97,238,0.18); }
    #lcCard::before { background: rgba(237,137,54,0.18); }
    #roadmapCard { background: linear-gradient(135deg,rgba(255,255,255,0.95),rgba(120,90,200,0.2)); border: 1px solid rgba(102,126,234,0.3); }
    #roadmapCard::before { background: rgba(120,90,200,0.25); }
    .roadmap-level { margin: 12px 0; padding: 14px; border-radius: 12px; background: linear-gradient(135deg,rgba(102,126,234,0.12),rgba(118,75,162,0.08)); border: 1px solid rgba(102,126,234,0.15); }
    .roadmap-level h4 { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; color: #3730a3; font-size: 1em; letter-spacing: 0.2px; }
    .roadmap-items { display: flex; flex-wrap: wrap; gap: 8px; }
    .roadmap-item { padding: 6px 12px; border-radius: 999px; background: white; box-shadow: 0 10px 24px rgba(76,81,191,0.18); font-size: 0.9em; color: #2d3748; }
    a { color: #667eea; text-decoration: none; word-break: break-all; }
    a:hover { text-decoration: underline; }
    ul { padding-left: 18px; }
    .section { margin-top: 10px; }
    .diff-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600; margin-left: 8px; }
    .diff-easy { background: linear-gradient(135deg,#48bb78,#38a169); color: white; }
    .diff-medium { background: linear-gradient(135deg,#ed8936,#dd6b20); color: white; }
    .diff-hard { background: linear-gradient(135deg,#f56565,#e53e3e); color: white; }
    .quiz-q { margin: 16px 0; padding: 12px; background: rgba(102,126,234,0.08); border-radius: 10px; }
    .quiz-q h4 { color: #2d3748; margin-bottom: 10px; font-size: 0.95em; }
    .quiz-opt { display: block; padding: 10px 14px; margin: 6px 0; background: white; border: 2px solid #e2e8f0; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
    .quiz-opt:hover { border-color: #667eea; background: #f7fafc; }
    .quiz-opt.correct { background: #c6f6d5; border-color: #48bb78; }
    .quiz-opt.wrong { background: #fed7d7; border-color: #f56565; }
    .quiz-score { text-align: center; padding: 16px; background: linear-gradient(135deg,rgba(102,126,234,0.15),rgba(118,75,162,0.1)); border-radius: 12px; margin-top: 12px; font-weight: 600; color: #3730a3; }
    .history-sidebar { position: fixed; right: 20px; top: 80px; width: 240px; background: white; padding: 16px; border-radius: 16px; box-shadow: 0 10px 24px rgba(76,81,191,0.2); max-height: 400px; overflow-y: auto; }
    .history-item { padding: 8px 12px; margin: 6px 0; background: #f7fafc; border-radius: 8px; cursor: pointer; font-size: 0.9em; transition: all 0.2s; }
    .history-item:hover { background: #edf2f7; transform: translateX(-4px); }
    .points-badge { position: fixed; top: 20px; right: 20px; background: linear-gradient(135deg,#ffd700,#ffed4e); color: #1a202c; padding: 12px 20px; border-radius: 999px; font-weight: 700; font-size: 1.1em; box-shadow: 0 4px 12px rgba(255,215,0,0.4); z-index: 100; }
    .points-badge::before { content: '🏆 '; }
    .achievement { display: inline-block; padding: 6px 12px; margin: 4px; background: linear-gradient(135deg,#667eea,#764ba2); color: white; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
  </style>
</head>
<body>
  <div class="points-badge" id="pointsBadge">0 pts</div>
  <div class="history-sidebar" id="historySidebar" style="display:none;">
    <h4 style="margin-top:0; color:#2d3748;">📚 Recent Searches</h4>
    <div id="historyList"></div>
  </div>
  <div class="container">
    <div class="header">
      <h1>🎓 NeuroSync</h1>
      <p>Curate top resources from YouTube, GeeksforGeeks, GitHub, and LeetCode — plus an AI summary.</p>
    </div>
    <div class="search-box">
      <div class="row">
        <input id="topicInput" type="text" placeholder="Enter a topic (e.g., Binary Search, Machine Learning)" required />
        <button id="searchBtn">🔍 Curate</button>
      </div>
    </div>
    <div id="loading" class="loading">⏳ Curating best resources for you...</div>
    <div id="error" class="error"></div>
    <div id="results" style="display:none;">
      <div class="card section" id="aiCard" style="display:none; margin-bottom: 20px;">
        <h3>🧠 AI Summary<span id="diffBadge"></span></h3>
        <div id="aiSummary" class="meta"></div>
        <div id="aiPrereqWrap" class="meta" style="margin-top:8px;"></div> </div>
      <div class="grid">
        <div class="card" id="ytCard" style="display:none;">
          <h3>🎥 YouTube</h3>
          <div class="title" id="ytTitle"></div>
          <div class="meta" id="ytViews"></div>
          <a id="ytLink" target="_blank"></a></div>
        <div class="card" id="gfgCard" style="display:none;">
          <h3>📄 GeeksforGeeks</h3>
          <div class="title" id="gfgTitle"></div>
          <a id="gfgLink" target="_blank"></a></div>
        <div class="card" id="ghCard" style="display:none;">
          <h3>💻 GitHub</h3>
          <div class="title" id="ghTitle"></div>
          <div class="meta" id="ghStars"></div>
          <a id="ghLink" target="_blank"></a></div>
        <div class="card" id="lcCard" style="display:none;">
          <h3>🧩 LeetCode</h3>
          <ul id="lcList"></ul></div>
        <div class="card" id="roadmapCard" style="display:none; grid-column: 1 / -1;">
          <h3>🚀 Learning Roadmap</h3>
          <div id="roadmapContent"></div> </div>
        <div class="card" id="quizCard" style="display:none; grid-column: 1 / -1;">
          <h3>🎯 Quick Knowledge Check</h3>
          <div id="quizContent"></div>
        </div>
      </div>
    </div>
  </div>
  <script>
    const topicEl = document.getElementById('topicInput');
    const btn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const errEl = document.getElementById('error');
    const results = document.getElementById('results');
    let userPoints = parseInt(localStorage.getItem('neuroPoints') || '0');
    document.getElementById('pointsBadge').textContent = userPoints + ' pts';
    function saveToHistory(topic) {
      let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
      history = history.filter(t => t !== topic);
      history.unshift(topic);
      history = history.slice(0, 8);
      localStorage.setItem('searchHistory', JSON.stringify(history));
      updateHistorySidebar();}
    function updateHistorySidebar() {
      const history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
      const historyList = document.getElementById('historyList');
      const sidebar = document.getElementById('historySidebar');
      if (history.length > 0) {
        sidebar.style.display = 'block';
        historyList.innerHTML = history.map(t => 
          `<div class="history-item" onclick="searchFromHistory('${t.replace(/'/g, "\\'")}')">🔍 ${t}</div>`
        ).join('');
      } else {
        sidebar.style.display = 'none';}
    }
    function searchFromHistory(topic) {
      topicEl.value = topic;
      curate();
    }
    function addPoints(points, reason) {
      userPoints += points;
      localStorage.setItem('neuroPoints', userPoints);
      document.getElementById('pointsBadge').textContent = userPoints + ' pts';
      showAchievement(reason);
    }
    function showAchievement(text) {
      const badge = document.createElement('div');
      badge.className = 'achievement';
      badge.textContent = text;
      badge.style.position = 'fixed';
      badge.style.top = '80px';
      badge.style.right = '20px';
      badge.style.zIndex = '1000';
      document.body.appendChild(badge);
      setTimeout(() => badge.remove(), 3000);
    }
    updateHistorySidebar();
    function fmt(n) { try { return new Intl.NumberFormat().format(n); } catch { return n; } }
    async function curate() {
      const topic = topicEl.value.trim();
      if (!topic) { alert('Enter a topic!'); return; }
      saveToHistory(topic);
      loading.style.display = 'block';
      errEl.style.display = 'none';
      results.style.display = 'none';
      try {
        const res = await fetch('/api/curate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic })
        });
        if (!res.ok) throw new Error('Request failed');
        const data = await res.json();
        render(data);
      } catch (e) {
        errEl.textContent = 'Failed to curate resources. Please try again later.';
        errEl.style.display = 'block';
      } finally {
        loading.style.display = 'none';
      }
    }
    function setCard(id, visible) { document.getElementById(id).style.display = visible ? 'block' : 'none'; }
    function render(data) {
      results.style.display = 'block';
      const ai = data.ai_summary || {};
      if (ai.summary || (ai.prerequisites && ai.prerequisites.length)) {
        setCard('aiCard', true);
        document.getElementById('aiSummary').textContent = ai.summary || '';
        const pre = ai.prerequisites || [];
        document.getElementById('aiPrereqWrap').innerHTML = pre.length ? ('Prerequisites: ' + pre.map(x => `<code>${x}</code>`).join(', ')) : '';
        const diff = ai.difficulty || '';
        const diffMap = {beginner:'easy',intermediate:'medium',advanced:'hard',easy:'easy',medium:'medium',hard:'hard'};
        const diffClass = diffMap[diff.toLowerCase()] || '';
        document.getElementById('diffBadge').innerHTML = diffClass ? `<span class="diff-badge diff-${diffClass}">${diff.charAt(0).toUpperCase()+diff.slice(1)}</span>` : '';
      } else { setCard('aiCard', false); }
      const roadmap = ai.roadmap;
      if (roadmap) {
        const html = [['beginner', '👶'], ['intermediate', '👨‍💻'], ['advanced', '🔥']]
          .map(([key, icon]) => {
            const items = (roadmap[key] || []).map(item => `<div class="roadmap-item">${item}</div>`).join('');
            return items ? `<div class="roadmap-level"><h4>${icon} ${key[0].toUpperCase() + key.slice(1)}</h4><div class="roadmap-items">${items}</div></div>` : '';
          }).join('');
        if (html) {
          setCard('roadmapCard', true);
          document.getElementById('roadmapContent').innerHTML = html;
        } else { setCard('roadmapCard', false); }
      } else { setCard('roadmapCard', false); }
      if (data.youtube) {
        setCard('ytCard', true);
        document.getElementById('ytTitle').textContent = data.youtube.title || '';
        document.getElementById('ytViews').textContent = (data.youtube.views ? `👁️ ${fmt(data.youtube.views)} views` : '');
        const a = document.getElementById('ytLink'); a.textContent = data.youtube.url || ''; a.href = data.youtube.url || '#';
      } else { setCard('ytCard', false); }
      if (data.gfg) {
        setCard('gfgCard', true);
        document.getElementById('gfgTitle').textContent = data.gfg.title || '';
        const a = document.getElementById('gfgLink'); a.textContent = data.gfg.url || ''; a.href = data.gfg.url || '#';
      } else { setCard('gfgCard', false); }
      if (data.github) {
        setCard('ghCard', true);
        document.getElementById('ghTitle').textContent = data.github.title || '';
        document.getElementById('ghStars').textContent = (data.github.stars ? `⭐ ${fmt(data.github.stars)} stars` : '');
        const a = document.getElementById('ghLink'); a.textContent = data.github.url || ''; a.href = data.github.url || '#';
      } else { setCard('ghCard', false); }
      const lc = data.leetcode || [];
      if (Array.isArray(lc) && lc.length) {
        setCard('lcCard', true);
        const ul = document.getElementById('lcList');
        ul.innerHTML = '';
        lc.slice(0, 5).forEach(p => {
          const li = document.createElement('li');
          const a = document.createElement('a');
          a.href = p.url || '#'; a.target = '_blank';
          a.textContent = `${p.id ? '[' + p.id + '] ' : ''}${p.title || 'Problem'}${p.difficulty ? ' (' + p.difficulty + ')' : ''}`;
          li.appendChild(a); ul.appendChild(li);
        });
      } else { setCard('lcCard', false); }
      const quiz = ai.quiz || [];
      if (Array.isArray(quiz) && quiz.length) {
        setCard('quizCard', true);
        let html = '';
        quiz.forEach((q, i) => {
          html += `<div class="quiz-q" data-idx="${i}"><h4>${i+1}. ${q.question}</h4>`;
          q.options.forEach((opt, j) => {
            html += `<div class="quiz-opt" data-qidx="${i}" data-oidx="${j}" data-correct="${j === q.correct}">${opt}</div>`;
          });
          html += `</div>`;
        });
        html += `<div class="quiz-score" id="quizScore" style="display:none;"></div>`;
        document.getElementById('quizContent').innerHTML = html;
        document.querySelectorAll('.quiz-opt').forEach(opt => {
          opt.addEventListener('click', function() {
            if (this.classList.contains('correct') || this.classList.contains('wrong')) return;
            const qIdx = this.dataset.qidx;
            const isCorrect = this.dataset.correct === 'true';
            document.querySelectorAll(`[data-qidx="${qIdx}"]`).forEach(o => {
              o.style.pointerEvents = 'none';
              if (o.dataset.correct === 'true') o.classList.add('correct');
              else if (o === this) o.classList.add('wrong');
            });
            setTimeout(() => {
              const total = quiz.length;
              const correct = document.querySelectorAll('.quiz-opt.correct').length;
              const answered = document.querySelectorAll('.quiz-q').length;
              const allAnswered = document.querySelectorAll('.quiz-opt.correct, .quiz-opt.wrong').length >= answered;
              if (allAnswered) {
                const percentage = Math.round(correct/total*100);
                document.getElementById('quizScore').style.display = 'block';
                document.getElementById('quizScore').textContent = `Score: ${correct}/${total} - ${percentage}%`;
                const earnedPoints = correct * 10;
                addPoints(earnedPoints, `+${earnedPoints} pts for ${correct}/${total} correct!`);
                if (percentage === 100) addPoints(20, '🎉 Perfect Score Bonus +20 pts!');
                else if (percentage >= 75) addPoints(10, '⭐ Great Job Bonus +10 pts!');
              }
            }, 500);
          });
        });
      } else { setCard('quizCard', false); }
    }

    btn.addEventListener('click', (e) => { e.preventDefault(); curate(); });
    topicEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); curate(); } });
  </script>
</body>
</html>
"""
def Neurosync_main(mode='run', topic=None): 
    fallback_leetcode = {
        'binary search': [
            {'id': '704', 'title': 'Binary Search', 'difficulty': 'Easy', 'url': 'https://leetcode.com/problems/binary-search/'},
            {'id': '35', 'title': 'Search Insert Position', 'difficulty': 'Easy', 'url': 'https://leetcode.com/problems/search-insert-position/'},
            {'id': '33', 'title': 'Search in Rotated Sorted Array', 'difficulty': 'Medium', 'url': 'https://leetcode.com/problems/search-in-rotated-sorted-array/'}
        ], }
    default_leetcode = [
        {'id': '1', 'title': 'Two Sum', 'difficulty': 'Easy', 'url': 'https://leetcode.com/problems/two-sum/'},
        {'id': '15', 'title': 'Three Sum', 'difficulty': 'Medium', 'url': 'https://leetcode.com/problems/3sum/'},
        {'id': '20', 'title': 'Valid Parentheses', 'difficulty': 'Easy', 'url': 'https://leetcode.com/problems/valid-parentheses/'}]  
    if mode == 'render':
        return render_template_string(HTML_TEMPLATE)
    # ===== MODE: CURATE RESOURCES =====
    if mode == 'curate' and topic:
        result = {'topic': topic, 'youtube': None, 'gfg': None, 'github': None, 'leetcode': None, 'ai_summary': None}
        # ===== SCRAPE YOUTUBE =====
        try:
            yt_url = f"https://www.youtube.com/results?search_query={quote(topic+" programming tutorial")}"
            yt_resp = requests.get(yt_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
            if yt_resp.status_code == 200:
                pattern = r'"videoRenderer":\{"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]+)"\}\].*?"viewCountText":\{"simpleText":"([^"]+)"\}'
                matches = re.findall(pattern, yt_resp.text)
                if matches:
                    videos = []
                    for vid_id, title, views in matches[:5]:
                        view_text = views.lower().replace(',', '').strip()
                        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
                        match_num = re.search(r'([\d.]+)\s*([kmb])?', view_text)
                        view_count = 0
                        if match_num:
                            num, mult = match_num.groups()
                            view_count = int(float(num) * multipliers.get(mult, 1))
                        title_lower = title.lower()
                        topic_words = topic.lower().split()
                        keyword_score = sum(50 for word in topic_words if word in title_lower)
                        score = view_count + keyword_score
                        videos.append({'title': title, 'url': f"https://www.youtube.com/watch?v={vid_id}", 'views': view_count, 'score': score})
                    if videos:
                        result['youtube'] = max(videos, key=lambda x: x['score'])
        except Exception as e:
            print(f"⚠️  YouTube error: {e}")
        # ===== SCRAPE GEEKSFORGEEKS =====
        try:
            gfg_direct = f"https://www.geeksforgeeks.org/{quote(topic.replace(' ', '-').lower())}/"
            gfg_resp = requests.get(gfg_direct, headers=HEADERS, timeout=TIMEOUT_SHORT)
            if gfg_resp.status_code == 200:
                soup = BeautifulSoup(gfg_resp.content, 'html.parser')
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    title_lower = title_text.lower()
                    topic_words = topic.lower().split()
                    keyword_score = sum(50 for word in topic_words if word in title_lower)
                    result['gfg'] = {'title': title_text, 'url': gfg_direct, 'score': 1000 + keyword_score}
            if not result['gfg']:
                gfg_search = f"https://www.geeksforgeeks.org/?s={quote(topic)}"
                gfg_resp = requests.get(gfg_search, headers=HEADERS, timeout=TIMEOUT_SHORT)
                if gfg_resp.status_code == 200:
                    soup = BeautifulSoup(gfg_resp.content, 'html.parser')
                    articles = []
                    for article in soup.find_all('div', class_='head', limit=5):
                        link_tag = article.find('a')
                        if link_tag:
                            title = link_tag.get_text(strip=True)
                            url = link_tag.get('href')
                            title_lower = title.lower()
                            topic_words = topic.lower().split()
                            keyword_score = sum(50 for word in topic_words if word in title_lower)
                            score = 500 + keyword_score
                            articles.append({'title': title, 'url': url, 'score': score})
                    if articles:
                        result['gfg'] = max(articles, key=lambda x: x['score'])
        except Exception as e:
            print(f"⚠️  GeeksforGeeks error: {e}")     
        # ===== SCRAPE GITHUB =====
        try:
            gh_url = f"https://github.com/search?q={quote(topic)}&type=repositories"
            gh_resp = requests.get(gh_url, headers=HEADERS, timeout=TIMEOUT_SHORT)
            if gh_resp.status_code == 200:
                soup = BeautifulSoup(gh_resp.content, 'html.parser')
                repo_containers = (soup.find_all('div', class_='Box-sc-g0xbh4-0', limit=5) or 
                                 soup.find_all('div', attrs={'data-testid': 'results-list'}) or 
                                 soup.find_all('div', class_='repo-list-item', limit=5))
                repos = []
                for repo in repo_containers:
                    link_tag = (repo.find('a', class_='Link__StyledLink-sc-14289xe-0') or 
                              repo.find('a', class_='v-align-middle') or 
                              repo.find('a', href=re.compile(r'^/[^/]+/[^/]+$')))
                    if not link_tag:
                        continue
                    title = link_tag.get_text(strip=True)
                    url = urljoin('https://github.com', link_tag.get('href'))
                    star_tag = repo.find('span', string=re.compile(r'\d'))
                    star_text = star_tag.get_text() if star_tag else '0'
                    star_text = star_text.lower().replace(',', '').strip()
                    stars = 0
                    if 'k' in star_text:
                        stars = int(float(star_text.replace('k', '')) * 1000)
                    else:
                        stars = int(re.sub(r'[^\d]', '', star_text)) if re.search(r'\d', star_text) else 0
                    title_lower = title.lower()
                    topic_words = topic.lower().split()
                    keyword_score = sum(50 for word in topic_words if word in title_lower)
                    score = stars + keyword_score
                    repos.append({'title': title, 'url': url, 'stars': stars, 'score': score})
                if repos:
                    result['github'] = max(repos, key=lambda x: x['score'])
        except Exception as e:
            print(f"⚠️  GitHub error: {e}")   
        # ===== SCRAPE LEETCODE =====
        try:
            graphql_url = "https://leetcode.com/graphql"
            query = """
            query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
              problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
              ) {
                questions: data {
                  questionFrontendId
                  title
                  titleSlug
                  difficulty
                  topicTags {
                    name
                  }
                }
              }
            }
            """
            variables = {"categorySlug": "", "limit": 10, "skip": 0, "filters": {"searchKeywords": topic}}
            payload = {"query": query, "variables": variables}
            graphql_headers = {**HEADERS, 'Content-Type': 'application/json', 'Referer': 'https://leetcode.com/problemset/', 'Origin': 'https://leetcode.com'}
            lc_resp = requests.post(graphql_url, json=payload, headers=graphql_headers, timeout=TIMEOUT_LONG)
            if lc_resp.status_code == 200:
                data = lc_resp.json()
                questions = data.get('data', {}).get('problemsetQuestionList', {}).get('questions', [])
                if questions:
                    problems = []
                    for q in questions[:3]:
                        problems.append({
                            'id': q.get('questionFrontendId', ''),
                            'title': q.get('title', 'LeetCode Problem'),
                            'difficulty': q.get('difficulty', 'Unknown'),
                            'url': f"https://leetcode.com/problems/{q.get('titleSlug', '')}/"
                        })
                    result['leetcode'] = problems
            if not result['leetcode']:
                topic_lower = topic.lower()
                for key, probs in fallback_leetcode.items():
                    if key in topic_lower:
                        result['leetcode'] = probs[:3]
                        break
                if not result['leetcode']:
                    result['leetcode'] = default_leetcode
        except Exception as e:
            print(f"⚠️  LeetCode error: {e}, using fallback")
            topic_lower = topic.lower()
            for key, probs in fallback_leetcode.items():
                if key in topic_lower:
                    result['leetcode'] = probs[:3]
                    break
            if not result['leetcode']:
                result['leetcode'] = default_leetcode
        # ===== GET AI SUMMARY =====
        try:
            if not GEMINI_API_KEY:
                result['ai_summary'] = {
                    'summary': f"{topic} is an important concept in computer science and programming.",
                    'difficulty': 'intermediate',
                    'prerequisites': ['Basic programming knowledge', 'Problem-solving skills']
                }
            else:
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
                prompt = (
                    f"Teach {topic} from basics to advanced.\n\n"
                    "Return JSON (no markdown):\n"
                    "{\n"
                    f"  \"summary\": \"2-3 sentence overview of {topic}\",\n"
                    "  \"difficulty\": \"beginner|intermediate|advanced\",\n"
                    "  \"prerequisites\": [\"prerequisite 1\", \"prerequisite 2\"],\n"
                    "  \"roadmap\": {\n"
                    "    \"beginner\": [\"step 1\", \"step 2\"],\n"
                    "    \"intermediate\": [\"step 1\", \"step 2\"],\n"
                    "    \"advanced\": [\"step 1\", \"step 2\"]\n"
                    "  },\n"
                    "  \"quiz\": [\n"
                    "    {\"question\": \"question text\", \"options\": [\"opt1\", \"opt2\", \"opt3\", \"opt4\"], \"correct\": 0}\n"
                    "  ]\n"
                    "}\n"
                    "Create 3-4 quiz questions. Assess difficulty for beginners. Keep concise."
                )
                ai_payload = {"contents": [{"parts": [{"text": prompt}]}]}
                ai_resp = requests.post(api_url, json=ai_payload, timeout=TIMEOUT_LONG)
                if ai_resp.status_code == 200:
                    data = ai_resp.json()
                    text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    if text.startswith('```json'):
                        text = text[7:]
                    if text.startswith('```'):
                        text = text[3:]
                    if text.endswith('```'):
                        text = text[:-3]
                    text = text.strip()
                    import json as _json
                    result['ai_summary'] = _json.loads(text)
                else:
                    result['ai_summary'] = {
                        'summary': f"{topic} is a fundamental concept in computer science that helps solve various programming problems efficiently.",
                        'difficulty': 'intermediate',
                        'prerequisites': ['Basic programming knowledge', 'Understanding of data structures', 'Problem-solving skills']
                    }
        except Exception as e:
            print(f"⚠️  Gemini AI error: {e}")
            result['ai_summary'] = {
                'summary': f"{topic} is a fundamental concept in computer science that helps solve various programming problems efficiently.",
                'difficulty': 'intermediate',
                'prerequisites': ['Basic programming knowledge', 'Understanding of data structures', 'Problem-solving skills']
            }
        return result
# # ===================== Main Entry Point =====================
if __name__ == '__main__':
    Neurosync_main('run')