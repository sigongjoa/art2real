# 판 보고서 → claude.ai Artifact 한 쪽(시안 비교용 · 모션 M1 도장 / M2 그리기 전환) · Artifact 규칙: 껍데기 태그 없음 · Google Fonts 만 · 밝음/어두움 토큰 · 안전 영역 여백 · 10-22
# 사용: python 하네스/아티팩트.py <판> → 하네스/판/<판>/아티팩트.html (그림은 publish 때 files 로)
import re, sys
뿌리 = "G:/art2real"
토큰 = """
/* 왼쪽 요약 고정 · 오른쪽 본문(시안 C) · 회백 종이 위에 뜻 색 하나씩(초록 통과 · 빨강 실패 · 금 도구 · 파랑 데이터) */
:root{--paper:#f6f4ef;--sheet:#fffdf8;--ink:#1d2129;--muted:#585e68;--rule:#dcd7cc;--soft:#ece8de;--pass:#1f7a3e;--pass-bg:#e3f1e6;--fail:#b3261e;--fail-bg:#f7e2de;--tool:#8a5f00;--tool-bg:#f6ecd4;--line1:#2d5fa8;--line2:#c0661b;--code-bg:#1d2129;--code-fg:#f3efe6;--img-bg:#ffffff;--sel-bg:#1d2129;--sel-fg:#fffdf8;--heat-fg:#ffffff;
--font-body:"IBM Plex Sans KR","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;--font-mono:"JetBrains Mono",Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#15181d;--sheet:#1c2027;--ink:#e8e4da;--muted:#a3a8b1;--rule:#343a44;--soft:#262b33;--pass:#6fcf8f;--pass-bg:#1d3326;--fail:#f08a7e;--fail-bg:#3a201d;--tool:#e3b54f;--tool-bg:#3a2f15;--line1:#7fa8ec;--line2:#f0a060;--code-bg:#0e1013;--code-fg:#e8e4da;--img-bg:#f4f1ea;--sel-bg:#e8e4da;--sel-fg:#15181d;--heat-fg:#0e1013;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#15181d;--sheet:#1c2027;--ink:#e8e4da;--muted:#a3a8b1;--rule:#343a44;--soft:#262b33;--pass:#6fcf8f;--pass-bg:#1d3326;--fail:#f08a7e;--fail-bg:#3a201d;--tool:#e3b54f;--tool-bg:#3a2f15;--line1:#7fa8ec;--line2:#f0a060;--code-bg:#0e1013;--code-fg:#e8e4da;--img-bg:#f4f1ea;--sel-bg:#e8e4da;--sel-fg:#15181d;--heat-fg:#0e1013;color-scheme:dark}
"""
고침 = [(r'@import url\([^)]*\);\s*', ''), (r':root\{--paper:[^}]*\}', ''), (r'"Pretendard Variable",Pretendard,"Malgun Gothic",system-ui,sans-serif', 'var(--font-body)'),
        (r'"Pretendard Variable",Pretendard,sans-serif', 'var(--font-body)'), (r'"JetBrains Mono",D2Coding,Consolas,monospace', 'var(--font-mono)'),
        (r'::selection\{background:#1d2129;color:#fffdf8\}', '::selection{background:var(--sel-bg);color:var(--sel-fg)}'),
        (r'main\{max-width:1040px;margin:0 auto;padding:56px 32px 96px\}', ''), (r'background:#fff\}', 'background:var(--img-bg)}'),
        (r'pre\{background:#1d2129;color:#f3efe6;', 'pre{background:var(--code-bg);color:var(--code-fg);'), (r'td\.열\.진\{color:#fff\}', 'td.열.진{color:var(--heat-fg)}'),
        (r'position:sticky;top:28px;', 'position:sticky;top:calc(28px + env(safe-area-inset-top, 0px));'), (r'@media \(max-width:640px\)\{main\{padding:32px 16px 64px\}', '@media (max-width:640px){main{padding-block:32px 64px}')]
뼈대 = """main{margin:0 auto;padding-block:56px 96px;padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px))}
@media (min-width:700px){main{padding-left:max(32px, env(safe-area-inset-left, 0px));padding-right:max(32px, env(safe-area-inset-right, 0px))}}
main>*{min-width:0}
.시안{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:0 0 28px;font-size:.9rem;color:var(--muted)}
.시안 button{font:600 .9rem var(--font-body);color:var(--ink);background:var(--sheet);border:1px solid var(--rule);border-radius:999px;padding:6px 14px;cursor:pointer}
.시안 button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.시안 button:focus-visible{outline:2px solid var(--line1);outline-offset:2px}
@media (prefers-reduced-motion:no-preference){
:root.m-stamp .기준줄{animation:줄 .5s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*120ms + 150ms)}
@keyframes 줄{from{opacity:.15;transform:translateX(-10px)}}
:root.m-stamp td.결과 svg path{stroke-dasharray:24;animation:긋기 .45s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*120ms + 380ms)}
@keyframes 긋기{from{stroke-dashoffset:24}}
:root.m-stamp header .판정{animation:도장 .7s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--n)*120ms + 520ms);box-shadow:0 6px 18px -8px currentColor}
@keyframes 도장{0%{transform:scale(1.35) rotate(-6deg);opacity:0;filter:blur(3px)}60%{transform:scale(.96) rotate(1deg);opacity:1;filter:none}100%{transform:none}}
:root.m-draw .곡선 polyline{stroke-dasharray:var(--len);animation:그림 1.6s cubic-bezier(.16,1,.3,1) both .2s}
@keyframes 그림{from{stroke-dashoffset:var(--len)}}
:root.m-draw .곡선 circle{animation:점 .4s ease-out both 1.4s}@keyframes 점{from{opacity:0}}
:root.m-draw td.열{transition:background-color 1.1s cubic-bezier(.16,1,.3,1)}:root.m-draw td.열.대기{background:var(--sheet)!important;color:inherit!important}}
"""
스크립트 = """<script>(()=>{const 줄임=matchMedia('(prefers-reduced-motion: reduce)').matches,root=document.documentElement,
선=[...document.querySelectorAll('.곡선 polyline')];선.forEach(p=>p.style.setProperty('--len',p.getTotalLength()));
const 셀=[...document.querySelectorAll('td.열')],수=[...document.querySelectorAll('td[data-n]')].filter(t=>t.dataset.n!=='');let io;
function 올리기(t){const v=parseFloat(t.dataset.n),자=(t.dataset.n.split('.')[1]||'').length,t0=performance.now();const 걸음=n=>{const k=Math.min(1,(n-t0)/900);t.textContent=(v*(1-Math.pow(2,-10*k))).toFixed(자);if(k<1)requestAnimationFrame(걸음)};requestAnimationFrame(걸음)}
function 그리기켜기(){if(io)io.disconnect();셀.forEach(c=>c.classList.add('대기'));io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const t=e.target;io.unobserve(t);if(t.classList.contains('열'))t.classList.remove('대기');else 올리기(t)}),{threshold:.4});[...셀,...수].forEach(x=>io.observe(x))}
function 고르기(m){root.classList.remove('m-stamp','m-draw');셀.forEach(c=>c.classList.remove('대기'));수.forEach(t=>t.textContent=t.dataset.n);void root.offsetWidth;root.classList.add(m==='draw'?'m-draw':'m-stamp');
 document.querySelectorAll('.시안 button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.m===m)));if(!줄임&&m==='draw')그리기켜기();document.getAnimations().forEach(a=>{a.cancel();a.play()})}
document.querySelectorAll('.시안 button').forEach(b=>b.addEventListener('click',()=>{고르기(b.dataset.m);try{history.replaceState(null,'','#'+b.dataset.m)}catch(e){}}));
고르기(location.hash==='#draw'?'draw':'stamp')})()</script>"""
def 만들기(판):
    import 보고; d = f"{뿌리}/하네스/판/{판}/"; 보고.만들기(판, None, "_아티팩트원본.html"); h = open(d + "_아티팩트원본.html", encoding="utf-8").read()
    css = re.search(r"<style>(.*?)</style>", h, re.S).group(1)
    for a, b in 고침: css = re.sub(a, b, css)
    본 = re.search(r"(<main.*?</main>)", h, re.S).group(1)
    본 = 본.replace("<header>", '<header>', 1)
    시안 = '<div class="시안" role="group" aria-label="모션 시안"><span>모션 시안</span><button type="button" data-m="stamp" aria-pressed="true">M1 도장</button><button type="button" data-m="draw" aria-pressed="false">M2 그리기</button></div>'
    본 = re.sub(r'(<main[^>]*>)(<header>.*?</header>)', lambda m: m.group(1) + m.group(2) + 시안, 본, count=1, flags=re.S)
    글 = (f'<title>판 {판} 보고서</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
          '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap">\n'
          f"<style>{토큰}{css}{뼈대}</style>\n{본}\n{스크립트}\n")
    import os; os.remove(d + "_아티팩트원본.html"); open(d + "아티팩트.html", "w", encoding="utf-8").write(글); return d + "아티팩트.html"
if __name__ == "__main__": sys.path.insert(0, 뿌리 + "/하네스"); print(만들기(sys.argv[1]))
