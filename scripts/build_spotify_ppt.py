"""Build guizang Style A (ink-classic) deck from Spotify story materials."""
import shutil
from pathlib import Path

GUIZANG = Path.home() / ".agents" / "skills" / "guizang-ppt-skill"
OUT = Path(__file__).resolve().parents[1] / "ppt"
TOTAL = 11

SLIDES = """
<section class="slide hero dark">
  <div class="chrome"><div>Spotify Story · 数据可视化</div><div>01 / {total}</div></div>
  <div class="frame" style="display:grid;gap:4vh;align-content:center;min-height:80vh">
    <div class="kicker" data-anim>Top 10,000 Songs · 2025</div>
    <h1 class="h-hero" data-anim>解码流行 <em>bolder.</em></h1>
    <h2 class="h-sub" data-anim>从流派王权到情绪象限</h2>
    <p class="lead" style="max-width:62vw" data-anim>基于 Spotify 全球热门歌曲，用数据讲述王权交替、黄金公式与文化反叛。</p>
    <div class="meta-row" data-anim><span>2024080126 黄之颖</span><span>·</span><span>深圳大学 · 数据可视化期末</span></div>
  </div>
  <div class="foot"><div>一场关于流行音乐的数据叙事</div><div>2026</div></div>
</section>

<section class="slide light">
  <div class="chrome"><div>Act I · 宏观流派</div><div>02 / {total}</div></div>
  <div class="col" style="padding-top:4vh">
    <div class="kicker" data-anim>第一章</div>
    <h2 class="h-xl" data-anim>王权交替</h2>
    <p class="lead" data-anim>2024 年市场占有率：Pop 与 Rock 分居冠亚军，但历史曲线曾发生一次「王权交替」。</p>
    <div class="grid-6" style="margin-top:4vh">
      <div class="stat-card" data-anim><div class="stat-label">Pop</div><div class="stat-nb">4,469</div><div class="stat-note">市场占有率第一</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Rock</div><div class="stat-nb">2,417</div><div class="stat-note">稳居第二</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Dataset</div><div class="stat-nb">10K</div><div class="stat-note">Spotify 热门曲目</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Year</div><div class="stat-nb">2024</div><div class="stat-note">分析基准年</div></div>
    </div>
  </div>
  <div class="foot"><div>各音乐流派市场占有率</div><div>Genre Market</div></div>
</section>

<section class="slide dark">
  <div class="chrome"><div>趋势 · Timeline</div><div>03 / {total}</div></div>
  <div class="frame grid-2-7-5" style="padding-top:6vh">
    <div class="col">
      <div class="kicker" data-anim>第二章</div>
      <h2 class="h-xl" data-anim>Pop 反超 Rock</h2>
      <p class="lead" data-anim>2000 年代初 Rock 仍占上风；约 2005 年 Pop 热度曲线拔地而起，正式完成反超。</p>
      <div class="callout" data-anim>2024 年 Pop 热度合计达 <strong>59,015</strong>，流媒体与疫情共同推高全流派指数级增长。<div class="callout-src">— 各音乐流派的受欢迎程度变化趋势</div></div>
    </div>
    <figure class="frame-img r-16x10" data-anim style="background:rgba(255,255,255,.06);display:grid;place-items:center;padding:2vh">
      <svg viewBox="0 0 640 360" width="100%" aria-label="Pop vs Rock trend">
        <text x="24" y="28" fill="#f1efea" font-size="14" opacity=".7">Popularity SUM by Year</text>
        <line x1="40" y1="300" x2="600" y2="300" stroke="#666" stroke-width="1"/>
        <line x1="40" y1="40" x2="40" y2="300" stroke="#666" stroke-width="1"/>
        <polyline fill="none" stroke="#499894" stroke-width="3" points="60,260 120,240 180,200 240,170 300,120 360,90 420,70 480,55 540,45 580,40"/>
        <polyline fill="none" stroke="#ff9d9a" stroke-width="3" points="60,180 120,175 180,170 240,165 300,160 360,155 420,150 480,145 540,140 580,135"/>
        <line x1="280" y1="40" x2="280" y2="300" stroke="#f1efea" stroke-dasharray="4 4" opacity=".5"/>
        <text x="272" y="320" fill="#f1efea" font-size="11" opacity=".6">2004</text>
        <text x="500" y="55" fill="#499894" font-size="12">Pop</text>
        <text x="500" y="130" fill="#ff9d9a" font-size="12">Rock</text>
      </svg>
      <figcaption class="img-cap">流行乐反超摇滚 · 标注 2004</figcaption>
    </figure>
  </div>
  <div class="foot"><div>流派受欢迎程度变化趋势</div><div>— · —</div></div>
</section>

<section class="slide light">
  <div class="chrome"><div>艺人 · Artists</div><div>04 / {total}</div></div>
  <div class="col" style="padding-top:4vh">
    <div class="kicker" data-anim>第三章</div>
    <h2 class="h-xl" data-anim>顶流镜像</h2>
    <p class="lead" data-anim>顶流艺人的热度轨迹，是流派繁荣的完美镜像。</p>
    <div class="pipeline" style="margin-top:5vh">
      <div class="step" data-anim><div class="step-nb">01</div><div class="step-title">Taylor Swift</div><div class="step-desc">Pop 代言人 · 粉丝量 16,074M+</div></div>
      <div class="step" data-anim><div class="step-nb">02</div><div class="step-title">Bad Bunny</div><div class="step-desc">Latin 全球逆袭 · 5,282M 粉丝</div></div>
      <div class="step" data-anim><div class="step-nb">03</div><div class="step-title">Drake · Carti</div><div class="step-desc">伫立 HipHop 山巅的双峰</div></div>
    </div>
  </div>
  <div class="foot"><div>粉丝量与艺人热度</div><div>Artist Scatter</div></div>
</section>

<section class="slide dark">
  <div class="chrome"><div>音频 · Metrics</div><div>05 / {total}</div></div>
  <div class="col" style="padding-top:4vh">
    <div class="kicker" data-anim>第四章</div>
    <h2 class="h-xl" data-anim>Top 100 黄金公式</h2>
    <p class="lead" data-anim>红遍全球的热歌，在四个音频维度上高度相似：</p>
    <div class="grid-4" style="margin-top:4vh">
      <div class="stat-card" data-anim><div class="stat-label">Tempo</div><div class="stat-nb">120</div><div class="stat-note">中速流行 / 快板</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Energy</div><div class="stat-nb">0.62</div><div class="stat-note">中高能量</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Dance</div><div class="stat-nb">0.63</div><div class="stat-note">强律动</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Loudness</div><div class="stat-nb">-7.4</div><div class="stat-note">dB · 高响度</div></div>
    </div>
  </div>
  <div class="foot"><div>Top100 黄金配比</div><div>Golden Ratio</div></div>
</section>

<section class="slide light">
  <div class="chrome"><div>异类 · Outlier</div><div>06 / {total}</div></div>
  <div class="frame grid-2-7-5" style="padding-top:6vh">
    <div class="col">
      <div class="kicker" data-anim>第五章</div>
      <h2 class="h-xl" data-anim>异类碧梨</h2>
      <p class="lead" data-anim>在 Top 10 歌手的流行大潮中，Billie Eilish 是能量最低、情绪最暗的异类。</p>
      <p class="body-zh" data-anim>2016 年首支单曲杀入战场后粉丝量爆发式增长，但音频指纹与「黄金公式」背道而驰。</p>
    </div>
    <div class="callout" data-anim style="align-self:center">平均 Energy <strong>0.33</strong><br>远低于 Top100 的 0.61+<div class="callout-src">— Top10 歌手黄金配比</div></div>
  </div>
  <div class="foot"><div>Billie Eilish · 低能量异类</div><div>— · —</div></div>
</section>

<section class="slide dark">
  <div class="chrome"><div>风格 · Styles</div><div>07 / {total}</div></div>
  <div class="col" style="padding-top:3vh">
    <div class="kicker" data-anim>第六章</div>
    <h2 class="h-xl" data-anim>五种风格歌手</h2>
    <div class="grid-3" style="margin-top:4vh">
      <div class="stat-card" data-anim><div class="stat-label">Billie</div><div class="stat-note">暗黑电子流行</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Linkin Park</div><div class="stat-note">新金属</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Mrs. GREEN APPLE</div><div class="stat-note">日式流行摇滚</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Taylor Swift</div><div class="stat-note">乡村流行</div></div>
      <div class="stat-card" data-anim><div class="stat-label">The Weeknd</div><div class="stat-note">复古 R&amp;B</div></div>
    </div>
    <p class="body-zh" style="margin-top:3vh" data-anim>模仿各风格代表歌手的高分曲目音频特征，是在该领域深耕的捷径。</p>
  </div>
  <div class="foot"><div>五种不同风格歌手的作品分布</div><div>Style Matrix</div></div>
</section>

<section class="slide light">
  <div class="chrome"><div>情绪 · Mood</div><div>08 / {total}</div></div>
  <div class="frame grid-2-6-6" style="padding-top:5vh">
    <div class="col">
      <div class="kicker" data-anim>第七章</div>
      <h2 class="h-xl" data-anim>情绪象限</h2>
      <p class="lead" data-anim>Billie 的歌落在低 Energy、低 Valence 区域——低能量 + 负面情绪。</p>
      <p class="body-zh" data-anim>对应 2016 年前后年轻人中的「丧文化」：疲惫、焦虑、反对过度积极。</p>
    </div>
    <figure class="frame-img r-1x1" data-anim style="background:#e8e5de;display:grid;place-items:center">
      <svg viewBox="0 0 300 300" width="90%">
        <rect x="30" y="30" width="240" height="240" fill="#f1efea" stroke="#ccc"/>
        <line x1="150" y1="30" x2="150" y2="270" stroke="#e15759" stroke-dasharray="5 4"/>
        <line x1="30" y1="150" x2="270" y2="150" stroke="#e15759" stroke-dasharray="5 4"/>
        <circle cx="190" cy="95" r="6" fill="#f28e2b" opacity=".75"/>
        <circle cx="85" cy="195" r="6" fill="#4e79a7" opacity=".75"/>
        <text x="200" y="88" font-size="10" fill="#333">Taylor</text>
        <text x="55" y="210" font-size="10" fill="#333">Billie</text>
        <text x="248" y="155" font-size="9" fill="#666">Energy→</text>
        <text x="38" y="42" font-size="9" fill="#666">Valence</text>
      </svg>
    </figure>
  </div>
  <div class="foot"><div>Energy × Valence</div><div>Emotion Quadrant</div></div>
</section>

<section class="slide dark">
  <div class="chrome"><div>文化 · Culture</div><div>09 / {total}</div></div>
  <div class="col" style="padding-top:4vh">
    <div class="kicker" data-anim>第八章</div>
    <h2 class="h-xl" data-anim>文化反叛</h2>
    <p class="lead" data-anim>Explicit 标签歌曲在 2018–2024 年疯狂上升，映射全球年轻人的审美新趋势。</p>
    <div class="grid-3" style="margin-top:4vh">
      <div class="stat-card" data-anim><div class="stat-label">HipHop</div><div class="stat-nb">261</div><div class="stat-note">2024 Explicit 合计</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Latin</div><div class="stat-nb">162</div><div class="stat-note">紧随其后</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Pop</div><div class="stat-nb">129</div><div class="stat-note">主流亦参与</div></div>
    </div>
  </div>
  <div class="foot"><div>文化叛逆变化趋势</div><div>Explicit Trend</div></div>
</section>

<section class="slide light">
  <div class="chrome"><div>悖论 · Paradox</div><div>10 / {total}</div></div>
  <div class="col" style="padding-top:4vh">
    <div class="kicker" data-anim>第九章</div>
    <h2 class="h-xl" data-anim>叛逆悖论</h2>
    <p class="lead" data-anim>刻板印象里最狂躁的 Rock，Explicit 占比仅 <strong>13.57%</strong>。</p>
    <div class="grid-3" style="margin-top:4vh">
      <div class="stat-card" data-anim><div class="stat-label">R&amp;B</div><div class="stat-nb">41.5%</div><div class="stat-note">最高占比</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Metal</div><div class="stat-nb">35.2%</div><div class="stat-note">极端表达</div></div>
      <div class="stat-card" data-anim><div class="stat-label">Latin</div><div class="stat-nb">28.3%</div><div class="stat-note">身体与欲望</div></div>
    </div>
  </div>
  <div class="foot"><div>不同流派 Explicit 占比</div><div>Explicit Ratio</div></div>
</section>

<section class="slide hero light">
  <div class="chrome"><div>Closing · 结语</div><div>11 / {total}</div></div>
  <div class="frame" style="display:grid;gap:4vh;align-content:center;min-height:75vh;text-align:center">
    <div class="kicker" data-anim style="justify-self:center">Takeaway</div>
    <h2 class="h-xl" data-anim>音乐没有标准答案，<br><em>但有数据可循。</em></h2>
    <p class="lead" style="max-width:58vw;justify-self:center" data-anim>从王权交替到情绪象限，从黄金公式到文化反叛——数据帮我们读懂 Spotify 热门歌曲背后的故事。</p>
    <div class="meta-row" data-anim style="justify-content:center"><span>谢谢</span><span>·</span><span>Q&amp;A</span></div>
  </div>
  <div class="foot"><div>解码流行 bolder.</div><div>2026</div></div>
</section>
""".strip().format(total=TOTAL)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(exist_ok=True)
    shutil.copy2(GUIZANG / "assets" / "motion.min.js", OUT / "motion.min.js")
    template = (GUIZANG / "assets" / "template.html").read_text(encoding="utf-8")
    template = template.replace(
        "<title>[必填] 替换为 PPT 标题 · Deck Title</title>",
        "<title>解码流行 bolder. · Spotify Story</title>",
    )
    template = template.replace("<!-- SLIDES_HERE -->", SLIDES)
    (OUT / "index.html").write_text(template, encoding="utf-8")
    print(f"Wrote {OUT / 'index.html'} ({TOTAL} slides)")


if __name__ == "__main__":
    main()
