# -*- coding: utf-8 -*-
import json, os
S = os.path.dirname(os.path.abspath(__file__))
cells = json.load(open(S + "/cut/cells52_units.json", encoding="utf-8"))
html = r'''<title>오메가몬 머리 52 부품</title>
<style>
/* 레이아웃: 왼쪽 3D 캔버스(격자에 부품 52개 · 붙이지 않음) · 오른쪽 부품 목록. 클릭하면 그 부품만 크게 돌린다 */
:root{--bg:#f3f2ee;--fg:#1c1b19;--muted:#6d6a62;--panel:#ffffff;--line:#d9d6ce;--accent:#1f5fd6;--canvas:#2a2b33;
 --f-display:"Black Han Sans","Noto Sans KR",system-ui,sans-serif;--f-body:"Noto Sans KR",system-ui,sans-serif;--f-mono:ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}
html,body{height:100%}body{background:var(--bg);color:var(--fg);font-family:var(--f-body);margin:0;padding-inline:16px;padding-block:12px;box-sizing:border-box;display:flex;flex-direction:column;gap:10px}
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px}h1{font-family:var(--f-display);font-weight:400;font-size:26px;margin:0;text-wrap:balance}
header p{margin:0;color:var(--muted);font-size:13px}
main{flex:1;min-height:0;display:grid;grid-template-columns:1fr 300px;gap:12px}
#wrap{position:relative;background:var(--canvas);border-radius:8px;overflow:hidden;min-height:360px}canvas{display:block;width:100%;height:100%}
#hud{position:absolute;left:10px;top:10px;color:#fff;font-size:13px;background:rgba(0,0,0,.55);padding:6px 10px;border-radius:6px;max-width:calc(100% - 20px)}
#hud b{font-family:var(--f-display);font-weight:400;font-size:18px;margin-right:8px}
#hud button,#list button{font:inherit;cursor:pointer}
#hud button{margin-left:8px;background:#fff;color:#111;border:0;border-radius:4px;padding:2px 8px}
aside{background:var(--panel);border:1px solid var(--line);border-radius:8px;min-width:0;display:flex;flex-direction:column;min-height:0}
aside h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:10px 12px 4px}
#list{overflow:auto;padding:0 6px 8px;margin:0;list-style:none}
#list li{display:flex;gap:8px;align-items:center;padding:4px 6px;border-radius:5px;font-size:13px}
#list li:hover{background:color-mix(in srgb,var(--accent) 12%,transparent)}#list li.on{background:color-mix(in srgb,var(--accent) 22%,transparent)}
#list li button{all:unset;flex:1;display:flex;gap:8px;cursor:pointer;min-width:0}#list li button:focus-visible{outline:2px solid var(--accent);border-radius:4px}
.n{font-family:var(--f-mono);color:var(--muted);width:2ch;text-align:right;font-variant-numeric:tabular-nums}.sw{width:10px;height:10px;border-radius:2px;flex:none;border:1px solid var(--line)}
.grp{font-size:11px;color:var(--muted);margin:8px 6px 2px;letter-spacing:.06em}
footer{font-size:12px;color:var(--muted)}
@media (max-width:760px){main{grid-template-columns:1fr;grid-template-rows:60vh auto}}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700&display=swap">
<header><h1>오메가몬 머리 52 부품</h1><p>GrabCut 먹선 셀(02 정면) 하나 = 부품 하나. 붙이지 않고 격자에 늘어놓음. 앞면 윤곽은 원화 그대로 · 두께는 겹별 가정값(투구 6 · 마스크 5 · 눈 1.5 · 뿔 10, 머리 단위 뿔 끝 0 ~ 턱 100)</p></header>
<main><div id="wrap"><canvas id="c"></canvas><div id="hud"><b id="hn">전체</b><span id="ht">끌어서 돌리기 · 휠 확대 · 부품 클릭 = 하나만</span><button id="back" hidden>전체 보기</button></div></div>
<aside><h2>부품</h2><ul id="list"></ul></aside></main>
<footer>자료 <code>out/오메가몬2/지표/선파츠_정면.npz</code> · 이름 <code>오메가몬/지표/선파츠_정면_이름.json</code> · 10-01</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"></script>
<script>
const CELLS=__CELLS__;
const DEPTH={"투구":6,"마스크":5,"속머리(눈)":1.5}; const HORN=new Set([1,2,3]);
function colorOf(c){const n=c.name; if(/홍채/.test(n))return 0x2f6fd8; if(/동공/.test(n))return 0x10131a; if(/흰자|반짝/.test(n))return 0xd6e4ff; if(/눈구멍|그늘/.test(n))return 0x23252c; if(/번개/.test(n))return 0x3b5bd0; return 0xe9e9ee;}
const cv=document.getElementById('c'), wrap=document.getElementById('wrap');
const R=new THREE.WebGLRenderer({canvas:cv,antialias:true}); R.setPixelRatio(Math.min(devicePixelRatio,2));
const S=new THREE.Scene(); S.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--canvas').trim()||'#2a2b33');
const cam=new THREE.PerspectiveCamera(40,1,1,4000); S.add(new THREE.HemisphereLight(0xffffff,0x334,1.1)); const dl=new THREE.DirectionalLight(0xffffff,1.3); dl.position.set(1,2,3); S.add(dl);
// 부품 만들기: 셀 다각형 → Shape → Extrude(두께 · 베벨)
const parts=[]; const groups={"투구":[],"마스크":[],"속머리(눈)":[]};
for(const c of CELLS){const sh=new THREE.Shape(); c.poly.forEach(([x,y],i)=>i?sh.lineTo(x,-y):sh.moveTo(x,-y));
 const d=HORN.has(c.n)?10:DEPTH[c.layer]; const g=new THREE.ExtrudeGeometry(sh,{depth:d,bevelEnabled:true,bevelThickness:Math.min(0.8,d*0.15),bevelSize:0.6,bevelSegments:2,steps:1}); g.center();
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:colorOf(c),roughness:0.55,metalness:0.05})); m.userData=c; const bb=new THREE.Box3().setFromObject(m); m.userData.size=bb.getSize(new THREE.Vector3()); parts.push(m); groups[c.layer].push(m);}
// 격자 배치: 겹 순서(투구 → 눈 → 마스크) · 한 줄 8개 · 칸 크기는 가장 큰 부품
const cell=Math.max(...parts.map(p=>Math.max(p.userData.size.x,p.userData.size.y)))*0.9+4; const cols=8; const root=new THREE.Group(); S.add(root); let i=0; const order=[...groups["투구"],...groups["속머리(눈)"],...groups["마스크"]];
const labels=[]; function label(txt){const k=document.createElement('canvas'); k.width=256;k.height=64; const x=k.getContext('2d'); x.font='bold 30px "Noto Sans KR",sans-serif'; x.fillStyle='#fff'; x.textAlign='center'; x.fillText(txt,128,42); const t=new THREE.CanvasTexture(k); const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:t,transparent:true})); sp.scale.set(cell*0.9,cell*0.225,1); return sp;}
for(const p of order){const r=Math.floor(i/cols), q=i%cols; p.position.set((q-(cols-1)/2)*cell, -(r)*cell, 0); p.userData.home=p.position.clone(); root.add(p); const sp=label(p.userData.n+' '+p.userData.name.replace(/\(.*?\)/g,'').slice(0,9)); sp.position.set(p.position.x,p.position.y-cell*0.42,8); root.add(sp); labels.push(sp); i++;}
const rows=Math.ceil(order.length/cols); root.position.y=(rows-1)*cell/2;
// 간단 궤도(끌기 · 휠)
let yaw=0,pitch=0,dist=cell*cols*1.15, target=new THREE.Vector3(0,0,0), sel=null;
function place(){cam.position.set(target.x+dist*Math.sin(yaw)*Math.cos(pitch), target.y+dist*Math.sin(pitch), target.z+dist*Math.cos(yaw)*Math.cos(pitch)); cam.lookAt(target);}
let drag=null; cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,moved:false}; cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!drag)return; const dx=e.clientX-drag.x, dy=e.clientY-drag.y; if(Math.abs(dx)+Math.abs(dy)>3)drag.moved=true; yaw-=dx*0.006; pitch=Math.max(-1.4,Math.min(1.4,pitch+dy*0.006)); drag.x=e.clientX;drag.y=e.clientY;});
cv.addEventListener('pointerup',e=>{if(drag&&!drag.moved)pick(e); drag=null;}); cv.addEventListener('wheel',e=>{e.preventDefault(); dist*=Math.exp(e.deltaY*0.001); dist=Math.max(20,Math.min(5000,dist));},{passive:false});
const ray=new THREE.Raycaster(); function pick(e){const b=cv.getBoundingClientRect(); const v=new THREE.Vector2(((e.clientX-b.left)/b.width)*2-1,-((e.clientY-b.top)/b.height)*2+1); ray.setFromCamera(v,cam); const h=ray.intersectObjects(parts,false); if(h.length)select(h[0].object); }
const list=document.getElementById('list'), hn=document.getElementById('hn'), ht=document.getElementById('ht'), back=document.getElementById('back');
for(const [g,arr] of Object.entries(groups)){const h=document.createElement('li'); h.className='grp'; h.textContent=g+' · '+arr.length; list.appendChild(h); for(const p of arr){const li=document.createElement('li'); li.dataset.n=p.userData.n; const bt=document.createElement('button'); bt.innerHTML='<span class="n">'+p.userData.n+'</span><span class="sw" style="background:#'+p.material.color.getHexString()+'"></span><span>'+p.userData.name+'</span>'; bt.addEventListener('click',()=>select(p)); li.appendChild(bt); list.appendChild(li);} }
function select(p){sel=p; for(const q of parts){q.visible=q===p;} for(const s of labels)s.visible=false; root.position.set(0,0,0); p.position.set(0,0,0); const sz=Math.max(p.userData.size.x,p.userData.size.y,p.userData.size.z); dist=sz*2.8; target.set(0,0,0); yaw=0.4;pitch=0.25; hn.textContent=p.userData.n+' '+p.userData.name; ht.textContent=p.userData.layer+' · 가로 '+p.userData.size.x.toFixed(1)+' · 세로 '+p.userData.size.y.toFixed(1)+' · 두께 '+p.userData.size.z.toFixed(1)+' (머리 단위)'; back.hidden=false; document.querySelectorAll('#list li.on').forEach(l=>l.classList.remove('on')); const li=document.querySelector('#list li[data-n="'+p.userData.n+'"]'); if(li){li.classList.add('on'); li.scrollIntoView({block:'nearest'});}}
function all(){sel=null; for(const q of parts){q.visible=true; q.position.copy(q.userData.home); q.rotation.set(0,0,0);} for(const s of labels)s.visible=true; root.position.set(0,(rows-1)*cell/2,0); dist=cell*cols*1.15; yaw=0;pitch=0; target.set(0,0,0); hn.textContent='전체'; ht.textContent='끌어서 돌리기 · 휠 확대 · 부품 클릭 = 하나만'; back.hidden=true; document.querySelectorAll('#list li.on').forEach(l=>l.classList.remove('on'));}
back.addEventListener('click',all);
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight; R.setSize(w,h,false); cam.aspect=w/h; cam.updateProjectionMatrix();} new ResizeObserver(resize).observe(wrap); resize();
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
(function loop(){requestAnimationFrame(loop); if(sel&&!drag&&!reduce){sel.rotation.y+=0.012;} place(); R.render(S,cam);})();
</script>
'''
out = S + "/cut/parts52.html"
open(out, "w", encoding="utf-8").write(html.replace("__CELLS__", json.dumps(cells, ensure_ascii=False)))
print(out, os.path.getsize(out) // 1024, "KB")
