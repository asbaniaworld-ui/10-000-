"""Build meteor-shower dark variant of the deck (separate preview copy)."""
import re
import shutil
from pathlib import Path

from build_deck import (
    CHAPTER_THEMES,
    DECK_PATCH,
    GENRE_SHOWCASE,
    MUSIC_BAR,
    STORY,
    STORY_DRAWER,
    TITLE,
    SUBTITLE,
    TOTAL,
    chapter_slide,
    esc,
)

ROOT = Path(__file__).resolve().parents[1]
GUIZANG = Path.home() / ".agents" / "skills" / "guizang-ppt-skill"
SRC_DECK = ROOT / "deck"
DECK = ROOT / "deck-meteor"

THEME_ROOT = """
    --ink:#030508;
    --ink-rgb:3,5,8;
    --paper:#e4eaf6;
    --paper-rgb:228,234,246;
    --paper-tint:#9aa8c8;
    --ink-tint:#0c1224;
    --meteor-accent:#7eb8ff;
    --meteor-violet:#9d7cff;
"""

METEOR_CSS = """
  body.meteor-deck{background:#030508}
  body.meteor-deck.low-power{background:#030508!important}
  body.meteor-deck.low-power canvas.bg{display:block!important}
  body.meteor-deck.low-power canvas#bg-light{display:none!important}
  body.meteor-deck.low-power canvas#meteor-layer{display:none!important}
  canvas#meteor-layer{z-index:1;pointer-events:none;opacity:.92}
  body.meteor-deck canvas#bg-light{opacity:0!important}
  body.meteor-deck canvas#bg-dark{opacity:1!important}
  body.meteor-deck.light-bg canvas#bg-light{opacity:0!important}
  .slide.light,.slide.dark{color:var(--paper);background:transparent}
  .slide::before{background:rgba(3,5,8,.52)!important;backdrop-filter:blur(6px)}
  .slide.hero::before{background:rgba(3,5,8,.28)!important;backdrop-filter:blur(2px)}
  .slide.hero::after{background:linear-gradient(180deg,rgba(3,5,8,.55) 0%,rgba(3,5,8,0) 16%,rgba(3,5,8,0) 84%,rgba(3,5,8,.55) 100%)!important}
  .display-zh,.h1-zh{text-shadow:0 0 40px rgba(126,184,255,.22),0 0 80px rgba(157,124,255,.12)}
  .kicker{color:var(--meteor-accent);opacity:.75}
  .deck-layout-4060{display:grid;grid-template-columns:40fr 60fr;gap:3vw;flex:1;align-items:stretch}
  .deck-split{align-items:stretch;padding-top:1.5vh;flex:1;min-height:0}
  .deck-text{gap:1.1vh;max-height:76vh;overflow:auto;padding-right:.6vw;justify-content:flex-start}
  .deck-text::-webkit-scrollbar{width:3px}
  .deck-text::-webkit-scrollbar-thumb{background:rgba(126,184,255,.25);border-radius:2px}
  .split-slide .h1-zh{font-size:2.6vw;line-height:1.15;margin-bottom:.2vh}
  .deck-lead{font-size:max(13px,.95vw)!important;line-height:1.55!important;opacity:.84;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical;overflow:hidden}
  .deck-detail{font-size:max(12px,.88vw)!important;line-height:1.5!important;opacity:.72;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
  .deck-bullets{margin:.2vh 0 0 1em;line-height:1.45;font-size:max(12px,.88vw)!important;opacity:.82}
  .deck-bullets li{margin:.25em 0}
  .chart-panel{background:rgba(8,14,32,.78);color:#dce6f8;border:1px solid rgba(126,184,255,.2);border-radius:10px;padding:8px 10px 6px;min-height:68vh;height:100%;display:flex;flex-direction:column;box-shadow:0 0 48px rgba(126,184,255,.1),inset 0 1px 0 rgba(255,255,255,.06);backdrop-filter:blur(12px)}
  .chart-panel-head{color:rgba(220,230,255,.55)}
  .deck-chart{flex:1;min-height:62vh;width:100%}
  .deck-chart.wide{min-height:64vh}
  .deck-chart.matrix{min-height:66vh}
  .deck-chart.facet{min-height:66vh}
  #story-drawer{background:rgba(6,10,24,.94);color:var(--paper);border:1px solid rgba(126,184,255,.18);box-shadow:8px 0 48px rgba(0,0,0,.45),0 0 30px rgba(126,184,255,.08)}
  #genre-showcase{background:rgba(6,10,24,.94);color:var(--paper);border:1px solid rgba(126,184,255,.18);box-shadow:8px 0 48px rgba(0,0,0,.45),0 0 24px rgba(157,124,255,.1)}
  #genre-showcase .gs-track{color:var(--meteor-accent)}
  #genre-showcase .gs-pl-item{border-color:rgba(126,184,255,.15)}
  #genre-showcase .gs-pl-item:hover,#genre-showcase .gs-pl-item.is-active{background:rgba(126,184,255,.12);border-color:rgba(126,184,255,.45)}
  #genre-showcase .gs-pl-item.is-active .gs-pl-play,#genre-showcase .gs-pl-item:hover .gs-pl-play{color:var(--meteor-accent)}
  #genre-showcase .gs-story{border-top-color:rgba(126,184,255,.12)}
  #music-bar{background:rgba(6,10,24,.92);border:1px solid rgba(126,184,255,.2);box-shadow:0 12px 40px rgba(0,0,0,.4),0 0 24px rgba(126,184,255,.12)}
  #nav{background:rgba(6,10,24,.45);border:1px solid rgba(126,184,255,.15);box-shadow:0 0 24px rgba(126,184,255,.08)}
  #nav .dot{background:rgba(126,184,255,.25)}
  #nav .dot:hover{background:rgba(126,184,255,.55)}
  #nav .dot.active{background:linear-gradient(90deg,var(--meteor-accent),var(--meteor-violet));box-shadow:0 0 12px rgba(126,184,255,.5)}
  #hint{color:rgba(180,200,255,.45);mix-blend-mode:normal}
  .ch1-genre .deck-lead{-webkit-line-clamp:3}
  .ch1-genre .deck-text{display:grid;grid-template-rows:auto auto auto 1fr;min-height:0}
  #genre-showcase{position:fixed;left:0;bottom:10vh;top:auto;z-index:185;width:min(300px,32vw);max-height:58vh;overflow:auto;overflow-x:hidden;transform:translateX(-108%);transition:transform .5s cubic-bezier(.22,1,.36,1),opacity .4s;opacity:0;pointer-events:none}
  #genre-showcase.is-visible{transform:translateX(0);opacity:1;pointer-events:auto}
  #genre-showcase .gs-close{position:absolute;top:.6vh;right:.5vw;z-index:2;background:rgba(126,184,255,.2);border:none;color:#fff;font-size:18px;line-height:1;width:28px;height:28px;border-radius:50%;cursor:pointer;opacity:.85}
  #genre-showcase .gs-img-wrap{height:22vh;min-height:130px;background:#0a1020 center/cover no-repeat}
  #genre-showcase .gs-cap{padding:1.4vh 1.1vw 1.6vh}
  #genre-showcase .gs-name{font-family:var(--serif-zh);font-size:max(18px,1.25vw);font-weight:600;line-height:1.2}
  #genre-showcase .gs-stats{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-top:.5vh}
  #genre-showcase .gs-blurb{font-size:max(12px,.85vw);line-height:1.5;opacity:.78;margin-top:.7vh}
  #genre-showcase .gs-story{font-size:max(11px,.82vw);line-height:1.5;opacity:.72;margin-top:.8vh;padding-top:.8vh}
  #genre-showcase .gs-story-head{display:block;font-family:var(--mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;opacity:.5;margin-bottom:.35vh}
  #genre-showcase.gs-mode-playlist{width:min(320px,34vw);max-height:62vh}
  #genre-showcase .gs-playlist{display:none;margin-top:.6vh;max-height:42vh;overflow-y:auto;padding-right:.3vw}
  #genre-showcase.gs-mode-playlist .gs-playlist{display:block}
  #genre-showcase .gs-pl-item{display:block;width:100%;text-align:left;padding:.65vh .55vw;margin-bottom:.4vh;background:transparent;color:inherit;cursor:pointer;border-radius:4px;transition:background .2s,border-color .2s}
  #genre-showcase .gs-pl-main{display:flex;align-items:center;justify-content:space-between;gap:.5vw}
  #genre-showcase .gs-pl-genre{font-family:var(--serif-zh);font-size:max(13px,.92vw);font-weight:600;line-height:1.25}
  #genre-showcase .gs-pl-play{font-size:11px;opacity:.45;flex-shrink:0}
  #genre-showcase .gs-pl-meta{display:block;font-size:max(10px,.78vw);opacity:.55;margin-top:.25vh;line-height:1.35}
  #genre-showcase .gs-pl-count{display:block;font-family:var(--mono);font-size:8px;letter-spacing:.08em;opacity:.4;margin-top:.15vh}
  #story-drawer{position:fixed;left:0;top:50%;z-index:180;width:min(340px,36vw);max-height:72vh;overflow:auto;padding:2.2vh 1.4vw 2vh 1.6vw;border-left:none;border-radius:0 10px 10px 0;transform:translate(-108%,-50%);transition:transform .5s cubic-bezier(.22,1,.36,1);backdrop-filter:blur(14px);pointer-events:none;opacity:0}
  #story-drawer.is-on{transform:translate(0,-50%);pointer-events:auto;opacity:1}
  #story-drawer .sd-close{position:absolute;top:.8vh;right:.6vw;background:transparent;border:none;color:inherit;font-size:20px;line-height:1;cursor:pointer;opacity:.45;padding:4px 8px}
  #story-drawer .sp-title{font-family:var(--serif-zh);font-size:max(16px,1.1vw);font-weight:600;margin-bottom:.6vh;padding-right:1.4em}
  #story-drawer .sp-head{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-bottom:.4vh}
  #story-drawer p{font-size:max(12px,.88vw);line-height:1.55;margin:.35vh 0;opacity:.88}
  #story-drawer .sp-num{font-family:var(--mono);font-size:10px;opacity:.5;margin-top:.6vh}
  #music-bar{position:fixed;right:2.2vw;bottom:2.2vh;transform:translateY(120%);width:min(340px,42vw);z-index:200;padding:12px 14px;display:grid;grid-template-columns:1fr auto;gap:8px 10px;align-items:start;transition:transform .45s cubic-bezier(.22,1,.36,1);backdrop-filter:blur(12px);border-radius:8px}
  #music-bar.is-visible{transform:translateY(0)}
  .mp-track{font-family:var(--serif-zh);font-size:14px;line-height:1.25;grid-column:1}
  .mp-artist{font-family:var(--mono);font-size:9px;letter-spacing:.12em;opacity:.55;margin-top:2px;grid-column:1}
  .mp-mode{font-family:var(--mono);font-size:9px;letter-spacing:.1em;opacity:.4;grid-column:1;margin-top:2px}
  .mp-actions{display:flex;gap:6px;grid-column:2;grid-row:1/3}
  .mp-btn{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;background:transparent;border:1px solid rgba(126,184,255,.35);color:inherit;padding:4px 8px;cursor:pointer;border-radius:4px}
  #music-audio,#music-spotify{display:none}
  #music-spotify{width:100%;height:72px;border:none;border-radius:6px}
  #music-spotify:not(.hidden){display:block;grid-column:1/-1}
  #music-bar:has(#music-spotify:not(.hidden)){grid-template-rows:auto auto auto}
"""

FS_METEOR = r"""const FS_DARK = `precision highp float;
uniform vec2 u_resolution;uniform float u_time;uniform vec2 u_mouse;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float hash2(vec2 p){return fract(sin(dot(p,vec2(269.5,183.3)))*43758.5453);}
void main(){
  vec2 uv=gl_FragCoord.xy/u_resolution.xy;
  vec2 p=uv*2.0-1.0;p.x*=u_resolution.x/u_resolution.y;
  vec3 col=mix(vec3(0.01,0.015,0.04),vec3(0.04,0.03,0.10),uv.y*0.85+0.08);
  col+=vec3(0.06,0.03,0.12)*pow(1.0-uv.y,2.0)*0.35;
  vec2 starUV=uv*vec2(u_resolution.x/u_resolution.y,1.0)*220.0;
  vec2 cell=floor(starUV);
  float h=hash(cell);
  if(h>0.985){
    vec2 f=fract(starUV)-0.5;
    float d=length(f);
    float tw=0.55+0.45*sin(u_time*2.5+h*40.0);
    col+=vec3(0.85,0.92,1.0)*exp(-d*d*80.0)*tw*((h-0.985)/0.015);
  }
  float neb=sin(p.x*1.8+u_time*0.08)*sin(p.y*1.4-u_time*0.06);
  col+=vec3(0.12,0.08,0.22)*neb*0.04;
  vec2 m=u_mouse*2.0-1.0;m.x*=u_resolution.x/u_resolution.y;
  col+=vec3(0.15,0.25,0.55)*exp(-length(p-m)*2.2)*0.12;
  gl_FragColor=vec4(col,1.0);
}`;

const FS_LIGHT = `precision highp float;
uniform vec2 u_resolution;uniform float u_time;uniform vec2 u_mouse;
void main(){
  vec2 uv=gl_FragCoord.xy/u_resolution.xy;
  vec3 col=mix(vec3(0.02,0.03,0.07),vec3(0.05,0.04,0.11),uv.y);
  gl_FragColor=vec4(col,1.0);
}`;"""

METEOR_CANVAS = '<canvas id="meteor-layer" class="bg"></canvas>\n'

METEOR_PATCH = """
<script src="js/meteor-bg.js?v=1"></script>
"""

METEOR_DECK_PATCH = DECK_PATCH.replace(
    "<script>window.__WEB_DATA_BASE",
    METEOR_PATCH + "<script>window.__WEB_DATA_BASE",
)


def build_slides_meteor() -> str:
    parts = [
        f"""
<section class="slide hero dark" data-slide="0" data-theme="dark">
  <div class="chrome"><div>Meteor Edition · 情绪脉动</div><div>01 / {TOTAL}</div></div>
  <div class="frame" style="display:grid;gap:3.2vh;align-content:center;min-height:78vh">
    <div class="kicker" data-anim>Data Visualization · Final Project</div>
    <h1 class="display-zh" data-anim>{esc(TITLE)}</h1>
    <h2 class="h2-zh" data-anim style="opacity:.88">{esc(SUBTITLE)}</h2>
    <p class="lead" style="max-width:64vw" data-anim>
      基于 Spotify 全球 Top 10,000 热门歌曲数据集，以 Tableau 工作簿为视觉基准，
      复刻 9 组交互图表，讲述从<strong>流派王权交替</strong>到<strong>情绪象限</strong>、
      从<strong>黄金公式</strong>到<strong>文化反叛</strong>的完整数据叙事。
    </p>
    <div class="meta-row" data-anim style="font-family:var(--mono);font-size:12px;letter-spacing:.14em;opacity:.65;display:flex;gap:1.2em;margin-top:1vh">
      <span>2024080126 黄之颖</span><span>·</span><span>深圳大学</span><span>·</span><span>数据可视化 2026</span>
    </div>
  </div>
  <div class="foot"><div>悬停试听 · ← → 翻页 · B 切换动态</div><div>2026</div></div>
</section>"""
    ]
    for i, ch in enumerate(STORY):
        left, right = CHAPTER_THEMES[i]
        s = chapter_slide(ch, i, left, right, dark=True)
        s = s.replace('<section class="slide dark', '<section class="slide dark" data-theme="dark"')
        parts.append(s)

    parts.append(
        f"""
<section class="slide hero dark" data-slide="10" data-theme="dark">
  <div class="chrome"><div>Closing · 结语</div><div>{TOTAL:02d} / {TOTAL}</div></div>
  <div class="frame" style="display:grid;gap:3.5vh;align-content:center;min-height:72vh;text-align:center">
    <div class="kicker" data-anim style="justify-self:center">Takeaway</div>
    <h2 class="h1-zh" data-anim>音乐没有标准答案，<br><em>但有数据可循。</em></h2>
    <p class="body-zh" style="max-width:58vw;justify-self:center;opacity:.85" data-anim>
      从王权交替到情绪象限，从黄金公式到文化反叛——10,000 次心跳的采样，
      让我们听见全球数字音乐的情绪脉动。
    </p>
    <div class="meta-row" data-anim style="justify-content:center;font-family:var(--mono);font-size:12px;letter-spacing:.16em;opacity:.6">
      <span>谢谢</span><span>·</span><span>Q&amp;A</span>
    </div>
  </div>
  <div class="foot"><div>{esc(TITLE)}</div><div>Meteor Edition</div></div>
</section>"""
    )
    return "\n".join(parts)


def patch_theme(html: str) -> str:
    html = html.replace("<body>", '<body class="meteor-deck">', 1)
    html = re.sub(
        r"--ink:#0a0a0b;\s*--ink-rgb:10,10,11;\s*--paper:#f1efea;\s*--paper-rgb:241,239,234;\s*--paper-tint:#e8e5de;\s*--ink-tint:#18181a;",
        THEME_ROOT.strip(),
        html,
        count=1,
    )
    html = html.replace(
        f"<title>{TITLE} · {SUBTITLE}</title>",
        f"<title>{TITLE} · {SUBTITLE} · Meteor Edition</title>",
    )
    html = re.sub(
        r"const FS_DARK = `[\s\S]*?`;\s*\n\s*const FS_LIGHT = `[\s\S]*?`;",
        FS_METEOR,
        html,
        count=1,
    )
    html = html.replace(
        '<canvas id="bg-dark" class="bg"></canvas>',
        METEOR_CANVAS + '<canvas id="bg-dark" class="bg"></canvas>',
    )
    html = html.replace(
        "document.body.classList.toggle('light-bg',th==='light');",
        "document.body.classList.remove('light-bg');",
    )
    return html


def sync_assets():
    for sub in ("js", "images"):
        src = SRC_DECK / sub
        dst = DECK / sub
        if dst.exists():
            shutil.rmtree(dst)
        if src.exists():
            shutil.copytree(src, dst)
    meteor_src = ROOT / "deck-meteor" / "js" / "meteor-bg.js"
    if meteor_src.exists():
        shutil.copy2(meteor_src, DECK / "js" / "meteor-bg.js")
    for name in ("motion.min.js",):
        src = SRC_DECK / name
        if src.exists():
            shutil.copy2(src, DECK / name)
    assets = DECK / "assets"
    assets.mkdir(exist_ok=True)
    src_m = SRC_DECK / "assets" / "motion.min.js"
    if src_m.exists():
        shutil.copy2(src_m, assets / "motion.min.js")
    elif (SRC_DECK / "motion.min.js").exists():
        shutil.copy2(SRC_DECK / "motion.min.js", assets / "motion.min.js")


def main():
    DECK.mkdir(parents=True, exist_ok=True)
    sync_assets()

    template = (GUIZANG / "assets" / "template.html").read_text(encoding="utf-8")
    template = template.replace(
        "<title>[必填] 替换为 PPT 标题 · Deck Title</title>",
        f"<title>{TITLE} · {SUBTITLE} · Meteor Edition</title>",
    )
    template = template.replace("<!-- SLIDES_HERE -->", build_slides_meteor())
    template = template.replace("</style>", METEOR_CSS + "\n</style>", 1)
    template = template.replace(
        "</body>",
        STORY_DRAWER + GENRE_SHOWCASE + MUSIC_BAR + METEOR_DECK_PATCH + "\n</body>",
    )
    template = template.replace(
        "window.__currentSlideIndex = idx;",
        "window.__currentSlideIndex = idx;\n  if(window.__onDeckSlide) window.__onDeckSlide(idx);",
    )
    template = patch_theme(template)

    (DECK / "index.html").write_text(template, encoding="utf-8")
    print(f"Built {DECK / 'index.html'} — Meteor Edition ({TOTAL} slides)")


if __name__ == "__main__":
    main()
