// 장난감 쇼츠 Three.js 공용 — 무대(빛 · 하늘 · 후처리) · 공원 · 고양이 · 모션 그래픽 키트.
// 장면 html 이 import 한다(three굽기.py 가 http://scene.local/ 로 파일을 넘겨준다). 카니자v2.html 에서 떼어 냄.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
export { THREE };

export const W = 1080, H = 1920;
export const clamp01 = u => Math.min(Math.max(u, 0), 1);
export const ease = u => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(u));
export const back = k => { const c = 1.7; k = clamp01(k) - 1; return 1 + (c + 1) * k * k * k + c * k * k; };
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
let seed = 11; export const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

// 시간표: U(줄, a, b, f) = 줄 안 a..b 구간 진행(이징) · after(줄, f) · cutAt(f) = [컷, 컷 안 진행]
export function 시간(T) {
  return {
    U: (i, a, b, f) => { const [f0, f1] = T.lines[i], L = f1 - f0; return ease((f - f0 - a * L) / Math.max(1, (b - a) * L)); },
    after: (i, f) => f >= T.lines[i][0],
    cutAt: f => { let s = 1; for (const c of T.cuts) { if (f < s + c.n) return [c, (f - s) / c.n]; s += c.n; } return [T.cuts.at(-1), 1]; },
  };
}

export const std = (c, r = 0.75, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
export function mesh(scene, g, m, p = [0, 0, 0], parent = scene) { const o = new THREE.Mesh(g, m); o.position.set(...p); o.castShadow = o.receiveShadow = true; parent.add(o); return o; }
export function canvasTex(w, h, paint, rep) { const c = document.createElement('canvas'); c.width = w; c.height = h; paint(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); } return t; }

// 무대: 렌더러 · 하늘(노을로 바꿀 수 있음) · 해 · 후처리(AO → 피사계 심도 → 블룸 문턱 8 → 출력)
export function 무대() {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
  document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene(); scene.fog = new THREE.Fog(0xd8e6f2, 60, 220);
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const skyU = { top: { value: new THREE.Color(0x5d9be0) }, bot: { value: new THREE.Color(0xf6e3d2) } };
  scene.add(new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false, uniforms: skyU,
    vertexShader: 'varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }',
    fragmentShader: 'uniform vec3 top; uniform vec3 bot; varying vec3 p; void main(){ float h = clamp(normalize(p).y*1.8+0.12,0.,1.); gl_FragColor = vec4(mix(bot, top, h), 1.); }' })));
  scene.add(new THREE.HemisphereLight(0xe8f2ff, 0x6f8f5a, 0.9));
  const sun = new THREE.DirectionalLight(0xfff0dc, 2.6); sun.position.set(30, 45, 20); sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096); Object.assign(sun.shadow.camera, { left: -30, right: 30, top: 30, bottom: -30, far: 150 }); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02; scene.add(sun);
  const camera = new THREE.PerspectiveCamera(50, W / H, 0.02, 2000);
  const composer = new EffectComposer(renderer); composer.setPixelRatio(1); composer.setSize(W, H);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new GTAOPass(scene, camera, W, H); ao.blendIntensity = 0.85; composer.addPass(ao);
  const bokeh = new BokehPass(scene, camera, { focus: 5, aperture: 0.0002, maxblur: 0.009 }); composer.addPass(bokeh);
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.6, 0.4, 8));
  composer.addPass(new OutputPass());
  const 노을 = k => { skyU.top.value.setHex(0x5d9be0).lerp(new THREE.Color(0x3a4f9a), k); skyU.bot.value.setHex(0xf6e3d2).lerp(new THREE.Color(0xffa36b), k); sun.color.setHex(0xfff0dc).lerp(new THREE.Color(0xffb27a), k); };
  // 카메라를 놓고 그린다 — 초점은 바라보는 곳, 가까울수록 배경이 크게 흐려진다(미니어처)
  const 찍기 = (f, pos, tgt, fov) => { pos.y += 0.01 * Math.sin(f / 13); camera.position.copy(pos); camera.fov = fov; camera.updateProjectionMatrix(); camera.lookAt(tgt);
    const focus = camera.position.distanceTo(tgt); bokeh.uniforms.focus.value = focus; bokeh.uniforms.aperture.value = 0.0007 / focus; composer.render(); };
  return { renderer, scene, camera, sun, 노을, 찍기 };
}

// 공원: 풀 · 흰 광장(선택) · 길 · 나무(흔들림) · 벤치 · 가로등 · 꽃밭 · 언덕 · 새 떼 · 구름. 움직임(f) 로 매 프레임 갱신
export function 공원(scene, { plaza = 14 } = {}) {
  const M = (g, m, p, parent) => mesh(scene, g, m, p, parent);
  const grassTex = canvasTex(512, 512, (x, w, h) => { x.fillStyle = '#7fb865'; x.fillRect(0, 0, w, h);
    for (let i = 0; i < 9000; i++) { const g = 120 + rnd() * 70; x.fillStyle = `rgba(${70 + rnd() * 50},${g},${60 + rnd() * 30},0.5)`; x.fillRect(rnd() * w, rnd() * h, 2, 3 + rnd() * 4); } }, 60);
  M(new THREE.CircleGeometry(300, 64).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: grassTex, roughness: 0.95 }), [0, -0.02, 0]);
  if (plaza) {
    const plazaTex = canvasTex(1024, 1024, (x, w, h) => { x.fillStyle = '#f4f2ee'; x.fillRect(0, 0, w, h); x.strokeStyle = 'rgba(0,0,0,0.035)'; x.lineWidth = 2;
      for (let k = 0; k <= 16; k++) { x.beginPath(); x.moveTo(k * w / 16, 0); x.lineTo(k * w / 16, h); x.stroke(); x.beginPath(); x.moveTo(0, k * h / 16); x.lineTo(w, k * h / 16); x.stroke(); } });
    M(new THREE.CircleGeometry(plaza, 96).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: plazaTex, roughness: 0.55 }), [0, 0, 0]);
    M(new THREE.RingGeometry(plaza, plaza + 1.6, 96).rotateX(-Math.PI / 2), std(0xcdbfa8, 0.95), [0, 0.005, 0]);
  }
  for (let k = 0; k < 4; k++) { const a = k * Math.PI / 2 + Math.PI / 4;
    const p = M(new THREE.PlaneGeometry(2.4, 40).rotateX(-Math.PI / 2), std(0xcdbfa8, 0.95), [Math.cos(a) * 35, 0.004, Math.sin(a) * 35]); p.rotation.y = -a + Math.PI / 2; }
  const leafM = [std(0x4f9a52, 0.85), std(0x62ad5c, 0.85), std(0x3f8848, 0.85)], trunkM = std(0x8a6242, 0.9), trees = [];
  const tree = (x, z, s) => { const g = new THREE.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); g.rotation.y = rnd() * 6; g.userData.ph = rnd() * 6; scene.add(g); trees.push(g);
    M(new THREE.CylinderGeometry(0.18, 0.28, 2.2, 8), trunkM, [0, 1.1, 0], g);
    for (let k = 0; k < 4; k++) M(new THREE.IcosahedronGeometry(1.1 - k * 0.12, 2), leafM[k % 3], [(rnd() - .5) * 1.2, 2.6 + k * 0.55 + rnd() * .3, (rnd() - .5) * 1.2], g); };
  for (let i = 0; i < 90; i++) { const a = rnd() * Math.PI * 2, r = plaza + 5 + rnd() * 45;
    if (Math.abs(Math.sin(a - Math.PI / 4) * r) < 3 || Math.abs(Math.cos(a - Math.PI / 4) * r) < 3) continue; tree(r * Math.cos(a), r * Math.sin(a), 0.8 + rnd() * 0.8); }
  const benchM = std(0xa8754d, 0.8), ironM = std(0x2d3238, 0.5, 0.6), rb = plaza + 2.6;
  for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4, b = new THREE.Group(); b.position.set(rb * Math.cos(a), 0, rb * Math.sin(a)); b.rotation.y = -a - Math.PI / 2; scene.add(b);
    if (k % 2 === 0) { for (let s = 0; s < 3; s++) M(new THREE.BoxGeometry(1.8, 0.05, 0.12), benchM, [0, 0.45, -0.15 + s * 0.15], b);
      M(new THREE.BoxGeometry(1.8, 0.35, 0.05), benchM, [0, 0.72, 0.25], b); for (const sx of [-0.8, 0.8]) M(new THREE.BoxGeometry(0.06, 0.45, 0.5), ironM, [sx, 0.22, 0], b); }
    else { M(new THREE.CylinderGeometry(0.06, 0.08, 3.6, 8), ironM, [0, 1.8, 0], b); M(new THREE.SphereGeometry(0.22, 12, 8), new THREE.MeshStandardMaterial({ color: 0xfff6dd, emissive: 0xffe6a0, emissiveIntensity: 1.6 }), [0, 3.7, 0], b); } }
  const petalC = [0xff7fa3, 0xffd04a, 0xffffff, 0xa98cff, 0xff9a52];
  const fl = new THREE.InstancedMesh(new THREE.SphereGeometry(0.09, 6, 4), new THREE.MeshStandardMaterial({ roughness: 0.7 }), 1400), dd = new THREE.Object3D();
  for (let i = 0; i < 1400; i++) { const a = rnd() * 6.283, r = plaza + 1.8 + rnd() * 2.2; dd.position.set(r * Math.cos(a), 0.12 + rnd() * 0.1, r * Math.sin(a)); dd.scale.setScalar(0.6 + rnd()); dd.updateMatrix(); fl.setMatrixAt(i, dd.matrix); fl.setColorAt(i, new THREE.Color(petalC[i % 5])); }
  fl.castShadow = true; scene.add(fl);
  for (let i = 0; i < 7; i++) { const a = rnd() * 6.28; M(new THREE.SphereGeometry(40 + rnd() * 30, 24, 12), std(0x86b07a, 1), [170 * Math.cos(a), -25, 170 * Math.sin(a)]).scale.y = 0.5; }
  const birdM = std(0x3b3f48, 0.7);
  const birds = Array.from({ length: 7 }, (_, i) => { const b = new THREE.Group(); scene.add(b);
    const wings = [-1, 1].map(s => { const w = new THREE.Group(); b.add(w); M(new THREE.BoxGeometry(0.12, 0.02, 0.5), birdM, [0, 0, 0.25 * s], w); return w; });
    M(new THREE.SphereGeometry(0.09, 8, 6), birdM, [0, 0, 0], b).scale.set(2.2, 1, 1); b.userData = { wings, ph: rnd() * 6, dx: (i % 3) * 1.6 - (i > 3 ? 1.5 : 0), dy: (i % 2) * 0.8, dz: Math.floor(i / 2) * 1.3 }; return b; });
  const clouds = Array.from({ length: 8 }, (_, i) => { const c = new THREE.Group(); c.position.set(-160 + i * 45, 45 + rnd() * 25, -60 - rnd() * 120); scene.add(c);
    for (let k = 0; k < 6; k++) { const m = new THREE.Mesh(new THREE.SphereGeometry(7 + rnd() * 6, 16, 10), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, emissive: 0x8899aa, emissiveIntensity: 0.25 }));
      m.position.set(k * 8 - 20, (rnd() - .3) * 4, rnd() * 6); m.scale.y = 0.6; c.add(m); } return c; });
  return { 움직임: f => {
    trees.forEach(g => { g.rotation.z = 0.025 * Math.sin(f / 23 + g.userData.ph); g.rotation.x = 0.018 * Math.sin(f / 31 + g.userData.ph); });
    birds.forEach(b => { const u = ((f / 420) + 0.15) % 1, d = b.userData; b.position.set(-45 + 90 * u + d.dx, 14 + d.dy + 0.4 * Math.sin(f / 9 + d.ph), -8 + d.dz);
      d.wings.forEach((w, k) => w.rotation.x = (k ? 1 : -1) * 0.6 * Math.sin(f / 2.2 + d.ph)); });
    clouds.forEach((c, i) => c.position.x = -160 + i * 45 + f * 0.03);
  } };
}

// 고양이 — 지온 조립(캡슐 몸 · 공 머리 · 원뿔 귀 · 마디 꼬리) · 줄무늬 · 눈 하이라이트 · 수염. +x 를 본다. 자세({walk, surprise, look, yaw, sq, flat})
export function 고양이(scene) {
  const M = (g, m, p, parent) => mesh(scene, g, m, p, parent);
  const fur = std(0xec9446, 0.8), furD = std(0xc56a2e, 0.8), cream = std(0xfbecd8, 0.85), pink = std(0xf79aa7, 0.7);
  const cat = new THREE.Group(); scene.add(cat);
  M(new THREE.CapsuleGeometry(0.13, 0.26, 8, 16).rotateZ(Math.PI / 2), fur, [0, 0.3, 0], cat);
  M(new THREE.SphereGeometry(0.1, 14, 10), cream, [0.06, 0.25, 0], cat).scale.set(1.6, 0.8, 1.05);
  for (const x of [-0.12, -0.03, 0.06]) M(new THREE.TorusGeometry(0.133, 0.014, 6, 18, Math.PI * 0.9).rotateY(Math.PI / 2).rotateX(Math.PI * 0.05), furD, [x, 0.3, 0], cat);
  const head = new THREE.Group(); head.position.set(0.25, 0.44, 0); cat.add(head);
  M(new THREE.SphereGeometry(0.135, 24, 16), fur, [0, 0, 0], head).scale.set(1, 0.9, 1.08);
  M(new THREE.SphereGeometry(0.07, 14, 10), cream, [0.09, -0.045, 0], head).scale.set(0.8, 0.7, 1.2);
  const ears = [-1, 1].map(s => { const e = new THREE.Group(); e.position.set(-0.01, 0.1, 0.075 * s); head.add(e);
    M(new THREE.ConeGeometry(0.055, 0.11, 12), fur, [0, 0.04, 0], e); M(new THREE.ConeGeometry(0.03, 0.07, 12), pink, [0.02, 0.035, 0], e); return e; });
  const eyes = [-1, 1].map(s => { const e = new THREE.Group(); e.position.set(0.105, 0.025, 0.052 * s); head.add(e);
    M(new THREE.SphereGeometry(0.036, 16, 12), std(0xfdfdf8, 0.3), [0, 0, 0], e);
    const pu = M(new THREE.SphereGeometry(0.024, 14, 10), std(0x15121a, 0.2), [0.018, 0, 0], e); pu.scale.set(0.6, 1.15, 1);
    M(new THREE.SphereGeometry(0.008, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }), [0.037, 0.012, 0.008 * s], e); e.userData.pu = pu; return e; });
  M(new THREE.SphereGeometry(0.016, 10, 8), pink, [0.15, -0.025, 0], head).scale.set(0.7, 0.7, 1.2);
  const whM = new THREE.LineBasicMaterial({ color: 0x4a3a3a });
  for (const s of [-1, 1]) for (const k of [-1, 0, 1]) head.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([V(0.13, -0.04, 0.04 * s), V(0.17, -0.04 + 0.018 * k, 0.16 * s)]), whM));
  const legs = [[0.17, 0.08], [0.17, -0.08], [-0.15, 0.08], [-0.15, -0.08]].map(([x, z]) => { const g = new THREE.Group(); g.position.set(x, 0.24, z); cat.add(g);
    M(new THREE.CapsuleGeometry(0.038, 0.13, 6, 10), fur, [0, -0.11, 0], g); M(new THREE.SphereGeometry(0.045, 12, 8), cream, [0.01, -0.21, 0], g).scale.set(1.2, 0.65, 1); return g; });
  const tail = []; let par = cat, tp = [-0.27, 0.36, 0];
  for (let k = 0; k < 7; k++) { const g = new THREE.Group(); g.position.set(...tp); par.add(g); M(new THREE.SphereGeometry(0.042 - k * 0.002, 12, 8), k % 2 ? furD : fur, [0, 0.03, 0], g).scale.y = 1.4; tail.push(g); par = g; tp = [0, 0.065, 0]; }
  const 자세 = (f, { walk = false, surprise = 0, look = 0, yaw = 0, sq = 0, flat = 0, air = false } = {}) => {
    cat.scale.set(1 + 0.15 * sq + 0.35 * flat, 1 - 0.18 * sq - 0.45 * flat, 1 + 0.35 * flat);
    head.rotation.set(0, yaw, 0.5 * look + 0.25 * surprise);
    legs.forEach((g, i) => g.rotation.z = walk ? 0.6 * Math.sin(f / 3 + ((i === 0 || i === 3) ? 0 : Math.PI)) : (air ? (i < 2 ? -0.7 : 0.7) : 0));
    tail.forEach((g, k) => { g.rotation.z = -0.35 + 0.18 * Math.sin(f / 7 - k * 0.6) - 0.5 * surprise; g.rotation.x = 0.12 * Math.sin(f / 11 - k * 0.5); });
    ears.forEach(e => e.rotation.x = 0.04 * Math.sin(f / 13) - 0.3 * surprise * Math.sign(e.position.z));
    const blink = (f % 64) < 3 && surprise < 0.1 ? 0.12 : 1;
    eyes.forEach(e => { e.scale.set(1, (1 + 0.4 * surprise) * blink, 1 + 0.25 * surprise); e.userData.pu.scale.set(0.6 * (1 - 0.4 * surprise), 1.15 * (1 - 0.4 * surprise), 1); });
  };
  return { cat, head, 자세, 머리위치: () => { const p = new THREE.Vector3(); head.getWorldPosition(p); return p; } };
}

// 모션 그래픽 — 3D 위치를 화면 좌표로 바꿔 #out 2D 캔버스에 얹는다(three굽기.py 가 window.OUT 을 찍는다).
// 크기 규칙: 폰에서 한눈에 — 이름표 92px · 숫자 120px · 큰 글씨는 위(y≈430 은 굽기의 큰 낱말 자리, 그 아래 620 쯤). 자막 띠 y≈1250–1330 은 피한다.
export function 모션(renderer, camera) {
  const out = document.createElement('canvas'); out.width = W; out.height = H; const g = out.getContext('2d'); window.OUT = out;
  const FONT = '"Malgun Gothic", sans-serif', INK = '#1f2430', GOLD = '#ffd24a';
  const scr = v => { const p = v.clone().project(camera); return [(p.x + 1) / 2 * W, (1 - p.y) / 2 * H, p.z < 1 && Math.abs(p.x) < 1.3 && Math.abs(p.y) < 1.3]; };
  const pill = (x, y, text, size, k, fill = 'rgba(255,255,255,0.93)', color = INK) => { if (k <= 0) return;
    g.save(); g.translate(x, y); g.scale(0.6 + 0.4 * back(k), 0.6 + 0.4 * back(k)); g.globalAlpha = clamp01(k * 2);
    g.font = `bold ${size}px ${FONT}`; const w = g.measureText(text).width + size * 1.1, h = size * 1.6;
    g.shadowColor = 'rgba(0,0,0,0.25)'; g.shadowBlur = 18; g.shadowOffsetY = 6; g.fillStyle = fill; g.beginPath(); g.roundRect(-w / 2, -h / 2, w, h, h / 2); g.fill();
    g.shadowColor = 'transparent'; g.fillStyle = color; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, 0, size * 0.04); g.restore(); };
  const stroke2 = (pts, w, color, dash) => { g.save(); g.lineCap = 'round'; if (dash) g.setLineDash(dash);
    for (const [lw, c] of [[w * 1.9, 'rgba(20,20,30,0.45)'], [w, color]]) { g.lineWidth = lw; g.strokeStyle = c; g.beginPath(); pts.forEach(([x, y], j) => j ? g.lineTo(x, y) : g.moveTo(x, y)); g.stroke(); } g.restore(); };
  return {
    GOLD, scr, pill,
    begin: () => { g.clearRect(0, 0, W, H); g.drawImage(renderer.domElement, 0, 0); },
    // 점 → 지시선 → 이름표(물체를 따라붙는다). dx, dy 는 화면 픽셀
    label(anchor, text, k, dx, dy) { if (k <= 0) return; const [x, y, ok] = scr(anchor); if (!ok) return;
      const lx = Math.min(W - 330, Math.max(330, x + dx)), ly = Math.max(260, y + dy), d = clamp01(k * 1.6);
      stroke2([[x, y], [x + (lx - x) * d, y + (ly - y) * d]], 9, '#fff');
      g.save(); g.fillStyle = '#fff'; g.strokeStyle = INK; g.lineWidth = 7; g.beginPath(); g.arc(x, y, 20 * Math.min(1, k * 3), 0, 7); g.fill(); g.stroke(); g.restore();
      if (k > 0.45) pill(lx, ly, text, 92, (k - 0.45) / 0.55); },
    // 굵은 테두리 큰 글씨(튀어나옴)
    big(text, y, size, k, color = '#fff') { if (k <= 0) return; g.save(); g.translate(W / 2, y); const sc = 0.6 + 0.4 * back(k); g.scale(sc, sc); g.globalAlpha = clamp01(k * 2);
      g.font = `bold ${size}px ${FONT}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
      g.lineWidth = size * 0.16; g.strokeStyle = 'rgba(20,20,30,0.95)'; g.strokeText(text, 0, 0); g.fillStyle = color; g.fillText(text, 0, 0); g.restore(); },
    // 3D 두 점 사이 점선(뇌가 이은 부분 같은 「상상한 선」) — k 만큼 그려진다
    ghost(p, q, k, w = 14) { if (k <= 0) return; const [x0, y0] = scr(p), [x1, y1] = scr(q); stroke2([[x0, y0], [x0 + (x1 - x0) * clamp01(k), y0 + (y1 - y0) * clamp01(k)]], w, GOLD, [w * 2.2, w * 1.6]); },
    // 화면 위 양쪽 화살표(움직임 방향) — 3D 점 p 에서 좌우로
    arrow2(p, k, len = 150) { if (k <= 0) return; const [x, y, ok] = scr(p); if (!ok) return; const L = len * clamp01(k * 1.5);
      for (const s of [-1, 1]) { const tip = x + s * L; stroke2([[x, y], [tip, y]], 14, GOLD); stroke2([[tip - s * 40, y - 30], [tip, y], [tip - s * 40, y + 30]], 14, GOLD); } },
    // 두 3D 점 사이 치수 괄호 + 이름(틈 · 길이)
    bracket(p, q, text, k, side = 1) { if (k <= 0) return; const [x0, y0] = scr(p), [x1, y1] = scr(q), off = 70 * side;
      stroke2([[x0, y0], [x0 + off, y0], [x1 + off, y1], [x1, y1]].map(([x, y], j) => [x, y]), 10, '#fff');
      pill(x0 + off + 150 * side, (y0 + y1) / 2, text, 80, k, 'rgba(31,36,48,0.92)', GOLD); },
    // 놀람 · 강조 파동(세 겹, 화면 가득) — q 0..1
    pulse(p, q) { if (q <= 0 || q >= 1) return; const [x, y, ok] = scr(p); if (!ok) return;
      for (const d of [0, 0.2, 0.4]) { const t = clamp01(q - d); if (t <= 0) continue; g.save(); g.globalAlpha = 1 - t; g.lineWidth = 34 * (1 - t) + 4; g.strokeStyle = GOLD; g.beginPath(); g.arc(x, y, 90 + 850 * t, 0, 7); g.stroke(); g.restore(); } },
    // 정답: 화면 테두리가 금빛으로 숨 쉰다
    border(k, f) { if (k <= 0) return; g.save(); g.globalAlpha = k * (0.55 + 0.35 * Math.sin(f / 5)); g.lineWidth = 44; g.strokeStyle = GOLD; g.shadowColor = GOLD; g.shadowBlur = 40; g.strokeRect(13, 13, W - 26, H - 26); g.restore(); },
    tag(text, k) { pill(W - 40 - text.length * 13, H - 130, text, 48, k, 'rgba(31,36,48,0.75)', '#fff'); },
  };
}
