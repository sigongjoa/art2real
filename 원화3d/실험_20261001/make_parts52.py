# -*- coding: utf-8 -*-
"""three.js 머리 52 부품 — 펼침(격자) / 조립(원래 자리 + z) 토글 · z 는 부품마다 칸에 적는다(사람 숫자 · 초안값은 내가) · 정면 원화 배경판으로 겹침 확인."""
import json, os
S = os.path.dirname(os.path.abspath(__file__))
cells = json.load(open(S + "/cut/cells52_units.json", encoding="utf-8"))
bg = json.load(open(S + "/cut/front_bg.json", encoding="utf-8"))
# z 초안(머리 단위 · 앞이 +): 겹 기본 + 부품별. 10-01 머리.md: 부리꼴 아래 얼굴이 가장 앞 · 투구 차양이 마스크 윗변을 덮음 · 눈은 눈구멍 속
Z = {"투구": 0.0, "마스크": -1.0, "속머리(눈)": -5.0}
ZP = {1: 3, 2: 3, 3: 3, 20: 2, 26: 0, 40: 0, 44: 0, 43: 0, 46: 0.5, 45: 1.5, 47: 1.5, 48: 1.5, 50: 1.5, 49: 3, 51: 3, 52: 4,
      24: -4.5, 34: -4.5, 31: -4, 33: -4.2, 25: -4.3, 35: -4.3, 38: -1.5, 42: -1.5, 41: -1.5, 12: -0.5, 19: -0.5}
for c in cells:
    c["z"] = ZP.get(c["n"], Z[c["layer"]])
html = r'''<title>오메가몬 머리 52 부품</title>
<style>
/* 레이아웃: 왼쪽 3D 캔버스 · 오른쪽 부품 목록(z 칸). 조립 = 원래 자리 + z · 펼침 = 격자. 배경판 = 정면 원화 */
:root{--bg:#f3f2ee;--fg:#1c1b19;--muted:#6d6a62;--panel:#ffffff;--line:#d9d6ce;--accent:#1f5fd6;--canvas:#2a2b33;
 --f-display:"Black Han Sans","Noto Sans KR",system-ui,sans-serif;--f-body:"Noto Sans KR",system-ui,sans-serif;--f-mono:ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}
html,body{height:100%}body{background:var(--bg);color:var(--fg);font-family:var(--f-body);margin:0;padding-inline:16px;padding-block:12px;box-sizing:border-box;display:flex;flex-direction:column;gap:10px}
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px}h1{font-family:var(--f-display);font-weight:400;font-size:26px;margin:0;text-wrap:balance}
header p{margin:0;color:var(--muted);font-size:13px}
main{flex:1;min-height:0;display:grid;grid-template-columns:1fr 320px;gap:12px}
#wrap{position:relative;background:var(--canvas);border-radius:8px;overflow:hidden;min-height:360px}canvas{display:block;width:100%;height:100%}
#hud{position:absolute;left:10px;top:10px;color:#fff;font-size:13px;background:rgba(0,0,0,.55);padding:6px 10px;border-radius:6px;max-width:calc(100% - 20px);display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}
#hud b{font-family:var(--f-display);font-weight:400;font-size:18px}
#hud button{font:inherit;cursor:pointer;background:#fff;color:#111;border:0;border-radius:4px;padding:2px 9px}#hud button.on{background:#ffe83a}
aside{background:var(--panel);border:1px solid var(--line);border-radius:8px;min-width:0;display:flex;flex-direction:column;min-height:0}
aside h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:10px 12px 4px;display:flex;justify-content:space-between}
aside h2 span{font-weight:400;text-transform:none;letter-spacing:0}
#list{overflow:auto;padding:0 6px 8px;margin:0;list-style:none}
#list li{display:flex;gap:6px;align-items:center;padding:3px 6px;border-radius:5px;font-size:13px}
#list li:hover{background:color-mix(in srgb,var(--accent) 12%,transparent)}#list li.on{background:color-mix(in srgb,var(--accent) 22%,transparent)}
#list li button{all:unset;flex:1;display:flex;gap:8px;cursor:pointer;min-width:0;align-items:center}#list li button:focus-visible{outline:2px solid var(--accent);border-radius:4px}
#list input{width:4.2em;font:inherit;font-family:var(--f-mono);font-size:12px;padding:1px 4px;border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--fg);text-align:right}
.n{font-family:var(--f-mono);color:var(--muted);width:2ch;text-align:right;font-variant-numeric:tabular-nums}.sw{width:10px;height:10px;border-radius:2px;flex:none;border:1px solid var(--line)}
.grp{font-size:11px;color:var(--muted);margin:8px 6px 2px;letter-spacing:.06em}
footer{font-size:12px;color:var(--muted)}
@media (max-width:760px){main{grid-template-columns:1fr;grid-template-rows:60vh auto}}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700&display=swap">
<header><h1>오메가몬 머리 52 부품</h1><p>GrabCut 먹선 셀(02 정면) 하나 = 부품 하나. 조립은 원래 자리에 z 만 더한 것 · z 는 오른쪽 칸의 숫자(앞이 +, 머리 단위 뿔 끝 0 ~ 턱 100) · 두께는 겹별 가정값(투구 6 · 마스크 5 · 눈 1.5 · 뿔 10)</p></header>
<main><div id="wrap"><canvas id="c"></canvas><div id="hud"><b id="hn">조립</b><button id="mode" class="on">조립 ↔ 펼침</button><button id="bgb" class="on">원화 배경</button><button id="vf">정면</button><button id="vs">옆</button><button id="v34">3/4</button><button id="back" hidden>전체 보기</button><span id="ht"></span></div></div>
<aside><h2>부품 <span>z (앞 +)</span></h2><ul id="list"></ul></aside></main>
<footer>자료 <code>out/오메가몬2/지표/선파츠_정면.npz</code> · 이름 <code>오메가몬/지표/선파츠_정면_이름.json</code> · z 초안은 10-01 머리.md(부리 아래가 가장 앞 · 차양이 마스크를 덮음 · 눈은 구멍 속)</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"></script>
<script>
const CELLS=__CELLS__; const BG=__BG__;
const DEPTH={"투구":6,"마스크":5,"속머리(눈)":1.5}; const HORN=new Set([1,2,3]);
function colorOf(c){const n=c.name; if(/홍채/.test(n))return 0x2f6fd8; if(/동공/.test(n))return 0x10131a; if(/흰자|반짝/.test(n))return 0xd6e4ff; if(/눈구멍|그늘/.test(n))return 0x23252c; if(/번개/.test(n))return 0x3b5bd0; return 0xe9e9ee;}
const cv=document.getElementById('c'), wrap=document.getElementById('wrap');
const R=new THREE.WebGLRenderer({canvas:cv,antialias:true}); R.setPixelRatio(Math.min(devicePixelRatio,2));
const S=new THREE.Scene(); S.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--canvas').trim()||'#2a2b33');
const cam=new THREE.PerspectiveCamera(35,1,1,4000); S.add(new THREE.HemisphereLight(0xffffff,0x334,1.0)); const dl=new THREE.DirectionalLight(0xffffff,1.2); dl.position.set(1,2,3); S.add(dl);
// 부품: 셀 다각형 → Extrude. 좌표는 원화 그대로(x 오른 + · y 아래 + → three 는 -y) · 앞면이 z=두께, 뒷면이 z=0 → 앞면이 z 값에 오도록 밀어 둔다
const parts=[]; const groups={"투구":[],"마스크":[],"속머리(눈)":[]}; const root=new THREE.Group(); S.add(root);
for(const c of CELLS){const sh=new THREE.Shape(); c.poly.forEach(([x,y],i)=>i?sh.lineTo(x,-y):sh.moveTo(x,-y));
 const d=HORN.has(c.n)?10:DEPTH[c.layer]; const g=new THREE.ExtrudeGeometry(sh,{depth:d,bevelEnabled:true,bevelThickness:Math.min(0.8,d*0.15),bevelSize:0.6,bevelSegments:2,steps:1}); g.translate(0,0,-d);
 const bb=new THREE.Box3().setFromBufferAttribute(g.getAttribute('position')); const ctr=bb.getCenter(new THREE.Vector3()); const size=bb.getSize(new THREE.Vector3());
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:colorOf(c),roughness:0.55,metalness:0.05})); m.userData={...c,ctr,size,d}; parts.push(m); groups[c.layer].push(m); root.add(m);}
// 배경판(정면 원화) — 모든 부품 뒤 z=-12
const tex=new THREE.TextureLoader().load(BG.data); tex.colorSpace=THREE.SRGBColorSpace; const bgm=new THREE.Mesh(new THREE.PlaneGeometry(BG.x1-BG.x0,BG.y1-BG.y0),new THREE.MeshBasicMaterial({map:tex,transparent:true,opacity:0.9})); bgm.position.set((BG.x0+BG.x1)/2,-(BG.y0+BG.y1)/2,-12); S.add(bgm);
// 격자 자리
const cell=Math.max(...parts.map(p=>Math.max(p.userData.size.x,p.userData.size.y)))*0.9+4; const cols=8; const order=[...groups["투구"],...groups["속머리(눈)"],...groups["마스크"]]; const rows=Math.ceil(order.length/cols);
const labels=[]; function label(txt){const k=document.createElement('canvas'); k.width=256;k.height=64; const x=k.getContext('2d'); x.font='bold 30px "Noto Sans KR",sans-serif'; x.fillStyle='#fff'; x.textAlign='center'; x.fillText(txt,128,42); const t=new THREE.CanvasTexture(k); const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:t,transparent:true})); sp.scale.set(cell*0.9,cell*0.225,1); return sp;}
order.forEach((p,i)=>{const r=Math.floor(i/cols),q=i%cols; p.userData.grid=new THREE.Vector3((q-(cols-1)/2)*cell-p.userData.ctr.x, -(r)*cell+(rows-1)*cell/2-p.userData.ctr.y, -p.userData.ctr.z); const sp=label(p.userData.n+' '+p.userData.name.replace(/\(.*?\)/g,'').slice(0,9)); sp.position.set(p.userData.grid.x+p.userData.ctr.x,p.userData.grid.y+p.userData.ctr.y-cell*0.42,8); root.add(sp); labels.push(sp);});
let assembled=true, showBg=true, sel=null;
function layout(){for(const p of parts){p.rotation.set(0,0,0); if(assembled)p.position.set(0,0,p.userData.z); else p.position.copy(p.userData.grid);} for(const s of labels)s.visible=!assembled&&!sel; bgm.visible=assembled&&showBg&&!sel;}
// 궤도
let yaw=0,pitch=0,dist=240, target=new THREE.Vector3(0,-50,0);
function place(){cam.position.set(target.x+dist*Math.sin(yaw)*Math.cos(pitch), target.y+dist*Math.sin(pitch), target.z+dist*Math.cos(yaw)*Math.cos(pitch)); cam.lookAt(target);}
function home(){target.set(assembled?0:0,assembled?-50:0,0); dist=assembled?240:cell*cols*1.15; yaw=0;pitch=0;}
let drag=null; cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,moved:false}; cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!drag)return; const dx=e.clientX-drag.x, dy=e.clientY-drag.y; if(Math.abs(dx)+Math.abs(dy)>3)drag.moved=true; yaw-=dx*0.006; pitch=Math.max(-1.4,Math.min(1.4,pitch+dy*0.006)); drag.x=e.clientX;drag.y=e.clientY;});
cv.addEventListener('pointerup',e=>{if(drag&&!drag.moved)pick(e); drag=null;}); cv.addEventListener('wheel',e=>{e.preventDefault(); dist*=Math.exp(e.deltaY*0.001); dist=Math.max(20,Math.min(5000,dist));},{passive:false});
const ray=new THREE.Raycaster(); function pick(e){const b=cv.getBoundingClientRect(); const v=new THREE.Vector2(((e.clientX-b.left)/b.width)*2-1,-((e.clientY-b.top)/b.height)*2+1); ray.setFromCamera(v,cam); const h=ray.intersectObjects(parts.filter(p=>p.visible),false); if(h.length)select(h[0].object); }
const list=document.getElementById('list'), hn=document.getElementById('hn'), ht=document.getElementById('ht'), back=document.getElementById('back');
for(const [g,arr] of Object.entries(groups)){const h=document.createElement('li'); h.className='grp'; h.textContent=g+' · '+arr.length; list.appendChild(h);
 for(const p of arr){const li=document.createElement('li'); li.dataset.n=p.userData.n; const bt=document.createElement('button'); bt.innerHTML='<span class="n">'+p.userData.n+'</span><span class="sw" style="background:#'+p.material.color.getHexString()+'"></span><span>'+p.userData.name+'</span>'; bt.addEventListener('click',()=>select(p));
  const inp=document.createElement('input'); inp.type='number'; inp.step='0.5'; inp.id='z'+p.userData.n; inp.value=p.userData.z; inp.title='z (앞 +)'; inp.addEventListener('input',()=>{p.userData.z=parseFloat(inp.value)||0; if(assembled&&!sel)p.position.z=p.userData.z;});
  li.appendChild(bt); li.appendChild(inp); list.appendChild(li);} }
function select(p){sel=p; for(const q of parts){q.visible=q===p;} layout(); p.position.set(-p.userData.ctr.x,-p.userData.ctr.y,-p.userData.ctr.z); const sz=Math.max(p.userData.size.x,p.userData.size.y,p.userData.size.z); dist=sz*2.8; target.set(0,0,0); yaw=0.4;pitch=0.25; hn.textContent=p.userData.n+' '+p.userData.name; ht.textContent=p.userData.layer+' · 가로 '+p.userData.size.x.toFixed(1)+' · 세로 '+p.userData.size.y.toFixed(1)+' · 두께 '+p.userData.d+' · z '+p.userData.z; back.hidden=false; document.querySelectorAll('#list li.on').forEach(l=>l.classList.remove('on')); const li=document.querySelector('#list li[data-n="'+p.userData.n+'"]'); if(li){li.classList.add('on'); li.scrollIntoView({block:'nearest'});}}
function all(){sel=null; for(const q of parts)q.visible=true; layout(); home(); hn.textContent=assembled?'조립':'펼침'; ht.textContent=''; back.hidden=true; document.querySelectorAll('#list li.on').forEach(l=>l.classList.remove('on'));}
back.addEventListener('click',all);
document.getElementById('mode').addEventListener('click',e=>{assembled=!assembled; e.target.classList.toggle('on',assembled); all();});
document.getElementById('bgb').addEventListener('click',e=>{showBg=!showBg; e.target.classList.toggle('on',showBg); layout();});
document.getElementById('vf').addEventListener('click',()=>{yaw=0;pitch=0;}); document.getElementById('vs').addEventListener('click',()=>{yaw=Math.PI/2;pitch=0;}); document.getElementById('v34').addEventListener('click',()=>{yaw=0.6;pitch=0.15;});
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight; R.setSize(w,h,false); cam.aspect=w/h; cam.updateProjectionMatrix();} new ResizeObserver(resize).observe(wrap); resize();
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches; all();
(function loop(){requestAnimationFrame(loop); if(sel&&!drag&&!reduce){sel.rotation.y+=0.012;} place(); R.render(S,cam);})();
</script>
'''
out = S + "/cut/parts52.html"
open(out, "w", encoding="utf-8").write(html.replace("__CELLS__", json.dumps(cells, ensure_ascii=False)).replace("__BG__", json.dumps(bg)))
print(out, os.path.getsize(out) // 1024, "KB")
