# -*- coding: utf-8 -*-
"""세 면(정면 · 옆 · 3/4) 먹선 셀 → three.js 부품 · 같은 부위끼리 한 줄에 나란히. 데이터 cut/three_views.json"""
import json, os
S = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(S + "/cut/three_views.json", encoding="utf-8"))
html = r'''<title>오메가몬 세 면 부품</title>
<style>
/* 레이아웃: 왼쪽 3D(행 = 부위 · 열 = 정면 / 옆 / 3-4) · 오른쪽 부위 목록. 부위를 누르면 그 줄만 크게 */
:root{--bg:#f3f2ee;--fg:#1c1b19;--muted:#6d6a62;--panel:#ffffff;--line:#d9d6ce;--accent:#1f5fd6;--canvas:#23242b;
 --f-display:"Black Han Sans","Noto Sans KR",system-ui,sans-serif;--f-body:"Noto Sans KR",system-ui,sans-serif;--f-mono:ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17181c;--fg:#ecebe6;--muted:#9a978f;--panel:#1f2026;--line:#34353d;--accent:#7aa6ff;--canvas:#101115;color-scheme:dark}
html,body{height:100%}body{background:var(--bg);color:var(--fg);font-family:var(--f-body);margin:0;padding-inline:16px;padding-block:12px;box-sizing:border-box;display:flex;flex-direction:column;gap:10px}
header{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 18px}h1{font-family:var(--f-display);font-weight:400;font-size:26px;margin:0}
header p{margin:0;color:var(--muted);font-size:13px}
main{flex:1;min-height:0;display:grid;grid-template-columns:1fr 330px;gap:12px}
#wrap{position:relative;background:var(--canvas);border-radius:8px;overflow:hidden;min-height:360px}canvas{display:block;width:100%;height:100%}
#hud{position:absolute;left:10px;top:10px;color:#fff;font-size:13px;background:rgba(0,0,0,.55);padding:6px 10px;border-radius:6px;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;max-width:calc(100% - 20px)}
#hud b{font-family:var(--f-display);font-weight:400;font-size:18px}#hud button{font:inherit;cursor:pointer;background:#fff;color:#111;border:0;border-radius:4px;padding:2px 9px}
aside{background:var(--panel);border:1px solid var(--line);border-radius:8px;min-width:0;display:flex;flex-direction:column;min-height:0}
aside h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:10px 12px 4px}
#list{overflow:auto;padding:0 6px 8px;margin:0;list-style:none}
#list li{border-radius:5px;font-size:13px;padding:5px 8px}#list li:hover{background:color-mix(in srgb,var(--accent) 12%,transparent)}#list li.on{background:color-mix(in srgb,var(--accent) 22%,transparent)}
#list button{all:unset;cursor:pointer;display:block;width:100%}#list button:focus-visible{outline:2px solid var(--accent);border-radius:4px}
#list .t{font-weight:700}#list .c{color:var(--muted);font-family:var(--f-mono);font-size:11px;font-variant-numeric:tabular-nums}
#list .miss{color:#c0392b}
footer{font-size:12px;color:var(--muted)}
@media (max-width:760px){main{grid-template-columns:1fr;grid-template-rows:60vh auto}}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700&display=swap">
<header><h1>오메가몬 세 면 부품</h1><p>02 극장판 정면 · 옆 · 3/4 캡처를 먹선으로 가른 셀(52 · 19 · 29)에 이름을 붙이고, 같은 부위끼리 한 줄에 놓았다. 색은 원화의 그 셀 평균색 · 판 두께는 가정(3). 붙이지 않음.</p></header>
<main><div id="wrap"><canvas id="c"></canvas><div id="hud"><b id="hn">전체</b><button id="back" hidden>전체 보기</button><span id="ht">끌어서 돌리기 · 휠 확대 · 오른쪽에서 부위 고르기</span></div></div>
<aside><h2>부위 · 정면 / 옆 / 3-4 셀 번호</h2><ul id="list"></ul></aside></main>
<footer>이름 <code>오메가몬/지표/선파츠_세면_이름.json</code> · 분할 <code>선파츠_{정면,옆,3-4}.npz</code> · 3/4 는 뿔이 화면 밖 · 깃 셀 셋은 머리가 아니라 따로 묶음</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"></script>
<script>
const DATA=__DATA__; const VIEWS=["정면","옆","3/4"]; const TH=3, COLW=120, ROWH=64;
const cv=document.getElementById('c'), wrap=document.getElementById('wrap');
const R=new THREE.WebGLRenderer({canvas:cv,antialias:true}); R.setPixelRatio(Math.min(devicePixelRatio,2));
const S=new THREE.Scene(); S.background=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--canvas').trim()||'#23242b');
const cam=new THREE.PerspectiveCamera(35,1,1,8000); S.add(new THREE.HemisphereLight(0xffffff,0x445,1.25)); const dl=new THREE.DirectionalLight(0xffffff,0.9); dl.position.set(1,2,3); S.add(dl);
function label(txt,w,h,size,color){const k=document.createElement('canvas'); k.width=512;k.height=96; const x=k.getContext('2d'); x.font='bold '+size+'px "Noto Sans KR",sans-serif'; x.fillStyle=color||'#fff'; x.textAlign='center'; x.fillText(txt,256,64); const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(k),transparent:true})); sp.scale.set(w,h,1); return sp;}
const rows=[]; const root=new THREE.Group(); S.add(root);
DATA.groups.forEach((g,ri)=>{const row=new THREE.Group(); row.userData={name:g.name,cells:g.cells}; const y0=-ri*ROWH;
 VIEWS.forEach((v,ci)=>{const ids=g.cells[v]; const cell=new THREE.Group(); let bb=new THREE.Box3();
  ids.forEach(n=>{const c=DATA.views[v][n]; if(!c)return; const sh=new THREE.Shape(); c.poly.forEach(([x,y],i)=>i?sh.lineTo(x,-y):sh.moveTo(x,-y));
   const geo=new THREE.ExtrudeGeometry(sh,{depth:TH,bevelEnabled:true,bevelThickness:0.4,bevelSize:0.35,bevelSegments:1}); const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:c.color,roughness:0.6})); m.userData={v,n,name:c.name}; cell.add(m); bb.expandByObject(m);});
  if(ids.length){const ctr=bb.getCenter(new THREE.Vector3()); cell.children.forEach(m=>m.position.sub(ctr));}
  else{const sp=label('없음',40,7.5,44,'#e06a5a'); cell.add(sp);}
  cell.position.set((ci-1)*COLW,y0,0); cell.userData.col=ci; row.add(cell);});
 const sp=label(g.name,90,17,40,'#ffe83a'); sp.position.set(-COLW*1.95,y0,0); row.add(sp); root.add(row); rows.push(row);});
const heads=VIEWS.map((v,ci)=>{const sp=label(v,60,11,52,'#ffffff'); sp.position.set((ci-1)*COLW,ROWH*0.75,0); root.add(sp); return sp;});
const total=(rows.length-1)*ROWH;
let yaw=0,pitch=0,dist=1200,target=new THREE.Vector3(-30,-total/2,0),sel=null;
function place(){cam.position.set(target.x+dist*Math.sin(yaw)*Math.cos(pitch),target.y+dist*Math.sin(pitch),target.z+dist*Math.cos(yaw)*Math.cos(pitch)); cam.lookAt(target);}
let drag=null; cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY}; cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{if(!drag)return; yaw-=(e.clientX-drag.x)*0.006; pitch=Math.max(-1.4,Math.min(1.4,pitch+(e.clientY-drag.y)*0.006)); drag.x=e.clientX;drag.y=e.clientY;});
cv.addEventListener('pointerup',()=>{drag=null;}); cv.addEventListener('wheel',e=>{e.preventDefault(); dist*=Math.exp(e.deltaY*0.001); dist=Math.max(40,Math.min(6000,dist));},{passive:false});
const list=document.getElementById('list'), hn=document.getElementById('hn'), ht=document.getElementById('ht'), back=document.getElementById('back');
rows.forEach((row,i)=>{const li=document.createElement('li'); const bt=document.createElement('button'); const c=row.userData.cells; const f=a=>a.length?a.join(' '):'<span class="miss">없음</span>';
 bt.innerHTML='<div class="t">'+row.userData.name+'</div><div class="c">정면 '+f(c["정면"])+'</div><div class="c">옆 '+f(c["옆"])+'</div><div class="c">3/4 '+f(c["3/4"])+'</div>'; bt.addEventListener('click',()=>select(i)); li.appendChild(bt); list.appendChild(li);});
function select(i){sel=i; rows.forEach((r,j)=>r.visible=j===i); heads.forEach(h=>h.position.y=-i*ROWH+ROWH*0.62); target.set(-30,-i*ROWH,0); dist=430; yaw=0.35;pitch=0.2; hn.textContent=rows[i].userData.name; ht.textContent='세 면에서 이 부위로 묶은 셀'; back.hidden=false; [...list.children].forEach((l,j)=>l.classList.toggle('on',j===i));}
function all(){sel=null; rows.forEach(r=>r.visible=true); heads.forEach(h=>h.position.y=ROWH*0.75); target.set(-30,-total/2,0); dist=1200; yaw=0;pitch=0; hn.textContent='전체'; ht.textContent='끌어서 돌리기 · 휠 확대 · 오른쪽에서 부위 고르기'; back.hidden=true; [...list.children].forEach(l=>l.classList.remove('on'));}
back.addEventListener('click',all);
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight; R.setSize(w,h,false); cam.aspect=w/h; cam.updateProjectionMatrix(); if(sel===null) dist=Math.max(1200,(total+ROWH*2)/(2*Math.tan(cam.fov*Math.PI/360))*1.05);} new ResizeObserver(resize).observe(wrap); resize(); all(); resize();
(function loop(){requestAnimationFrame(loop); place(); R.render(S,cam);})();
</script>
'''
out = S + "/cut/three_views.html"
open(out, "w", encoding="utf-8").write(html.replace("__DATA__", json.dumps(D, ensure_ascii=False)))
print(out, os.path.getsize(out) // 1024, "KB")
