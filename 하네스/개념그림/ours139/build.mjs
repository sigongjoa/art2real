// 판 139 「다중 라벨」 머리 — 회전 선택 스위치(판 137: 화소마다 한 칸만) 대 토글 스위치 넷(판 139: 칸마다 예/아니오)
// 근거(이 그림이 쓰는 사실만):
//   하네스/과제선지도.py: 입력 128×128 선 도면(3 시점 중 하나) · 판 137 머리 = 화소마다 softmax 로 {없음 · 직선 · 곡선 · 곡면테} 중 하나
//   out/하네스/137전부합침 겹침 진단: 직선과 곡선이 1~2 px 안에 닿으면 틀림 0.39 · 직선끼리 0.07
//   판 139: 머리만 바꿈 · 화소마다 sigmoid 넷 「선 있음?」「직선?」「곡선?」「곡면테?」 · 정답 = 자기 종류 예 +
//     3×3(1 px) 안에 다른 종류 화소가 닿으면 그 종류도 예 · 읽기 = 직선 · 곡선 중 큰 쪽 · 둘 다 켜기만 하면 무승부 = 틀림(모서리 채점)
//   판 139 는 아직 돌지 않았다 — 결과 숫자는 그리지 않는다. 그림의 도면은 22×11 화소로 확대한 설명용 격자다.
// 그림 요소: 정답 카드(화소 격자 · 닿은 화소는 파랑/초록 반반 · 받침의 램프 두 줄) · 확대 화소판 + 3×3 창 탐침 ·
//   콘솔 뒤 = 판 137 회전 스위치 · 콘솔 앞 = 판 139 토글 넷과 램프 · 단계 번호판 ①~⑥ · 정답 카드에 도장 대조
// 사용: node build.mjs [--light] → out/설명/anatomy/ours139/ours139[-light].html
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../../out/설명/anatomy/ours139");
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

const PLATE = { x: -182, y: -104, w: 324, d: 256, r: 10 };
const PLATE_H = 10, FOOT_H = 5;
// 확대 화소판: 칸 6 단위 = 화소 1 개
const G = 6, COLS = 22, ROWS = 11;
const BOARD = { x: -150, y: -62, w: COLS * G, d: ROWS * G, r: 1.5 };
const ST = 0.8;
const R0 = 9, ARC = { c: 11, r: 1, R: 8 };          // 곧은 선 = 줄 8 · 호 = 중심 (11, 2) 반지름 6 칸, 바닥이 곧은 선에 닿음
const key = (c, r) => c + "," + r;
const LINE = new Set(), CURVE = new Set();
for (let c = 1; c <= 20; c++) LINE.add(key(c, R0));
for (let a = 12; a <= 168; a += 0.5) { const t = a * Math.PI / 180; CURVE.add(key(Math.round(ARC.c + ARC.R * Math.cos(t)), Math.round(ARC.r + ARC.R * Math.sin(t)))); }
const near = (set, c, r) => { for (let dc = -1; dc <= 1; dc++) for (let dr = -1; dr <= 1; dr++) if (set.has(key(c + dc, r + dr))) return true; return false; };
// 판 139 정답: 자기 종류 예 + 3×3 안에 닿은 다른 종류도 예
const CELLS = [...new Set([...LINE, ...CURVE])].map((s) => { const [c, r] = s.split(",").map(Number); return { c, r, st: LINE.has(s) || near(LINE, c, r), cu: CURVE.has(s) || near(CURVE, c, r) }; });
// 탐침 자리: B = 닿은 화소(호 바닥) · A = 곡선이 1 px 밖(닿지 않음)에 있는 가장 가까운 직선 화소
const B = { c: ARC.c, r: R0 };
const A = { c: Math.max(...[...LINE].map((s) => s.split(",").map(Number)).filter(([c, r]) => c < ARC.c && !near(CURVE, c, r)).map(([c]) => c)), r: R0 };
const gapA = Math.min(...[...CURVE].map((s) => s.split(",").map(Number)).map(([c, r]) => Math.max(Math.abs(c - A.c), Math.abs(r - A.r))));
if (gapA !== 2) throw new Error("A 화소의 곡선 거리 " + gapA + " px — 2 px 이어야 한다");
const cellXY = ({ c, r }) => [BOARD.x + (c + 0.5) * G, BOARD.y + (r + 0.5) * G];
const PA = cellXY(A), PB = cellXY(B);
const RAIL_Y = -84, MAST_R = 3, MAST_TOP = 26, WIN = 1.5 * G, FR = { z: 7, t: 1.4, h: 1.6 };
// 콘솔: 뒤 = 판 137 회전 스위치 · 앞 = 판 139 토글 넷
const DESK = { x: 8, y: -92, w: 124, d: 164, r: 6 }, DESK_H = 8;
const P137 = { x: 13, y: -87, w: 114, d: 74, r: 3 }, P139 = { x: 13, y: -7, w: 114, d: 74, r: 3 };
const ROT = { x: 74, y: -48, R: 15 };
const POS = { none: 205, st: 245, cu: 295, rim: 335 };
const KINDS = [["line", "선"], ["st", "직선"], ["cu", "곡선"], ["rim", "곡면테"]];
const LAMP_X = [28, 56, 84, 112], LAMP_Y = 14, TOG_Y = 36;
// 정답 카드
const CS = 0.7, CARD = { x: -168, y: 26, w: BOARD.w * CS, d: BOARD.d * CS, r: 1 };
const HOLD = { x: CARD.x - 4, y: CARD.y - 4, w: CARD.w + 8, d: CARD.d + 34, r: 2 };
const cardPt = ([x, y]) => [CARD.x + (x - BOARD.x) * CS, CARD.y + (y - BOARD.y) * CS];
const KEYS = { x: 8, y: 84, w: 124, d: 20, r: 2 }, NKEY = 6, KEY_W = 16;

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [PA[0], RAIL_Y, MAST_TOP + 2]], WIDTH, HEIGHT, { pad: 30, azimuth: 60, elevation: 40 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const T = (x, y, z, text, size, tone = "mid", anchor = "middle") => k.faceTextSvg(k.topMatrix([x, y], z, P, "x"), text, { size, tone, anchor });
const depth = (x, y, z = 0) => k.depthOf([x, y, z], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth(a[0], a[1]) - depth(b[0], b[1]));
const quad = (x0, y0, x1, y1, z) => k.onTop([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], z, P, true);
const halves = (x0, y0, x1, y1, z) => [k.onTop([[x0, y0], [x1, y0], [x0, y1]], z, P, true), k.onTop([[x1, y0], [x1, y1], [x0, y1]], z, P, true)];

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
  // 자 두 개 — 화소 칸마다 눈금(6), 5 칸마다 큰 눈금
  const strip = { x: BOARD.x, y: BOARD.y - 14, w: BOARD.w, d: 7, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 6, strip.x + strip.w - 6, G, 5, strip.y + strip.d - 0.8, 0.6, [-2, -3.6], P);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  const side = { x: BOARD.x - 14, y: BOARD.y, w: 7, d: BOARD.d, r: 1 };
  o.push(S(k.slabOf(side, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const s2 = k.topTicks(side.y + 6, side.y + side.d - 6, G, 5, side.x + side.w - 0.8, 0.6, [-2, -3.6], P, "y");
  if (s2 && s2.minor) o.push(L(s2.minor, { tone: "lo" }), L(s2.major, { tone: "mid" }));
  // 이름판(콘솔 앞) — 세 줄은 인쇄 글자
  const plate = { x: 30, y: PLATE.y + PLATE.d - 18, w: 44, d: 10, r: 1.2 };
  o.push(S(k.slabOf(plate, 0, 0.8, P, 4), { tone: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(plate, 1.6), 0.8, P), { tone: "faint" }));
  [[5, 30], [5, 22], [5, 26]].forEach(([dx, len], i) => o.push(L(k.lineOnTop([plate.x + dx, plate.y + 2.6 + i * 2.4], [plate.x + dx + len, plate.y + 2.6 + i * 2.4], 0.8, P), { tone: "lo", free: true })));
  o.push(D([at([plate.x + 2.4, plate.y + plate.d / 2, 0.8]), at([plate.x + plate.w - 2.4, plate.y + plate.d / 2, 0.8])], { size: 0.45 }));
  return o.join("");
}
function board() {   // 화소판: 종이 + 칸 격자 + 먹 칸(입력은 흑백) + 도장 자리
  const o = [S(k.slabOf(BOARD, 0, ST, P, 4), { tone: "hi", crease: "lo" })];
  const z = ST + 0.02;
  const grid = [];
  for (let c = 1; c < COLS; c++) grid.push(k.lineOnTop([BOARD.x + c * G, BOARD.y], [BOARD.x + c * G, BOARD.y + BOARD.d], z, P));
  for (let r = 1; r < ROWS; r++) grid.push(k.lineOnTop([BOARD.x, BOARD.y + r * G], [BOARD.x + BOARD.w, BOARD.y + r * G], z, P));
  o.push(L(grid.join(""), { tone: "faint" }));
  o.push(`<path class="ink-cell" d="${CELLS.map(({ c, r }) => quad(BOARD.x + c * G + 0.6, BOARD.y + r * G + 0.6, BOARD.x + (c + 1) * G - 0.6, BOARD.y + (r + 1) * G - 0.6, z + 0.02)).join("")}"/>`);
  for (const [name, { c, r }] of [["a", A], ["b", B]]) {
    const x0 = BOARD.x + c * G + 0.3, y0 = BOARD.y + r * G + 0.3, x1 = x0 + G - 0.6, y1 = y0 + G - 0.6;
    const [h1, h2] = halves(x0, y0, x1, y1, z + 0.06);
    o.push(`<g data-mark="${name}" style="opacity:0"><path class="m1" d="${h1}"/><path class="m2" d="${h2}"/><path class="iso-line" data-tone="hi" d="${quad(x0, y0, x1, y1, z + 0.06)}"/></g>`);
  }
  return o.join("");
}
function rail() {
  const r = { x: -152, y: RAIL_Y - 5, w: 136, d: 10, r: 2 };
  const o = [S(k.slabOf(r, 0, 4, P, 4, 0.5), { tone: "mid" })];
  o.push(L(k.lineOnTop([r.x + 6, RAIL_Y], [r.x + r.w - 6, RAIL_Y], 4, P), { tone: "faint" }));
  for (const x of [r.x - 2, r.x + r.w - 4]) {
    o.push(S(k.slabOf({ x, y: RAIL_Y - 7, w: 6, d: 14, r: 1.2 }, 0, 8, P, 3, 0.5), { tone: "mid" }));
    o.push(D([at([x + 3, RAIL_Y - 4, 8]), at([x + 3, RAIL_Y + 4, 8])], { size: 0.45 }));
  }
  return o.join("");
}
function carriage() {   // A 자리에 짓고 수레째 옮김 · 탐침 둘레 3×3 창 = 「닿음」의 기준(1 px)
  const [cx, cy] = PA, a = WIN, { z, t, h } = FR;
  const o = [];
  o.push(S(k.slabOf({ x: cx - 9, y: RAIL_Y - 7, w: 18, d: 14, r: 2 }, 4, 6, P, 4, 0.6), { tone: "mid" }));
  o.push(D(k.corners({ x: cx - 9, y: RAIL_Y - 7, w: 18, d: 14 }, 2.4).map(([x, y]) => at([x, y, 10])), { size: 0.42 }));
  o.push(S(k.cylinder(cx, RAIL_Y, 4.6, 10, 2.4, P, 28), { tone: "lo" }));
  o.push(S(k.cylinder(cx, RAIL_Y, MAST_R, 12.4, MAST_TOP - 12.4, P, 28), { tone: "mid", crease: "none" }));
  o.push(S(k.cylinder(cx, RAIL_Y, 3.8, MAST_TOP, 1.6, P, 24, 0.3), { tone: "mid" }));
  const armZ = 16, y0 = RAIL_Y + MAST_R - 0.4;
  o.push(S(k.slabOf({ x: cx - 1.8, y: y0, w: 3.6, d: cy - a - t - y0 + 1, r: 0.6 }, armZ, 2, P, 3, 0.3), { tone: "mid" }));
  // 내림대: 팔 끝에서 창 테까지
  o.push(S(k.slabOf({ x: cx - 1.8, y: cy - a - t, w: 3.6, d: t, r: 0.4 }, z + h, armZ - z - h, P, 2), { tone: "mid" }));
  const bars = [
    { x: cx - a - t, y: cy + a, w: 2 * a + 2 * t, d: t },
    { x: cx - a - t, y: cy - a - t, w: 2 * a + 2 * t, d: t },
    { x: cx - a - t, y: cy - a, w: t, d: 2 * a },
    { x: cx + a, y: cy - a, w: t, d: 2 * a },
  ].map((b) => ({ ...b, r: 0.4, dep: depth(b.x + b.w / 2, b.y + b.d / 2, z) })).sort((p, q) => p.dep - q.dep);
  const bar = (b) => S(k.slabOf(b, z, h, P, 3, 0.3), { tone: "mid" });
  const mesh = [];
  for (const u of [-G / 2, G / 2]) mesh.push(k.lineOnTop([cx + u, cy - a], [cx + u, cy + a], z + h, P), k.lineOnTop([cx - a, cy + u], [cx + a, cy + u], z + h, P));
  const needle = `<g data-part="needle">${S(k.cylinder(cx, cy, 1.4, 2.2, 1.4, P, 20, 0.3), { tone: "hi", lit: true })}${S(k.cylinder(cx, cy, 0.6, 3.6, z + h + 3 - 3.6, P, 14), { tone: "mid", crease: "none" })}${S(k.cylinder(cx, cy, 1.5, z + h + 3, 1.2, P, 20, 0.3), { tone: "mid" })}</g>`;
  o.push(`<g data-part="window">${bar(bars[0])}${bar(bars[1])}${L(mesh.join(""), { tone: "lo" })}</g>`, needle, `<g data-part="window">${bar(bars[2])}${bar(bars[3])}</g>`);
  return o.join("");
}
function desk() {
  const o = [S(k.slabOf(DESK, 0, DESK_H, P, 6, 0.8), { tone: "mid", inner: L(k.sideSeam(DESK, 3, P, 6), { tone: "faint" }) })];
  o.push(D(k.corners(DESK, 3.2).map(([x, y]) => at([x, y, DESK_H])), { size: 0.45 }));
  const z = DESK_H;
  // ── 판 137: 회전 선택 스위치 — 바늘은 한 칸에만 선다
  o.push(`<g data-panel="137"><path class="iso-line panel-edge" data-tone="lo" d="${k.planOutline(P137, z, P, 4)}"/>`);
  o.push(T(P137.x + 4, P137.y + P137.d - 4, z, "판 137 · 한 칸만 고름", 5.2, "mid", "start"));
  const { x, y, R } = ROT;
  o.push(S(k.cylinder(x, y, R + 4, z, 1.4, P, 64, 0.4), { tone: "lo" }));
  o.push(L(k.ring(x, y, R + 1.5, z + 1.4, P, 64), { tone: "faint" }));
  for (const [kind, label] of [["none", "없음"], ...KINDS.slice(1)]) {
    const ang = POS[kind] * Math.PI / 180, px = x + (R + 9) * Math.cos(ang), py = y + (R + 9) * Math.sin(ang);
    o.push(S(k.slabOf({ x: px - 3, y: py - 3, w: 6, d: 6, r: 1 }, z, 0.8, P, 3), { tone: "lo", className: "pad-" + kind, crease: "none" }));
    o.push(T(x + (R + (kind === "none" || kind === "rim" ? 24 : 19)) * Math.cos(ang), y + (R + (kind === "none" || kind === "rim" ? 24 : 19)) * Math.sin(ang) + 2.4, z, label, 6, "mid"));
  }
  o.push(S(k.cylinder(x, y, 9, z + 1.4, 4.2, P, 48, 0.5), { tone: "hi", crease: "lo", inner: L(k.knurl(x, y, 9, z + 2.2, z + 5, 28, P), { tone: "faint" }) }));
  o.push(`<path data-part="rot-needle" class="iso-line" data-tone="lit" data-free="end" style="stroke-width:1.6" d=""/>`);
  o.push(S(k.cylinder(x, y, 1.6, z + 5.6, 0.8, P, 20, 0.2), { tone: "mid" }));
  o.push(`</g>`);
  // ── 판 139: 칸마다 토글 + 램프 — 서로 따로 켜진다
  o.push(`<g data-panel="139"><path class="iso-line panel-edge" data-tone="lo" d="${k.planOutline(P139, z, P, 4)}"/>`);
  o.push(T(P139.x + 4, P139.y + P139.d - 4, z, "판 139 · 칸마다 예/아니오", 5.2, "mid", "start"));
  KINDS.forEach(([kind, label], i) => {
    const lx = LAMP_X[i];
    o.push(S(k.cylinder(lx, LAMP_Y, 6, z, 1.6, P, 40, 0.4), { tone: "lo" }));
    o.push(`<g data-lamp="${kind}">${S(k.cylinder(lx, LAMP_Y, 4.4, z + 1.6, 3.4, P, 40, 0.8), { tone: "hi", className: "lens" })}</g>`);
    const tb = { x: lx - 4, y: TOG_Y - 6, w: 8, d: 12, r: 1.2 };
    o.push(S(k.slabOf(tb, z, 1.4, P, 3, 0.4), { tone: "mid" }));
    o.push(L(k.lineOnTop([lx, TOG_Y - 4], [lx, TOG_Y + 4], z + 1.4, P), { tone: "lo" }));
    o.push(D([at([lx, tb.y + 1.2, z + 1.4]), at([lx, tb.y + tb.d - 1.2, z + 1.4])], { size: 0.38 }));
    o.push(`<g data-toggle="${kind}">${S(k.slabOf({ x: lx - 1.8, y: TOG_Y + 1, w: 3.6, d: 3.6, r: 0.8 }, z + 1.4, 4.2, P, 3, 0.4), { tone: "hi" })}</g>`);
    o.push(T(lx, TOG_Y + 15, z, label, 6, "mid"));
  });
  o.push(`</g>`);
  return o.join("");
}
function answer() {   // 정답 카드(판 139 정답): 직선만 파랑 · 곡선만 초록 · 닿은 화소 반반 + 받침 램프 두 줄
  const o = [S(k.slabOf(HOLD, 0, 2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(HOLD, 2).map(([x, y]) => at([x, y, 2])), { size: 0.42 }));
  o.push(S(k.slabOf(CARD, 2, 0.8, P, 4), { tone: "hi", crease: "lo" }));
  const z = 2.82, g = G * CS;
  const cls = { st: [], cu: [], s1: [], s2: [] };
  for (const cell of CELLS) {
    const [x0, y0] = cardPt([BOARD.x + cell.c * G, BOARD.y + cell.r * G]), x1 = x0 + g - 0.25, y1 = y0 + g - 0.25;
    if (cell.st && cell.cu) { const [h1, h2] = halves(x0 + 0.25, y0 + 0.25, x1, y1, z); cls.s1.push(h1); cls.s2.push(h2); }
    else cls[cell.st ? "st" : "cu"].push(quad(x0 + 0.25, y0 + 0.25, x1, y1, z));
  }
  o.push(`<path class="c-st" d="${cls.st.join("")}${cls.s1.join("")}"/><path class="c-cu" d="${cls.cu.join("")}${cls.s2.join("")}"/>`);
  o.push(T(HOLD.x + HOLD.w - 3, CARD.y + 4.5, z, "정답", 6, "mid", "end"));
  // 대조 고리: 판 137 도장(틀림 빨강 ×) · 판 139 도장(맞음 검정 고리)
  for (const [name, p, ok] of [["a137", PA, false], ["b137", PB, false], ["a139", PA, true], ["b139", PB, true]]) {
    const [cx, cy] = cardPt(p), rr = g * 1.05;
    const cross = ok ? "" : L(k.lineOnTop([cx + rr + 0.6, cy - rr - 3.6], [cx + rr + 3.6, cy - rr - 0.6], z, P) + k.lineOnTop([cx + rr + 0.6, cy - rr - 0.6], [cx + rr + 3.6, cy - rr - 3.6], z, P), { className: "check-x", free: true });
    o.push(`<g data-check="${name}" style="opacity:0"><path class="iso-line ${ok ? "check-ok" : "check-no"}" d="${k.ring(cx, cy, rr, z, P, 28)}"/>${cross}</g>`);
  }
  // 받침 램프 두 줄: 닿은 화소 = 직선 ● 곡선 ● · 직선 화소 = 직선 ● 곡선 ○
  const rows = [["b", "닿은 화소", true], ["a", "직선 화소", false]];
  rows.forEach(([name, label, both], i) => {
    const ry = CARD.y + CARD.d + 9 + i * 12;
    o.push(T(HOLD.x + 4, ry + 2.2, 2, label, 6, "mid", "start"));
    [["st", true], ["cu", both]].forEach(([kind, on], j) => {
      const lx = HOLD.x + 42 + j * 12;
      o.push(S(k.cylinder(lx, ry, 3.6, 2, 0.8, P, 28, 0.3), { tone: "mid" }));
      o.push(`<g data-cardlamp="${name}" data-kind="${kind}"${on ? ' data-want=""' : ""}>${S(k.cylinder(lx, ry, 2.6, 2.8, 1.8, P, 28, 0.5), { tone: "hi", className: "lens" })}</g>`);
    });
    o.push(T(HOLD.x + 60, ry + 2, 2, i ? "직선만" : "둘 다", 5.5, "mid", "start"));
  });
  return o.join("");
}
function steps() {
  const o = [S(k.slabOf(KEYS, 0, 1.2, P, 4, 0.4), { tone: "lo" })];
  o.push(D([at([KEYS.x + 2.2, KEYS.y + KEYS.d / 2, 1.2]), at([KEYS.x + KEYS.w - 2.2, KEYS.y + KEYS.d / 2, 1.2])], { size: 0.42 }));
  const gap = (KEYS.w - 8 - NKEY * KEY_W) / (NKEY - 1);
  for (let i = 0; i < NKEY; i++) {
    const kp = { x: KEYS.x + 4 + i * (KEY_W + gap), y: KEYS.y + 3.5, w: KEY_W, d: 13, r: 1.4 };
    o.push(`<g data-step="${i}">${S(k.slabOf(kp, 1.2, 2.6, P, 3, 0.5), { tone: "mid" })}${k.faceTextSvg(k.topMatrix([kp.x + kp.w / 2, kp.y + kp.d / 2 + 2.6], 3.8, P, "x"), String(i + 1), { size: 7, tone: "mid", anchor: "middle" })}</g>`);
  }
  return o.join("");
}
const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "판 139 다중 라벨 머리를 회전 스위치와 토글 스위치로 그린 그림. 확대한 화소판 위로 3×3 창 탐침이 곧은 선 화소 둘을 찾아간다. 판 137 회전 스위치는 한 칸에만 서서 곡선 옆 직선 화소를 곡선으로 찍고, 닿은 화소에서도 곡선 하나만 고른다. 판 139 토글 넷은 따로 켜져 닿은 화소에서 직선과 곡선을 둘 다 켜고 직선 화소에서는 직선만 켠다.",
  body: [base(), answer(), board(), rail(), `<g data-part="carriage">${carriage()}</g>`, desk(), steps()],
});

const live = `
const P = ${JSON.stringify(P)};
const PA = ${JSON.stringify(PA)}, PB = ${JSON.stringify(PB)}, ROT = ${JSON.stringify(ROT)}, ROT_Z = ${DESK_H + 5.7}, POS = ${JSON.stringify(POS)};
const $ = (s) => svg.querySelector(s), $$ = (s) => [...svg.querySelectorAll(s)];
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const car = $('[data-part="carriage"]'), needle = $('[data-part="needle"]'), rotNeedle = $('[data-part="rot-needle"]');
const marks = { a: $('[data-mark="a"]'), b: $('[data-mark="b"]') };
const checks = Object.fromEntries($$("[data-check]").map((g) => [g.dataset.check, g]));
const keys = $$("[data-step]").sort((a, b) => a.dataset.step - b.dataset.step);
const panels = { 137: $('[data-panel="137"]'), 139: $('[data-panel="139"]') };
const lamps = Object.fromEntries($$("[data-lamp]").map((g) => [g.dataset.lamp, g]));
const toggles = Object.fromEntries($$("[data-toggle]").map((g) => [g.dataset.toggle, g]));
const cardLamps = $$("[data-cardlamp]");
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
// 열쇠 장면 사이를 부드럽게: [[t, v], ...]
const kf = (t, ks) => { if (t <= ks[0][0]) return ks[0][1]; for (let i = 1; i < ks.length; i++) if (t <= ks[i][0]) { const [t0, v0] = ks[i - 1], [t1, v1] = ks[i]; return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0)); } return ks[ks.length - 1][1]; };
const on = (t, t0, t1) => t >= t0 && t < t1;
const LOOP = 28;
// 시간표(초) — 0 정답 · 3.6 판 137 A · 7.4 B · 13.2 판 139 A · 17.6 B · 22 읽기 · 26.5 되감기
const TX = [[0, PA[0]], [7.4, PA[0]], [8.6, PB[0]], [13.2, PB[0]], [14.6, PA[0]], [17.6, PA[0]], [18.8, PB[0]], [22.0, PB[0]], [23.0, PB[0] + 42], [26.5, PB[0] + 42], [27.8, PA[0]]];
const TROT = [[0, POS.none], [4.6, POS.none], [5.4, POS.st], [5.7, POS.st], [6.3, POS.cu], [7.4, POS.cu], [8.4, POS.none], [8.7, POS.none], [9.4, POS.cu], [13.2, POS.cu], [14.2, POS.none]];
const TOG = { line: [[15.0, 17.6], [19.2, 26.5]], st: [[15.6, 17.6], [19.7, 26.5]], cu: [[20.2, 26.5]], rim: [] };
const STAMP = [6.4, 9.8, 16.6, 20.8];
function text(t) {
  if (t < 1.8) return "① 정답: 직선과 곡선이 닿은 화소는 직선 · 곡선 둘 다 정답";
  if (t < 3.6) return "① 정답: 곡선이 2 px 옆인 직선 화소는 직선만";
  if (t < 4.6) return "② 판 137: 화소마다 회전 스위치 하나 — 한 칸에만 선다";
  if (t < 5.6) return "② 직선 화소: 스위치가 먼저 직선 칸으로 돈다";
  if (t < 6.6) return "② 2 px 옆 곡선에 끌려 곡선 칸으로 넘어간다";
  if (t < 7.4) return "② 곡선 도장 · 정답은 직선 → 틀림";
  if (t < 8.6) return "다음: 직선과 곡선이 닿은 화소로";
  if (t < 9.8) return "③ 닿은 화소: 둘 다 정답인데 스위치는 한 칸만";
  if (t < 11.6) return "③ 곡선 하나만 찍혀 직선을 잃는다 → 틀림";
  if (t < 13.2) return "판 137 진단: 직선–곡선 닿은 곳 틀림 0.39 · 직선끼리 0.07";
  if (t < 14.6) return "④ 판 139: 머리만 바꾼다 — 칸마다 예/아니오 토글 넷";
  if (t < 16.2) return "④ 직선 화소: 선? 예 · 직선? 예 · 곡선? 아니오 · 테? 아니오";
  if (t < 17.6) return "④ 직선 램프만 켜져 파랑 도장 → 정답과 같다";
  if (t < 18.8) return "다음: 닿은 화소로";
  if (t < 20.6) return "⑤ 닿은 화소: 직선 · 곡선 토글을 둘 다 켠다";
  if (t < 22.0) return "⑤ 반반 도장 → 정답과 같다";
  if (t < 24.2) return "⑥ 읽기: 직선 · 곡선 중 큰 쪽 · 다 켜기만 하면 무승부 = 틀림";
  return "닿은 화소는 둘 다 켠다 · 직선 자기 화소는 직선만";
}
function draw(t) {
  const fadeOut = (t0) => 1 - ease((t - t0) / 0.6);
  const cx = kf(t, TX);
  car.setAttribute("transform", translateAlong(P, [cx - PA[0], 0, 0]));
  let tap = 0; for (const s of STAMP) { const u = (t - s + 0.4) / 0.8; if (u > 0 && u < 1) tap = Math.sin(Math.PI * u); }
  needle.setAttribute("transform", translateAlong(P, [0, 0, -1.6 * tap]));
  const ang = kf(t, TROT) * Math.PI / 180;
  const a0 = iso([ROT.x - 3 * Math.cos(ang), ROT.y - 3 * Math.sin(ang), ROT_Z], P), a1 = iso([ROT.x + (ROT.R + 3) * Math.cos(ang), ROT.y + (ROT.R + 3) * Math.sin(ang), ROT_Z], P);
  rotNeedle.setAttribute("d", "M" + a0[0].toFixed(2) + " " + a0[1].toFixed(2) + "L" + a1[0].toFixed(2) + " " + a1[1].toFixed(2));
  for (const [kind, spans] of Object.entries(TOG)) {
    const v = spans.reduce((m, [t0, t1]) => Math.max(m, ease((t - t0) / 0.3) * (1 - ease((t - t1) / 0.3))), 0);
    toggles[kind].setAttribute("transform", translateAlong(P, [0, -5.2 * v, 0]));
    lamps[kind].toggleAttribute("data-on", v > 0.5);
  }
  panels[137].toggleAttribute("data-active", on(t, 3.6, 13.2));
  panels[139].toggleAttribute("data-active", on(t, 13.2, 26.5));
  panels[137].toggleAttribute("data-dim", on(t, 14.2, 26.5));
  // 도장: 판 137 → 초록 · 판 139 → A 파랑 · B 반반
  const mark = (g, k, op) => { g.dataset.k = k; g.style.opacity = op; };
  if (t >= 16.6) mark(marks.a, "blue", t < 26.5 ? 1 : fadeOut(26.5)); else if (t >= 6.4) mark(marks.a, "green", t < 13.2 ? 1 : fadeOut(13.2)); else mark(marks.a, "green", 0);
  if (t >= 20.8) mark(marks.b, "split", t < 26.5 ? 1 : fadeOut(26.5)); else if (t >= 9.8) mark(marks.b, "green", t < 13.2 ? 1 : fadeOut(13.2)); else mark(marks.b, "green", 0);
  const blink = (t0, t1) => t < t0 ? 0 : t < t0 + 0.9 ? 0.35 + 0.65 * Math.abs(Math.cos(Math.PI * (t - t0) / 0.3)) : t < t1 ? 1 : fadeOut(t1);
  checks.a137.style.opacity = blink(6.8, 13.2); checks.b137.style.opacity = blink(10.2, 13.2);
  checks.a139.style.opacity = t < 4.2 ? blink(2.0, 3.6) : blink(17.0, 26.5); checks.b139.style.opacity = t < 4.2 ? blink(0.8, 3.6) : blink(21.2, 26.5);
  cardLamps.forEach((g) => g.toggleAttribute("data-on", g.hasAttribute("data-want") && t >= (g.dataset.cardlamp === "b" ? 0.8 : 2.0)));
  const step = t < 3.6 ? 0 : t < 8.6 ? 1 : t < 13.2 ? 2 : t < 18.8 ? 3 : t < 22 ? 4 : t < 26.5 ? 5 : -1;
  keys.forEach((g, i) => g.toggleAttribute("data-active", i === step));
  readout.textContent = text(t);
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible && !held ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__seek = (t) => { held = true; cancelAnimationFrame(frame); frame = 0; draw(((t % LOOP) + LOOP) % LOOP); };   // 녹화용
if (still.matches) draw(25); else draw(0);
`;
const css = `<style>
.iso{--k-st:var(--anatomy-blue);--k-cu:var(--anatomy-green);--k-rim:#c9971c;--k-line:var(--anatomy-hi)}
.iso[data-theme="dark"],[data-theme="dark"] .iso{--k-rim:#e3b341}
.ink-cell{fill:var(--anatomy-hi);stroke:none}
.c-st{fill:var(--k-st);stroke:none}.c-cu{fill:var(--k-cu);stroke:none}
[data-mark] .m1,[data-mark] .m2{stroke:none}
[data-mark][data-k="green"] path.m1,[data-mark][data-k="green"] path.m2{fill:var(--k-cu)}
[data-mark][data-k="blue"] path.m1,[data-mark][data-k="blue"] path.m2{fill:var(--k-st)}
[data-mark][data-k="split"] path.m1{fill:var(--k-st)}[data-mark][data-k="split"] path.m2{fill:var(--k-cu)}
.pad-none>.iso-top{fill:var(--anatomy-faint)}.pad-st>.iso-top{fill:var(--k-st)}.pad-cu>.iso-top{fill:var(--k-cu)}.pad-rim>.iso-top{fill:var(--k-rim)}
[data-lamp][data-on] .lens>.iso-top,[data-cardlamp][data-on] .lens>.iso-top{fill:var(--lamp)}
[data-lamp][data-on] .lens>.iso-shade,[data-cardlamp][data-on] .lens>.iso-shade{fill:var(--lamp);filter:brightness(.82)}
[data-lamp="line"]{--lamp:var(--k-line)}[data-lamp="st"],[data-kind="st"]{--lamp:var(--k-st)}[data-lamp="cu"],[data-kind="cu"]{--lamp:var(--k-cu)}[data-lamp="rim"]{--lamp:var(--k-rim)}
[data-panel][data-active] .panel-edge{stroke:var(--anatomy-lit);stroke-width:1.3}
[data-panel][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
[data-panel="137"]{transition:opacity .4s}[data-panel="137"][data-dim]{opacity:.45}
.check-ok{stroke:var(--anatomy-lit);stroke-width:1.2}.iso-line.check-no,.iso-line.check-x{stroke:var(--anatomy-red);stroke-width:1.3}
[data-step][data-active] .iso-edge{stroke:var(--anatomy-lit)}[data-step][data-active] .iso-top{fill:var(--anatomy-lit-top)}
[data-step][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
</style>`;
const body = k.plateHtml({
  fig: "그림 3", title: "다중 라벨 머리 · 판 139",
  hint: "저절로 돈다 · 한 바퀴 28 초",
  readout: text0(),
  keys: [
    { mark: "flat", label: "번호판 ① 정답 ② 판 137 직선 화소 ③ 판 137 닿은 화소 ④ 판 139 직선 화소 ⑤ 판 139 닿은 화소 ⑥ 읽기" },
    { mark: "flat", label: "정답 카드 = 판 139 정답 · 파랑 직선 · 초록 곡선 · 닿은 화소(3×3 안에 다른 종류)는 반반 · 도장마다 맞음(검정 고리) / 틀림(빨강 ×)" },
    { mark: "raised", label: "회전 스위치 = 판 137 머리(softmax) · 없음 · 직선 · 곡선 · 곡면테 중 한 칸에만 선다" },
    { mark: "lit", label: "토글 넷 = 판 139 머리(sigmoid 넷) · 선 · 직선(파랑) · 곡선(초록) · 곡면테(금) 램프가 서로 따로 켜진다" },
    { mark: "dotted", label: "탐침의 3×3 창 = 「닿음」 기준 1 px · 화소판은 설명용으로 22×11 화소만 키웠다" },
  ],
  caption: "입력은 CAD 부품 시점 하나의 128×128 선 도면이다. 판 137 은 화소마다 {없음 · 직선 · 곡선 · 곡면테} 중 하나를 softmax 로 고르므로, 직선과 곡선이 닿거나 1~2 px 안을 나란히 지나는 화소도 한 종류여야 한다. 그래서 곡선 옆 직선이 곡선으로 읽힌다(직선–곡선이 닿은 모서리 틀림 0.39 · 직선끼리 0.07). 판 139 는 머리만 바꿔 화소마다 「선 있음?」「직선?」「곡선?」「곡면테?」를 따로 예/아니오(sigmoid)로 묻는다. 정답은 자기 종류가 예이고, 3×3 안에 다른 종류 화소가 닿으면 그 종류도 예다. 읽을 때는 직선 · 곡선 중 큰 쪽을 고르고, 둘 다 켜기만 하는 모델은 모서리 채점에서 무승부 = 틀림이 된다. 판 139 는 아직 돌지 않았다 — 이 그림은 결과가 아니라 바꾼 구조를 보여 준다. 스위치 움직임은 설명용이다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="판 139 다중 라벨 머리 동작 그림">${svg}</div>`,
});
function text0() { return "① 정답: 직선과 곡선이 닿은 화소는 직선 · 곡선 둘 다 정답"; }
mkdirSync(OUT, { recursive: true });
const out = join(OUT, theme === "light" ? "ours139-light.html" : "ours139.html");
writeFileSync(out, k.pageHtml({ title: "판 139 다중 라벨", theme, body, script: kitScript() + live }));
console.log("wrote", out, "· A =", JSON.stringify(A), "B =", JSON.stringify(B), "· 칸", CELLS.length, "· 반반", CELLS.filter((c) => c.st && c.cu).length);
