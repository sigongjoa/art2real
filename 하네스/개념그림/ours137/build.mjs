// 우리 모델(판 137 · 선지도 cnn · 합침 "전부") — 체 네 겹 + 혼합 콘솔: 화소 하나의 판정 = 넓이가 다른 네 층의 가중합
// 근거(이 그림이 쓰는 사실만):
//   하네스/과제선지도.py 망(): 시점마다 128×128 도면(3 시점) · CNN 블록 4 개(3×3 보폭 2 + 3×3 보폭 1 · GroupNorm · GELU)
//     채널 32/64/128/256 · 해상도 64/32/16/8 · 합침 "전부": 블록 2·3·4 를 64×64 로 nearest 확대해 블록 1 과 이어 붙임(480 채널)
//     → 1×1 conv 머리 하나 → pixel shuffle ×2 → 화소마다 종류 {없음 · 직선 · 곡선 · 곡면테} + 숨음 + 꼭짓점 열지도
//   하네스/계산과정그림.py 수용: 칸 하나가 보는 입력 폭 7 / 19 / 43 / 91 px (체의 창 크기) · 칸 간격 = 보폭 누적 2/4/8/16 px (체의 눈 간격)
//   하네스/판/137전부합침/판정.json: 선 자리 0.999 · 직선 0.78 · 곡선 0.76 · 곡선 옆 직선 오류 0.24 · 꼭짓점 F1 0.51
//   out/하네스/137전부합침 겹침 진단: 직선과 곡선이 2 px 안에 나란하면 틀림 0.39 · 직선끼리 0.07 · 곡선끼리 0.08
//   층별 미는 방향 · 세기(페이더 위치)는 설명용 정성 값이다(기록된 숫자 아님).
// 그림 요소: 정답 카드(같은 도면 · 선마다 정답 종류 색) · 단계 번호판 ①~⑦ · 끝에 모델 도장과 정답을 겹쳐 대조
// 움직임: 탐침 수레가 도면 위 화소로 가면 체 네 겹이 그 둘레를 보고, 앞 콘솔의 페이더 넷이 직선(파랑) · 곡선(초록) 쪽으로 밀리며
//   그 합이 바늘을 돌리고, 탐침이 종이에 판정 색을 찍는다 = 1×1 머리가 네 층 특징을 가중합해 화소 하나를 판정한다.
// 사용: node build.mjs [--light] → ours137.html / ours137-light.html
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

// 세계 단위 1 = 입력 1 px
const PLATE = { x: -182, y: -104, w: 324, d: 256, r: 10 };
const PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -140, y: -56, w: 128, d: 128, r: 1.5 };   // 128×128 도면 한 장
const ST = 0.8;
const LINE_Y = -14, LINE_X = [-134, -18];                     // 곧은 선
const ARC = { cx: -46, cy: 20, r: 32, a0: 205, a1: 335 };     // 호: 가장 낮은 점이 직선 위 2 px
const PA = [-124, LINE_Y], PB = [-46, LINE_Y];                // 탐침 자리: A 곡선에서 멂 · B 곡선 2 px 옆
const LAYERS = [ // 창 = 수용 폭 · 눈 = 칸 간격 · 높이 · 테 두께
  { win: 7, pitch: 2, z: 8, t: 1.2, h: 1.4 },
  { win: 19, pitch: 4, z: 13, t: 1.8, h: 1.8 },
  { win: 43, pitch: 8, z: 18, t: 2.4, h: 2.2 },
  { win: 91, pitch: 16, z: 23, t: 3, h: 2.6 },
];
const RAIL_Y = -84, MAST_R = 3, MAST_TOP = 29;
// 콘솔(오른쪽): 페이더 넷 + 저울 바늘판
const DESK = { x: 8, y: -92, w: 124, d: 164, r: 6 };
const DESK_H = 8;
const FADER_X = 70, TRAVEL = 30;
const FADER_Y = [56, 38, 20, 2];                          // 층 1(앞) → 층 4(뒤)
const DIAL = { x: 70, y: -50, R: 24 };
const DIAL_TOP = DESK_H + 6;
// 정답 카드(도면 왼쪽 앞): 같은 도면을 0.42 배로 · 선마다 정답 종류 색(직선 파랑 · 곡선 초록) = 하네스 정답.png 와 같은 뜻
const CS = 0.42, CARD = { x: -130, y: 88, w: 128 * CS, d: 128 * CS, r: 1 };
const HOLD = { x: CARD.x - 4, y: CARD.y - 4, w: CARD.w + 8, d: CARD.d + 15, r: 2 };
const cardPt = ([x, y]) => [CARD.x + (x - SHEET.x) * CS, CARD.y + (y - SHEET.y) * CS];
// 단계 번호판(콘솔 앞): ① 입력 ② 블록1 ③ 블록2 ④ 블록3 ⑤ 블록4 ⑥ 합쳐 판정 ⑦ 도장
const KEYS = { x: 8, y: 84, w: 124, d: 20, r: 2 }, KEY_W = 13;

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [PA[0], RAIL_Y, MAST_TOP + 2], [PB[0] + 45, LINE_Y + 45, 40]], WIDTH, HEIGHT, { pad: 30, azimuth: 38, elevation: 42 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const depth = (x, y, z = 0) => k.depthOf([x, y, z], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth(a[0], a[1]) - depth(b[0], b[1]));
const arcPts = (z, a0 = ARC.a0, a1 = ARC.a1) => Array.from({ length: 41 }, (_, i) => { const a = (a0 + (a1 - a0) * i / 40) * Math.PI / 180; return [ARC.cx + ARC.r * Math.cos(a), ARC.cy + ARC.r * Math.sin(a), z]; });

function base() {
  const o = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
    o.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    o.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  o.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  o.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  o.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  o.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // 앞 자(종이 아래) — 눈금은 자 가장자리에서 · 4 px 간격, 5 칸마다 큰 눈금
  const strip = { x: SHEET.x, y: SHEET.y - 14, w: SHEET.w, d: 7, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + strip.d - 0.8, 0.6, [-2, -3.6], P);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  // 왼쪽 자(세로)
  const side = { x: SHEET.x - 14, y: SHEET.y, w: 7, d: SHEET.d, r: 1 };
  o.push(S(k.slabOf(side, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const s2 = k.topTicks(side.y + 4, side.y + side.d - 4, 4, 5, side.x + side.w - 0.8, 0.6, [-2, -3.6], P, "y");
  if (s2 && s2.minor) o.push(L(s2.minor, { tone: "lo" }), L(s2.major, { tone: "mid" }));
  // 이름판(콘솔 앞) — 세 줄은 인쇄 글자
  const plate = { x: 30, y: PLATE.y + PLATE.d - 18, w: 44, d: 10, r: 1.2 };
  o.push(S(k.slabOf(plate, 0, 0.8, P, 4), { tone: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(plate, 1.6), 0.8, P), { tone: "faint" }));
  [[5, 30], [5, 22], [5, 26]].forEach(([dx, len], i) => o.push(L(k.lineOnTop([plate.x + dx, plate.y + 2.6 + i * 2.4], [plate.x + dx + len, plate.y + 2.6 + i * 2.4], 0.8, P), { tone: "lo", free: true })));
  o.push(D([at([plate.x + 2.4, plate.y + plate.d / 2, 0.8]), at([plate.x + plate.w - 2.4, plate.y + plate.d / 2, 0.8])], { size: 0.45 }));
  return o.join("");
}
function sheet() {   // 종이 + 도면(곧은 선 · 호) + 찍힌 판정 자국
  const o = [S(k.slabOf(SHEET, 0, ST, P, 4), { tone: "hi", crease: "lo" })];
  o.push(D(k.corners(SHEET, 3).map(([x, y]) => at([x, y, ST])), { size: 0.45 }));
  o.push(`<g class="ink">${L(k.lineOnTop([LINE_X[0], LINE_Y], [LINE_X[1], LINE_Y], ST, P), { tone: "hi", free: true })}${L(k.pathOf(arcPts(ST).map(at)), { tone: "hi", free: true })}</g>`);
  for (const [name, [x, y]] of [["a", PA], ["b", PB]]) o.push(`<g data-mark="${name}" style="opacity:0"><path class="mark-fill" d="${k.ring(x, y, 4.4, ST, P, 32)}"/><path class="iso-line" data-tone="hi" d="${k.ring(x, y, 4.4, ST, P, 32)}"/></g>`);
  return o.join("");
}
function rail() {   // 뒤 레일 + 끝 멈춤쇠
  const r = { x: -152, y: RAIL_Y - 5, w: 136, d: 10, r: 2 };
  const o = [S(k.slabOf(r, 0, 4, P, 4, 0.5), { tone: "mid" })];
  o.push(L(k.lineOnTop([r.x + 6, RAIL_Y], [r.x + r.w - 6, RAIL_Y], 4, P), { tone: "faint" }));
  for (const x of [r.x - 2, r.x + r.w - 4]) {
    o.push(S(k.slabOf({ x, y: RAIL_Y - 7, w: 6, d: 14, r: 1.2 }, 0, 8, P, 3, 0.5), { tone: "mid" }));
    o.push(D([at([x + 3, RAIL_Y - 4, 8]), at([x + 3, RAIL_Y + 4, 8])], { size: 0.45 }));
  }
  return o.join("");
}
// 체 하나(층 k): 창 = 수용 폭 · 그물 간격 = 칸 간격 · 테 네 변을 깊이 순으로, 그물은 먼 두 변 뒤
function sieve(L_, cx, cy, n) {
  const { win: W, pitch, z, t, h } = L_, a = W / 2;
  const bars = [
    { x: cx - a - t, y: cy + a, w: W + 2 * t, d: t },
    { x: cx - a - t, y: cy - a - t, w: W + 2 * t, d: t },
    { x: cx - a - t, y: cy - a, w: t, d: W },
    { x: cx + a, y: cy - a, w: t, d: W },
  ].map((b) => ({ ...b, r: Math.min(0.6, t / 3), dep: depth(b.x + b.w / 2, b.y + b.d / 2, z) })).sort((p, q) => p.dep - q.dep);
  const mesh = [];
  for (let u = -Math.floor(a / pitch) * pitch; u <= a + 1e-6; u += pitch) {
    mesh.push(k.lineOnTop([cx + u, cy - a], [cx + u, cy + a], z + h, P), k.lineOnTop([cx - a, cy + u], [cx + a, cy + u], z + h, P));
  }
  const bar = (b) => S(k.slabOf(b, z, h, P, 3, 0.3), { tone: "mid" });
  const near = bars[3];   // 가장 앞 변 위 층 번호 점(k 개)
  const ix = near.w > near.d ? Array.from({ length: n }, (_, i) => at([cx - (n - 1) * 1.6 + i * 3.2, near.y + near.d / 2, z + h])) : Array.from({ length: n }, (_, i) => at([near.x + near.w / 2, cy - (n - 1) * 1.6 + i * 3.2, z + h]));
  return [bar(bars[0]), bar(bars[1]), L(mesh.join(""), { tone: n === 1 ? "mid" : "lo" }), bar(bars[2]), bar(bars[3]), D(ix, { size: 0.42, tone: "hi" })].join("");
}
function carriage() {   // A 자리에 짓고 수레째 옮김
  const [cx, cy] = PA;
  const o = [];
  o.push(S(k.slabOf({ x: cx - 9, y: RAIL_Y - 7, w: 18, d: 14, r: 2 }, 4, 6, P, 4, 0.6), { tone: "mid" }));
  o.push(D(k.corners({ x: cx - 9, y: RAIL_Y - 7, w: 18, d: 14 }, 2.4).map(([x, y]) => at([x, y, 10])), { size: 0.42 }));
  o.push(S(k.cylinder(cx, RAIL_Y, 4.6, 10, 2.4, P, 28), { tone: "lo" }));
  o.push(S(k.cylinder(cx, RAIL_Y, MAST_R, 12.4, MAST_TOP - 12.4, P, 28), { tone: "mid", crease: "none", inner: L(LAYERS.map((l) => k.sideArc(cx, RAIL_Y, MAST_R, l.z - 1.2, P, 16)).join(""), { tone: "faint" }) }));
  o.push(S(k.cylinder(cx, RAIL_Y, 3.8, MAST_TOP, 1.6, P, 24, 0.3), { tone: "mid" }));
  // 발자국(종이 위 창 그림자) — 종이 밖은 잘림
  const foot = LAYERS.map((l, i) => `<path data-foot="${i}" class="iso-line foot" d="${k.planOutline({ x: cx - l.win / 2, y: cy - l.win / 2, w: l.win, d: l.win, r: 0.6 }, ST + 0.05, P, 3)}"/>`).join("");
  // 탐침(찍개) 아래 토막 — 체 1 아래
  const needleLo = `<g data-part="needle">${S(k.cylinder(cx, cy, 1.5, 2.2, 1.6, P, 20, 0.3), { tone: "hi", lit: true })}${S(k.cylinder(cx, cy, 0.7, 3.8, LAYERS[0].z - 3.8, P, 14), { tone: "mid", crease: "none" })}</g>`;
  const needleHi = `<g data-part="needle">${S(k.cylinder(cx, cy, 0.7, LAYERS[0].z + LAYERS[0].h, 3.2, P, 14), { tone: "mid", crease: "none" })}${S(k.cylinder(cx, cy, 1.6, LAYERS[0].z + LAYERS[0].h + 3.2, 1.4, P, 20, 0.3), { tone: "mid" })}</g>`;
  const tiers = LAYERS.map((l, i) => {
    const y0 = RAIL_Y + MAST_R - 0.4, arm = { x: cx - 1.6, y: y0, w: 3.2, d: cy - l.win / 2 - l.t - y0, r: 0.6 };
    return `<g data-sieve="${i}">${S(k.slabOf(arm, l.z, l.h, P, 3, 0.3), { tone: "mid" })}${sieve(l, cx, cy, i + 1)}</g>`;
  });
  o.push(`<g clip-path="url(#sheet-clip)"><g data-part="feet">${foot}</g></g>`);
  o.push(needleLo, tiers[0], needleHi, ...tiers.slice(1));
  return o.join("");
}
function desk() {   // 혼합 콘솔: 페이더 넷(층 1~4) + 바늘판
  const o = [S(k.slabOf(DESK, 0, DESK_H, P, 6, 0.8), { tone: "mid", inner: L(k.sideSeam(DESK, 3, P, 6), { tone: "faint" }) })];
  o.push(L(k.planOutline(k.insetPlan(DESK, 4), DESK_H, P, 6), { tone: "faint" }));
  o.push(D(k.corners(DESK, 3.2).map(([x, y]) => at([x, y, DESK_H])), { size: 0.45 }));
  // 바늘판(뒤)
  const { x, y, R } = DIAL;
  o.push(S(k.cylinder(x, y, R + 2, DESK_H, 2, P, 64, 0.4), { tone: "lo" }));
  o.push(S(k.cylinder(x, y, R, DESK_H + 2, 4, P, 64, 0.6), { tone: "hi", crease: "lo" }));
  o.push(L(k.ring(x, y, R - 2.2, DIAL_TOP, P, 64), { tone: "lo" }));
  const t = k.radialTicks(x, y, R - 2.2, 24, 4, DIAL_TOP, [1.4, 2.8], P, Math.PI * 255 / 180, Math.PI * 2 / 3);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  const band = (a0, a1, cls) => `<path class="iso-line ${cls}" d="${k.onTop(Array.from({ length: 21 }, (_, i) => { const a = (a0 + (a1 - a0) * i / 20) * Math.PI / 180; return [x + (R - 2.2) * Math.cos(a), y + (R - 2.2) * Math.sin(a)]; }), DIAL_TOP, P)}"/>`;
  o.push(band(165, 225, "band-straight"), band(225, 285, "band-curve"));
  { const c = Math.SQRT1_2; o.push(L(k.lineOnTop([x - c * (R - 2.2), y - c * (R - 2.2)], [x - c * (R - 6.6), y - c * (R - 6.6)], DIAL_TOP, P), { tone: "hi" })); }
  o.push(`<path data-part="dial-needle" class="iso-line" data-tone="lit" data-free="end" style="stroke-width:1.1" d=""/>`);
  o.push(S(k.cylinder(x, y, 1.8, DIAL_TOP, 1, P, 20, 0.2), { tone: "mid" }));
  // 페이더(뒤 → 앞)
  [...FADER_Y.map((fy, i) => [fy, i])].reverse().forEach(([fy, i]) => {
    const slot = { x: FADER_X - TRAVEL - 6, y: fy - 1.4, w: 2 * TRAVEL + 12, d: 2.8, r: 1.4 };
    o.push(L(k.planOutline(slot, DESK_H, P, 4), { tone: "lo" }));
    o.push(S(k.slabOf({ x: slot.x - 10, y: fy - 3, w: 7, d: 6, r: 1 }, DESK_H, 0.6, P, 3), { tone: "lo", className: "pad-straight", crease: "none" }));
    o.push(S(k.slabOf({ x: slot.x + slot.w + 3, y: fy - 3, w: 7, d: 6, r: 1 }, DESK_H, 0.6, P, 3), { tone: "lo", className: "pad-curve", crease: "none" }));
    const tk = k.topTicks(FADER_X - TRAVEL, FADER_X + TRAVEL, TRAVEL / 4, 4, fy - 1.4, DESK_H, [-1.2, -2.4], P);
    if (tk && tk.minor) o.push(L(tk.minor, { tone: "faint" }), L(tk.major, { tone: "lo" }));
    const kb = { x: FADER_X - 4, y: fy - 4.5, w: 8, d: 9, r: 1.4 };
    const dots = Array.from({ length: i + 1 }, (_, q) => at([FADER_X, fy - i * 1.4 + q * 2.8, DESK_H + 6]));
    o.push(`<g data-fader="${i}">${S(k.slabOf({ x: FADER_X - 1.2, y: fy - 1, w: 2.4, d: 2, r: 0.4 }, DESK_H, 1.6, P, 2), { tone: "lo" })}${S(k.slabOf(kb, DESK_H + 1.6, 4.4, P, 3, 0.5), { tone: "hi" })}${D(dots, { size: 0.42, tone: "hi" })}</g>`);
  });
  return o.join("");
}

function answer() {   // 정답 카드: 받침 + 카드 + 정답 색 선 + 대조 고리(맞음 검정 · 틀림 빨강 ×)
  const o = [S(k.slabOf(HOLD, 0, 2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(HOLD, 2).map(([x, y]) => at([x, y, 2])), { size: 0.42 }));
  o.push(k.faceTextSvg(k.topMatrix([HOLD.x + HOLD.w / 2, HOLD.y + HOLD.d - 3.2], 2, P, "x"), "정답", { size: 6, tone: "mid", anchor: "middle" }));
  o.push(S(k.slabOf(CARD, 2, 0.8, P, 4), { tone: "hi", crease: "lo" }));
  const z = 2.8, a = arcPts(z).map(([x, y]) => [...cardPt([x, y]), z]);
  o.push(`<g class="truth">${L(k.lineOnTop(cardPt([LINE_X[0], LINE_Y]), cardPt([LINE_X[1], LINE_Y]), z, P), { tone: "hi", free: true, className: "truth-straight" })}${L(k.pathOf(a.map(at)), { tone: "hi", free: true, className: "truth-curve" })}</g>`);
  for (const [name, p, ok] of [["a", PA, true], ["b", PB, false]]) {
    const [x, y] = cardPt(p);
    const cross = ok ? "" : L(k.lineOnTop([x + 3, y - 3], [x + 6, y - 6], z, P) + k.lineOnTop([x + 3, y - 6], [x + 6, y - 3], z, P), { className: "check-x", free: true });
    o.push(`<g data-check="${name}" style="opacity:0"><path class="check-dot ${ok ? "dot-straight" : "dot-curve"}" d="${k.ring(x, y, 2.2, z, P, 20)}"/><path class="iso-line ${ok ? "check-ok" : "check-no"}" d="${k.ring(x, y, 3.2, z, P, 28)}"/>${cross}</g>`);
  }
  return o.join("");
}
function steps() {   // 단계 번호판: 건반 일곱 · 지금 단계가 켜짐
  const o = [S(k.slabOf(KEYS, 0, 1.2, P, 4, 0.4), { tone: "lo" })];
  o.push(D([at([KEYS.x + 2.2, KEYS.y + KEYS.d / 2, 1.2]), at([KEYS.x + KEYS.w - 2.2, KEYS.y + KEYS.d / 2, 1.2])], { size: 0.42 }));
  const gap = (KEYS.w - 8 - 7 * KEY_W) / 6;
  for (let i = 0; i < 7; i++) {
    const kp = { x: KEYS.x + 4 + i * (KEY_W + gap), y: KEYS.y + 3.5, w: KEY_W, d: 13, r: 1.4 };
    o.push(`<g data-step="${i}">${S(k.slabOf(kp, 1.2, 2.6, P, 3, 0.5), { tone: "mid" })}${k.faceTextSvg(k.topMatrix([kp.x + kp.w / 2, kp.y + kp.d / 2 + 2.6], 3.8, P, "x"), String(i + 1), { size: 7, tone: "mid", anchor: "middle" })}</g>`);
  }
  return o.join("");
}
const clip = `<defs><clipPath id="sheet-clip"><path d="${k.slabOf(SHEET, 0, ST, P, 4).top}"/></clipPath></defs>`;
const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "우리 모델 판 137 을 체 네 겹과 혼합 콘솔로 그린 그림. 탐침 위에 창 7, 19, 43, 91 px 의 체가 겹쳐 있고, 각 체가 콘솔 페이더를 직선 또는 곡선 쪽으로 민다. 페이더 합이 바늘을 돌리고 탐침이 판정 색을 종이에 찍는다. 곡선 옆 직선에서는 넓은 체 셋이 곡선 쪽으로 밀어 곡선으로 찍힌다.",
  body: [clip, base(), answer(), sheet(), rail(), `<g data-part="carriage">${carriage()}</g>`, desk(), steps()],
});

const live = `
const P = ${JSON.stringify(P)};
const PA = ${JSON.stringify(PA)}, PB = ${JSON.stringify(PB)}, DIAL = ${JSON.stringify(DIAL)}, DIAL_TOP = ${DIAL_TOP}, TRAVEL = ${TRAVEL}, WIN = ${JSON.stringify(LAYERS.map((l) => l.win))};
// 층별 미는 방향(−1 직선 … +1 곡선) — 정성 값 · A: 넷 다 직선 쪽 · B: 층 1 만 직선, 넓은 층 2~4 는 곡선
const PUSH = { a: [-0.9, -0.7, -0.5, -0.3], b: [-0.8, 0.5, 0.8, 0.9] };
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const car = svg.querySelector('[data-part="carriage"]'), needles = [...svg.querySelectorAll('[data-part="needle"]')];
const faders = [...svg.querySelectorAll("[data-fader]")].sort((a, b) => a.dataset.fader - b.dataset.fader);
const sieves = [...svg.querySelectorAll("[data-sieve]")], feet = [...svg.querySelectorAll("[data-foot]")];
const dialNeedle = svg.querySelector('[data-part="dial-needle"]'), marks = { a: svg.querySelector('[data-mark="a"]'), b: svg.querySelector('[data-mark="b"]') };
const checks = { a: svg.querySelector('[data-check="a"]'), b: svg.querySelector('[data-check="b"]') }, keys = [...svg.querySelectorAll("[data-step]")].sort((a, b) => a.dataset.step - b.dataset.step);
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const NAME = ["층 1 · 창 7 px", "층 2 · 창 19 px", "층 3 · 창 43 px", "층 4 · 창 91 px"];
// 시간표(초): 한 자리 = 머묾 1.2 → 페이더 넷 0.9 씩 → 찍기 1.4 → 머묾 · 이동 2.2
const T0 = 1.0, TF = 0.8, SPOT = T0 + 4 * TF + 0.8 + 0.8 + 1.4, MOVE = 2.2, BACK = 3.6, LOOP = 2 * SPOT + MOVE + BACK;   // 돌아갈 때 B 의 초록 자국을 드러내 보임
function phase(t) {
  if (t < SPOT) return { spot: "a", s: t, x: PA[0] };
  if (t < SPOT + MOVE) return { spot: null, u: ease((t - SPOT) / MOVE), from: "a" };
  if (t < 2 * SPOT + MOVE) return { spot: "b", s: t - SPOT - MOVE };
  const r = t - 2 * SPOT - MOVE; return { spot: null, u: ease(r / MOVE), from: "b", fade: ease((r - BACK + 0.9) / 0.9) };
}
let lastMarks = { a: 0, b: 0 };
function draw(t) {
  const ph = phase(t);
  let cx, f = [0, 0, 0, 0], active = -1, tap = 0, txt = "", step = -1;
  if (ph.spot) {
    cx = ph.spot === "a" ? PA[0] : PB[0];
    const s = ph.s, push = PUSH[ph.spot];
    for (let i = 0; i < 4; i++) { const u = ease((s - T0 - i * TF) / 0.6); f[i] = push[i] * u; if (s >= T0 + i * TF && s < T0 + (i + 1) * TF) active = i; }
    const ts = s - T0 - 4 * TF - 0.8, tc = ts - 0.8, isA = ph.spot === "a";
    tap = ts > 0 && ts < 0.8 ? Math.sin(Math.PI * ts / 0.8) : 0;
    if (ts > 0.4) marks[ph.spot].style.opacity = 1;
    if (tc > 0) checks[ph.spot].style.opacity = tc < 0.9 ? 0.35 + 0.65 * Math.abs(Math.cos(Math.PI * tc / 0.3)) : 1;
    if (s < T0) { step = 0; txt = isA ? "① 입력: 도면에서 곧은 선 위 화소 하나를 고른다" : "① 입력: 이번엔 곡선이 2 px 옆에 붙은 곧은 선 화소"; }
    else if (active >= 0) { step = active + 1; txt = "②③④⑤"[active] + " 블록 " + (active + 1) + ": 둘레 " + WIN[active] + " px 를 보고 「" + (push[active] < 0 ? "직선" : "곡선") + " 같다」고 민다"; }
    else if (ts < 0) { step = 5; txt = "⑥ 합쳐 판정: 네 블록의 밂을 더하니 바늘이 " + (isA ? "직선" : "곡선"); }
    else if (tc < 0) { step = 6; txt = "⑦ 도장: 그 화소에 " + (isA ? "직선(파랑)" : "곡선(초록)") + " 도장을 찍는다"; }
    else { step = 6; txt = isA ? "정답 카드와 대조: 정답도 직선 → 맞음" : "정답 카드와 대조: 정답은 직선인데 곡선 → 틀림"; }
  } else {
    const A = PA[0], B = PB[0];
    cx = ph.from === "a" ? A + (B - A) * ph.u : B + (A - B) * ph.u;
    const back = ph.from === "a" ? 1 - ph.u : 1 - ph.u;
    const push = PUSH[ph.from]; f = push.map((p) => p * back);
    if (ph.from === "b") { for (const n of ["a", "b"]) { marks[n].style.opacity = 1 - ph.fade; checks[n].style.opacity = 1 - ph.fade; } txt = "겹쳐 보기: A 맞음 · B 틀림 · 곡선 옆 직선 틀림 0.39 (직선끼리 0.07)"; }
    else txt = "다음 화소로 옮긴다";
  }
  car.setAttribute("transform", translateAlong(P, [cx - PA[0], 0, 0]));
  needles.forEach((n) => n.setAttribute("transform", translateAlong(P, [0, 0, -1.6 * tap])));
  faders.forEach((g, i) => g.setAttribute("transform", translateAlong(P, [f[i] * TRAVEL, 0, 0])));
  sieves.forEach((g, i) => g.toggleAttribute("data-active", i === active));
  feet.forEach((g, i) => g.toggleAttribute("data-active", i === active));
  keys.forEach((g, i) => g.toggleAttribute("data-active", i === step));
  const sum = f.reduce((a, b) => a + b, 0) / 4;
  const ang = (225 + 58 * Math.max(-1, Math.min(1, sum * 1.6))) * Math.PI / 180;
  const a0 = iso([DIAL.x - 3 * Math.cos(ang), DIAL.y - 3 * Math.sin(ang), DIAL_TOP + 0.4], P), a1 = iso([DIAL.x + (DIAL.R - 3) * Math.cos(ang), DIAL.y + (DIAL.R - 3) * Math.sin(ang), DIAL_TOP + 0.4], P);
  dialNeedle.setAttribute("d", "M" + a0[0].toFixed(2) + " " + a0[1].toFixed(2) + "L" + a1[0].toFixed(2) + " " + a1[1].toFixed(2));
  if (ph.spot === "a" && ph.s < 0.05) for (const n of ["a", "b"]) { marks[n].style.opacity = 0; checks[n].style.opacity = 0; }
  readout.textContent = txt;
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible && !held ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__seek = (t) => { held = true; cancelAnimationFrame(frame); frame = 0; draw(((t % LOOP) + LOOP) % LOOP); };   // 녹화용: 시계를 멈추고 t 초 장면
if (still.matches) { draw(2 * SPOT + MOVE + 1.0); } else draw(0);
`;
const css = `<style>
.iso{--mark-straight:var(--anatomy-blue);--mark-curve:var(--anatomy-green)}
[data-mark] .mark-fill{stroke:none}
[data-mark="a"] .mark-fill{fill:var(--mark-straight)}[data-mark="b"] .mark-fill{fill:var(--mark-curve)}
.band-straight{stroke:var(--mark-straight);stroke-width:2.2}.band-curve{stroke:var(--mark-curve);stroke-width:2.2}
.pad-straight>.iso-top{fill:var(--mark-straight)}.pad-curve>.iso-top{fill:var(--mark-curve)}
.foot{stroke:var(--anatomy-lo);fill:var(--anatomy-hi);fill-opacity:0;transition:stroke .3s,fill-opacity .3s}
.foot[data-active]{stroke:var(--anatomy-lit);stroke-width:1.2;fill-opacity:.07}
.ink .iso-line{stroke-width:1.3}
.truth .iso-line.truth-straight{stroke:var(--mark-straight);stroke-width:1.6}.truth .iso-line.truth-curve{stroke:var(--mark-curve);stroke-width:1.6}
.check-dot{stroke:none}.dot-straight{fill:var(--mark-straight)}.dot-curve{fill:var(--mark-curve)}
.check-ok{stroke:var(--anatomy-lit);stroke-width:1.1}.iso-line.check-no,.iso-line.check-x{stroke:var(--anatomy-red);stroke-width:1.2}
[data-step][data-active] .iso-edge{stroke:var(--anatomy-lit)}[data-step][data-active] .iso-top{fill:var(--anatomy-lit-top)}
[data-step][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
[data-sieve][data-active] .iso-edge{stroke:var(--anatomy-lit)}
[data-sieve][data-active] .iso-top{fill:var(--anatomy-lit-top)}
</style>`;
const body = k.plateHtml({
  fig: "그림 2", title: "우리 모델 · 판 137",
  hint: "저절로 돈다 · 한 바퀴 약 20 초",
  readout: "① 입력: 도면에서 곧은 선 위 화소 하나를 고른다",
  keys: [
    { mark: "flat", label: "번호판 ① 입력 ② 블록 1 ③ 블록 2 ④ 블록 3 ⑤ 블록 4 ⑥ 합쳐 판정 ⑦ 도장 · 지금 단계가 켜진다" },
    { mark: "flat", label: "정답 카드 = 같은 도면의 선마다 정답 종류(파랑 직선 · 초록 곡선) · 도장마다 같은 자리에 모델 답을 겹쳐 맞음(검정 고리) / 틀림(빨강 ×)" },
    { mark: "raised", label: "체 1~4 = CNN 블록 1~4 · 창 7 / 19 / 43 / 91 px · 그물 눈 2 / 4 / 8 / 16 px" },
    { mark: "lit", label: "페이더 넷 = 1×1 머리가 네 층(32+64+128+256 = 480 채널)을 섞는 가중합 · 왼쪽 파랑 직선 · 오른쪽 초록 곡선" },
    { mark: "dotted", label: "탐침이 판정 색 도장을 종이에 찍는다 · 체 · 페이더의 점 개수 = 블록 번호" },
  ],
  caption: "이 모델은 선만 그린 도면(시점마다 128×128)을 받아, 화소마다 그 자리가 빈칸 · 직선 · 곡선 · 곡면테 중 무엇인지(그리고 숨은 선인지 · 꼭짓점인지)를 맞힌다. 판 137 은 시점마다 128×128 도면을 CNN 블록 넷(해상도 64 / 32 / 16 / 8)에 통과시키고, 블록 2~4 를 64×64 로 키워 블록 1 과 이어 붙인 뒤 1×1 머리 하나로 화소마다 {없음 · 직선 · 곡선 · 곡면테}를 고른다. 선 자리 0.999 · 직선 0.78 · 곡선 0.76 · 꼭짓점 F1 0.51. 곧은 선이 곡선 2 px 안을 지나면 넓게 보는 층 2~4 의 창에 곡선이 들어와 곡선 쪽으로 밀고, 좁게 보는 층 1 만 직선 쪽으로 버틴다. 그 자리의 틀림은 0.39 로 직선끼리(0.07) · 곡선끼리(0.08)보다 크다(곡선 옆 직선 오류 전체 0.24). 페이더의 세기는 설명용이다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="판 137 모델 동작 그림">${svg}</div>`,
});
const out = join(HERE, theme === "light" ? "ours137-light.html" : "ours137.html");
writeFileSync(out, k.pageHtml({ title: "판 137 체", theme, body, script: kitScript() + live }));
console.log("wrote", out);
