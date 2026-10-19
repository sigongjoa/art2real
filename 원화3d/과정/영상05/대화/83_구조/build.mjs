// 83 편 쇼츠 카드 — 우리 구조를 드릴 프레스 깊이 멈춤으로: 1:1 앞 도면(선 높이) → 높이 게이지가 읽어 멈춤 막대에 너트(후보) → 핀 하나(모델 · 유일한 강조) → 주축이 그 깊이까지 깎음 → 오른쪽 펜이 앞에서 다시 그림 → 램프
// node build.mjs [출력 폴더] [--still f,f] → element-NNN.png 300 장(1000×700 투명) · 단계 60 프레임씩: ① 게이지 오름 ② 너트 셋 ③ 관통 깎기 ④ 다시 그림 · 빨강 ⑤ 바닥 너트 → 포켓 · 다시 그림 · 초록
import { mkdirSync, mkdtempSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { spawn } from "node:child_process"; import { tmpdir } from "node:os"; import { dirname, join } from "node:path"; import { fileURLToPath, pathToFileURL } from "node:url";
import * as k from "../anatomy_src/repo/kit/iso-kit.mjs"; import * as G from "../anatomy_src/repo/kit/lathe.mjs"; import { chromePort } from "../anatomy_src/repo/scripts/chrome-port.mjs";
const HERE = dirname(fileURLToPath(import.meta.url)); const OUT = process.argv[2] && !process.argv[2].startsWith("--") ? process.argv[2] : join(HERE, "frames"); mkdirSync(OUT, { recursive: true });
const STILL = process.argv.includes("--still") ? process.argv[process.argv.indexOf("--still") + 1].split(",").map(Number) : null;
// ── 참값(부품 59 컵 · 앞 도면 높이 그대로 1:1) ──
const BX = 8, BW = 36, ZB = 12, ZT = 46, RP = 11;               // 컵 일감: 가운데 x 8 · 폭 36 · 바닥 z 12 · 윗면 z 46 · 홈 반지름 11
const ZF = ZT - 0.5 * (ZT - ZB);                                  // 컵 바닥(정답 16/32 층 → 깊이 절반) z 32
const W = 1000, H = 700;
const PLX = -122, PLW = 56, PLY = 4, PF = PLY + 3.55;            // 왼쪽 앞 도면 판(x −122..−66) · 앞면 y = PF(보는 쪽 +y)
const CRX = 62, CRW = 56;                                         // 오른쪽 다시 그리는 판
const GX = -50, RX = -26, SPX = BX, GY = 9, RY = 0;                               // 높이 게이지 · 멈춤 막대 · 주축 x
const fitPts = [...k.boxCorners({ x: -150, y: -34, w: 300, d: 68, r: .3 }, -10, 0), [PLX, PLY, 74], [CRX + CRW, PLY, 90], [SPX, -34, 118], [SPX + 14, 14, 118]];
const P = k.fitProjection(fitPts, W, H, { pad: 18, azimuth: 66, elevation: 34 });
const S = (p, s) => k.solidSvg(p, s), L = (d, s) => k.lineSvg(d, s), D3 = (pts, c) => k.pathOf(pts.map((p) => k.iso(p, P)), c);
const ease = (a, b, f) => { const t = Math.min(1, Math.max(0, (f - a) / (b - a))); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;
const dash = (a, b, n = 9) => Array.from({ length: n }, (_, i) => { const t0 = i / n, t1 = (i + .55) / n; return D3([a.map((v, j) => lerp(v, b[j], t0)), a.map((v, j) => lerp(v, b[j], t1))]); }).join("");
// ── 바탕 ──
function base() {
  const plate = { x: -136, y: -36, w: 272, d: 70, r: 6 };
  let s = `<path class="iso-halo" d="${k.haloOf(plate, -10, 10, P)}"/>`;
  for (const [x, y] of [[-126, -28], [126, -28], [-126, 26], [126, 26]]) s += S(k.cylinder(x, y, 4, -14, 4, P, 18), { tone: "lo" });
  s += S(k.slabOf(plate, -10, 10, P, 6, 1.2), { tone: "mid" });
  s += L(k.planOutline(k.insetPlan(plate, 5), 0, P), { tone: "faint" });
  s += k.dotsSvg([[-130, -30], [130, -30], [-130, 28], [130, 28]].map(([x, y]) => k.iso([x, y, 0], P)), { size: .55, tone: "mid" });
  s += S(k.slabOf({ x: -120, y: 26, w: 240, d: 5, r: .3 }, 0, .6, P), { tone: "lo", flat: true });   // 앞 모서리 자 띠
  for (let x = -118; x <= 118; x += 4) s += L(D3([[x, 31, .6], [x, 31 - ((x + 118) % 20 === 0 ? 3.4 : 1.8), .6]]), { tone: (x + 118) % 20 === 0 ? "mid" : "lo" });
  s += S(k.slabOf({ x: -24, y: 18, w: 34, d: 9, r: 1 }, 0, .8, P), { tone: "mid", inner: [0, 1, 2].map((i) => L(D3([[-20, 20.5 + i * 2.2, .8], [i === 2 ? -4 : 6, 20.5 + i * 2.2, .8]]), { tone: "lo", free: true })).join("") });   // 이름판
  return s;
}
// 세운 판(도면 판) — 다리 둘 · 테 · 앞면 y = PLY
function board(x0, w, top) {
  let s = "";
  for (const x of [x0 + 6, x0 + w - 6]) s += S(k.slabOf({ x: x - 4, y: PLY - 2, w: 8, d: 12, r: 1 }, 0, 3, P), { tone: "lo" }) + S(k.slabOf({ x: x - 1.5, y: PLY + 1, w: 3, d: 3, r: .3 }, 3, 6, P), { tone: "mid" });
  s += S(k.slabOf({ x: x0, y: PLY, w, d: 3.5, r: .8 }, 8, top - 8, P, 4, .5), { tone: "hi" });
  s += L(D3([[x0 + 2.5, PF, 10.5], [x0 + w - 2.5, PF, 10.5], [x0 + w - 2.5, PF, top - 2.5], [x0 + 2.5, PF, top - 2.5]], true), { tone: "faint" });
  s += k.dotsSvg([[x0 + 4, PF, 12], [x0 + w - 4, PF, 12], [x0 + 4, PF, top - 4], [x0 + w - 4, PF, top - 4]].map((p) => k.iso(p, P)), { size: .45, tone: "mid" });
  return s;
}
// 컵 앞 그림 선분(그리는 순서): 바깥 네모 넷 · 홈 벽 점선 둘 · 바닥 점선(있으면)
function segsOf(x0, floor) {
  const cx = x0 + PLW / 2, hw = BW / 2, rp = RP, y = PF + .05, dz = floor ?? ZB;
  const s = [[[cx - hw, y, ZB], [cx + hw, y, ZB], 0], [[cx + hw, y, ZB], [cx + hw, y, ZT], 0], [[cx + hw, y, ZT], [cx - hw, y, ZT], 0], [[cx - hw, y, ZT], [cx - hw, y, ZB], 0], [[cx - rp, y, ZT], [cx - rp, y, dz], 1], [[cx + rp, y, ZT], [cx + rp, y, dz], 1]];
  if (floor != null) s.push([[cx - rp, y, floor], [cx + rp, y, floor], 1]);
  return s;
}
function frontDrawing(x0, floor, t = 1, tone = "hi") {
  const all = segsOf(x0, floor), n = all.length; let out = "";
  all.forEach(([a, b, d], i) => { const u = Math.min(1, Math.max(0, t * n - i)); if (u <= 0) return; const e = a.map((v, j) => lerp(v, b[j], u)); out += d ? L(dash(a, e, Math.max(2, Math.round(8 * u))), { tone }) : L(D3([a, e]), { tone }); });
  return `<g class="ink">${out}</g>`;
}
function penPoint(x0, floor, t) { const all = segsOf(x0, floor), n = all.length, i = Math.min(n - 1, Math.floor(t * n)), u = Math.min(1, t * n - i); return all[i][0].map((v, j) => lerp(v, all[i][1][j], u)); }
// 높이 게이지: 둥근 받침 · 기둥(눈금) · 미끄럼틀 · 판 쪽으로 뻗은 바늘
function gauge(z) {
  let s = S(k.cylinder(GX, GY, 9, 0, 5, P, 32, .6), { tone: "lo" }) + S(k.cylinder(GX, GY, 6.5, 5, 1.5, P, 28), { tone: "mid" });
  s += S(k.slabOf({ x: GX - 2.5, y: GY - 1.5, w: 5, d: 3, r: .3 }, 6.5, 74, P), { tone: "mid" });
  for (let zz = 10; zz <= 76; zz += 3) s += L(D3([[GX - 2.5, GY + 1.5, zz], [GX - 2.5 - ((zz - 10) % 15 === 0 ? 2.4 : 1.3), GY + 1.5, zz]]), { tone: (zz - 10) % 15 === 0 ? "mid" : "lo" });
  s += S(k.cylinder(GX, GY, 3.2, 80.5, 2, P, 20), { tone: "mid" });
  s += S(k.slabOf({ x: PLX + PLW + .5, y: GY - 1.2, w: GX - 4.5 - (PLX + PLW + .5), d: 2.4, r: .3 }, z - .9, 1.8, P), { tone: "hi" });
  s += S(k.slabOf({ x: GX - 4.5, y: GY - 3, w: 9, d: 6, r: .8 }, z - 3.5, 7, P, 4, .5), { tone: "mid" }) + S(k.cylinder(GX + 6.1, GY, 1.6, z - 1.2, 2.4, P, 16), { tone: "mid", inner: L(k.knurl(GX + 6.1, GY, 1.6, z - 1.2, z + 1.2, 10, P), { tone: "lo" }) });
  s += k.dotsSvg([k.iso([PLX + PLW + .5, GY, z], P)], { size: .9, tone: "hi" });
  return s;
}
// 멈춤 막대 · 너트(후보) · 핀(모델이 고른 것)
function stopRod(nuts, pick, pinOut) {
  let s = S(k.cylinder(RX, RY, 4.5, 0, 3, P, 24), { tone: "lo" }) + S(k.cylinder(RX, RY, 1.6, 3, 95, P, 16), { tone: "mid" });
  for (const [z, a] of nuts) if (a > 0) { const n = S(k.cylinder(RX, RY, 1.6 + 4.2 * a, z - 2.2, 4.4, P, 6), { tone: z === pick ? "hi" : "mid", crease: "lo", lit: z === pick }); s += z === pick ? `<g class="gold">${n}</g>` : n; }
  if (pick != null && pinOut > 0) s += `<g class="gold">${S(k.slabOf({ x: RX + 2.5, y: RY - .9, w: 9 * pinOut, d: 1.8, r: .6 }, pick - .9, 1.8, P), { tone: "hi", lit: true })}</g>`;
  return s;
}
// 일감(컵) — d = 깎인 깊이(0 = 안 깎음 · ZT−ZB = 관통) · cls = 색
function block(d, cls, rimId) {
  const pl = { x: BX - BW / 2, y: -BW / 2, w: BW, d: BW, r: 2 };
  let s = S(k.slabOf({ x: BX - 30, y: -16, w: 60, d: 32, r: 2 }, 0, 4, P, 6, .6), { tone: "lo" });   // 바이스 바닥
  for (const x of [BX - 30 + 6, BX + 30 - 6]) s += k.dotsSvg([k.iso([x, -12, 4], P), k.iso([x, 12, 4], P)], { size: .5, tone: "mid" });
  s += S(k.slabOf({ x: BX - BW / 2 - 9, y: -10, w: 7, d: 20, r: 1 }, 4, ZB + 8 - 4, P, 4, .5), { tone: "mid" });   // 뒷 턱(고정)
  s += S(k.slabOf({ x: BX - 14, y: -14, w: 28, d: 28, r: 2 }, 4, ZB - 4, P, 6, .6), { tone: "lo" });   // 받침
  s += S(k.slabOf({ x: BX + BW / 2 + 2, y: -10, w: 7, d: 20, r: 1 }, 4, ZB + 8 - 4, P, 4, .5), { tone: "mid" }) + S(k.slabOf({ x: BX + BW / 2 + 9, y: -1.5, w: 12, d: 3, r: .6 }, 9, 3, P), { tone: "mid" });   // 움직이는 턱 · 나사
  let w = S(k.slabOf(pl, ZB, ZT - ZB, P, 6, .8), { tone: "hi", crease: "lo" });
  if (d > .3) {
    const rim = k.ring(BX, 0, RP, ZT, P, 64), zf = ZT - d;
    w += `<path class="iso-shade" data-shade="0" d="${rim}"/><g clip-path="url(#${rimId})">`;
    if (zf > ZB + .2) w += `<path class="iso-shade" data-shade="3" d="${k.ring(BX, 0, RP, zf, P, 64)}"/>` + L(k.ring(BX, 0, RP, zf, P, 64), { tone: "lo" });
    w += `</g>` + L(rim, { tone: "hi" });
  }
  return s + `<g class="${cls}">${w}</g>`;
}
// 드릴 프레스 뒤쪽: 기둥 · 받침 · 머리 · 손잡이
function pressCol() {
  let s = S(k.slabOf({ x: SPX - 12, y: -34, w: 24, d: 14, r: 2 }, 0, 5, P, 6, .6), { tone: "lo" }) + S(k.cylinder(SPX, -27, 6, 5, 107, P, 28, .5), { tone: "mid" });
  return s;
}
function pressHead() {
  let s = ""; const hd = { x: SPX - 13, y: -34, w: 26, d: 46, r: 4 };
  s += S(k.slabOf(hd, 98, 18, P, 6, .8), { tone: "mid" }) + L(k.planOutline(k.insetPlan(hd, 3), 116, P), { tone: "faint" });
  s += S(k.cylinder(SPX, -40, 9, 116, 16, P, 30, .6), { tone: "mid", inner: k.fadedSvg(G.ribsOf(G.frameAlong([SPX, -40, 116], [0, 0, 1]), 2, 14, 9, 18, P, { fade: [.1, .6], seams: true }), { tone: "lo" }) });   // 모터
  s += S(k.cylinder(SPX + 16, -10, 3, 104, 6, P, 20), { tone: "mid", inner: L(k.knurl(SPX + 16, -10, 3, 104, 110, 14, P), { tone: "lo" }) });
  for (const a of [0, 2.1, 4.2]) { const ex = SPX + 19 + 13 * Math.cos(a) * .25, ey = -10 + 13 * Math.sin(a), ez = 107 + 13 * Math.cos(a) * .9;
    s += L(D3([[SPX + 19, -10, 107], [ex, ey, ez]]), { tone: "mid" }) + S(k.cylinder(ex, ey, 1.6, ez - 1.6, 3.2, P, 14), { tone: "lo" }); }   // 이송 손잡이 세 가지
  return s;
}
// 주축 · 날(끝 z = tip) · 끝 높이 팔(멈춤 막대의 핀에 닿음)
function spindle(tip, rimId) {
  const top = 99, q = Math.max(tip + 10, ZT + 1); let s = q < top ? S(k.cylinder(SPX, 0, 7, q, top - q, P, 28, .4), { tone: "mid" }) : "";
  const below = tip < ZT ? `<g clip-path="url(#${rimId})">${S(k.cylinder(SPX, 0, RP - .6, tip, Math.min(10, ZT - tip), P, 32), { tone: "hi" })}</g>` : "";
  const above = tip + 10 > ZT ? S(k.cylinder(SPX, 0, RP - .6, Math.max(tip, ZT), tip + 10 - Math.max(tip, ZT), P, 32), { tone: "hi" }) : "";
  s += `<g class="gold">${below}${above}</g>`;
  // 깊이 손가락: 깃(날 끝 + 40) → 일감 위를 건너 → 일감 왼쪽 바깥으로 내려와 → 발이 멈춤 막대 쪽(끝 높이 = 날 끝)
  const zt = Math.max(tip, ZB), FX = BX - BW / 2 - 5, zc = zt + 40;
  s += S(k.cylinder(SPX, 0, 8.5, zc - 2, 4, P, 28, .4), { tone: "mid" });
  s += S(k.slabOf({ x: FX - 1.2, y: -1.2, w: SPX - 8 - FX + 1.2, d: 2.4, r: .3 }, zc - 1.2, 2.4, P), { tone: "mid" });
  s += S(k.cylinder(FX, 0, 1.3, zt, zc - zt, P, 14), { tone: "mid" });
  s += S(k.slabOf({ x: RX + 1.8, y: -1, w: FX - RX - 1.8, d: 2, r: .3 }, zt - .2, 1.6, P), { tone: "hi" });
  return s;
}
// 램프(다시 그리는 판 위) — 색 cls
function lamp(cls) {
  const x = CRX + CRW / 2; let s = S(k.cylinder(x, PLY + 1.7, 5.5, 74, 3, P, 24), { tone: "mid" });
  const F = G.frameAlong([x, PLY + 1.7, 77], [0, 0, 1]);
  return s + `<g class="${cls ? "lamp" + cls : ""}">${S(G.solidOf([[0, 7, 1], [5, 7.4, 1], [10, 5.2, 1], [12.4, .6, 1]], F, P), { tone: "hi" })}</g>`;
}
// 펜 수레: 판 오른쪽 레일 · 펜 끝 = 지금 그리는 점
function pen([x, , z]) {
  const rx = CRX + CRW + 5; let s = S(k.slabOf({ x: rx - 1.5, y: PF - 1, w: 3, d: 3, r: .3 }, 0, 74, P), { tone: "mid" });
  s += S(k.slabOf({ x: rx - 3.5, y: PF, w: 7, d: 6, r: .6 }, z - 3, 6, P, 4, .4), { tone: "mid" });
  if (rx - 3.5 - x > .5) s += S(k.slabOf({ x, y: PF + 2.5, w: rx - 3.5 - x, d: 1.6 }, z - .5, 1, P), { tone: "mid" });
  return s + `<g class="gold">${S(k.cylinder(x, PF + 1.2, 1.2, z - 2, 4, P, 12), { tone: "hi" })}</g>`;
}
// ── 장면(f = 0..299) ──
function scene(f) {
  const gz = f < 60 ? lerp(4, ZT, ease(5, 45, f)) : f < 120 ? (f < 86 ? lerp(ZT, ZF, ease(62, 80, f)) : lerp(ZF, ZB, ease(92, 110, f))) : ZB;
  const nuts = [[ZT, ease(48, 58, f)], [ZF, ease(80, 88, f)], [ZB, ease(110, 118, f)]];
  const pick = f < 120 ? null : f < 245 ? ZB : ZF;
  const pinOut = f < 120 ? 0 : f < 240 ? ease(120, 130, f) : f < 245 ? 1 - ease(240, 245, f) : ease(246, 254, f);
  let tip = 56, d = 0, cls = "";
  if (f >= 130 && f < 240) { tip = f < 230 ? lerp(56, ZB, ease(130, 170, f)) : lerp(ZB, 56, ease(230, 240, f)); d = f < 230 ? Math.max(0, ZT - tip) : ZT - ZB; cls = f >= 168 ? "bad" : ""; }
  if (f >= 250) { tip = lerp(56, ZF, ease(254, 278, f)); d = Math.max(0, ZT - tip); cls = f >= 276 ? "good" : ""; }
  const floorOnCard = f >= 240 ? ZF : null, cardT = f < 180 ? 0 : f < 240 ? ease(180, 224, f) : ease(278, 294, f);
  const lampCls = f >= 226 && f < 240 ? "bad" : f >= 294 ? "good" : "";
  const rimId = "rim" + f;
  return [`<defs><clipPath id="${rimId}"><path d="${k.ring(BX, 0, RP, ZT, P, 64)}"/></clipPath></defs>`, base(), pressCol(), board(PLX, PLW, 74), frontDrawing(PLX, ZF, 1, f < 120 ? "hi" : "mid"),
    gauge(gz), stopRod(nuts, pick, pinOut), board(CRX, CRW, 74), frontDrawing(CRX, floorOnCard, cardT, "hi"),
    block(d, cls, rimId), spindle(tip, rimId), pressHead(), lamp(lampCls), pen(cardT > 0 && cardT < 1 ? penPoint(CRX, floorOnCard, cardT) : [CRX + CRW + 1, 0, 40])].join("");
}
const css = `.gold{--anatomy-paper:#f3d68f;--anatomy-face:#f3d68f;--anatomy-top:#f6dc9c;--anatomy-lit-top:#f6dc9c;--anatomy-shade-0:#c48f1c;--anatomy-shade-1:#d39d26;--anatomy-shade-2:#dcab3a;--anatomy-shade-3:#e8bf5c;--anatomy-mid:#8a5c06;--anatomy-hi:#6b4704;--anatomy-lo:#b88420;--anatomy-faint:#c99a3a}
.ink path{stroke-width:2.2px}
.lampbad{--anatomy-paper:rgb(225,70,70);--anatomy-face:rgb(225,70,70);--anatomy-top:rgb(240,110,110);--anatomy-shade-0:rgb(170,30,30);--anatomy-shade-1:rgb(195,45,45);--anatomy-shade-2:rgb(215,60,60);--anatomy-shade-3:rgb(235,95,95);--anatomy-hi:rgb(140,20,20)}
.lampgood{--anatomy-paper:rgb(60,180,95);--anatomy-face:rgb(60,180,95);--anatomy-top:rgb(110,205,135);--anatomy-shade-0:rgb(25,120,55);--anatomy-shade-1:rgb(35,140,65);--anatomy-shade-2:rgb(45,160,80);--anatomy-shade-3:rgb(85,195,115);--anatomy-hi:rgb(20,100,45)}
.bad{--anatomy-paper:#f6d4d4;--anatomy-face:#f6d4d4;--anatomy-top:#f9dede;--anatomy-lit-top:#f9dede;--anatomy-shade-0:#e08a8a;--anatomy-shade-1:#e89c9c;--anatomy-shade-2:#efb0b0;--anatomy-shade-3:#f5c6c6;--anatomy-hi:rgb(220,50,50);--anatomy-lo:rgb(220,50,50)}
.good{--anatomy-paper:#d3ecd9;--anatomy-face:#d3ecd9;--anatomy-top:#e3f3e7;--anatomy-lit-top:#e3f3e7;--anatomy-shade-0:#7fbf91;--anatomy-shade-1:#92caa1;--anatomy-shade-2:#a8d6b4;--anatomy-shade-3:#c0e2c8;--anatomy-hi:rgb(40,160,80);--anatomy-lo:rgb(40,160,80)}`;
const frames = STILL ?? Array.from({ length: 300 }, (_, i) => i);
const blocks = frames.map((f) => `<div class="shot iso" data-theme="light" data-file="element-${String(f).padStart(3, "0")}.png">${k.figureSvg({ width: W, height: H, label: "구조 " + f, body: scene(f) })}</div>`);
writeFileSync(join(HERE, "index.html"), `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${k.ISO_CSS}${css}
html,body{margin:0;background:transparent}.shot{width:1000px;height:700px;background:transparent!important}.shot svg{width:1000px;height:700px;display:block}</style></head><body>${blocks.join("")}</body></html>`);
const chrome = [join(process.env.LOCALAPPDATA || "", "Google\\Chrome\\Application\\chrome.exe"), "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"].find((p) => existsSync(p));
const profile = mkdtempSync(join(tmpdir(), "a83-")); const proc = spawn(chrome, ["--headless=new", "--do-not-de-elevate", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run", "--hide-scrollbars", "--allow-file-access-from-files", "about:blank"]);
const port = await chromePort(proc, profile); const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl); let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } }; await new Promise((r) => (ws.onopen = r));
const send = (method, params = {}) => new Promise((r) => { const c = ++id; pending.set(c, r); ws.send(JSON.stringify({ id: c, method, params })); });
await send("Page.enable"); await send("Emulation.setDeviceMetricsOverride", { width: 1000, height: 700, deviceScaleFactor: 1, mobile: false }); await send("Emulation.setDefaultBackgroundColorOverride", { color: { r: 0, g: 0, b: 0, a: 0 } });
await send("Page.navigate", { url: pathToFileURL(join(HERE, "index.html")).href }); await new Promise((r) => setTimeout(r, 4000));
const boxes = JSON.parse((await send("Runtime.evaluate", { expression: `JSON.stringify([...document.querySelectorAll(".shot")].map(e=>{const r=e.getBoundingClientRect();return {f:e.dataset.file,y:r.top+scrollY}}))`, returnByValue: true })).result.result.value);
for (const b of boxes) { const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: b.y, width: 1000, height: 700, scale: 1 } }); writeFileSync(join(OUT, b.f), Buffer.from(shot.result.data, "base64")); }
console.log("saved", boxes.length, OUT); proc.kill("SIGKILL"); try { rmSync(profile, { recursive: true, force: true }); } catch {}
