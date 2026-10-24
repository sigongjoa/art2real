// 판 140 「벡터화」 — 칠한 화소 도면 → 선 목록(선 하나 = 토큰 한 줄). 계산만, 학습 없음.
// 근거(이 그림이 쓰는 사실만):
//   입력: 판 137 CNN 이 128×128 선 도면에 화소마다 칠한 것(선 예/아니오 · 종류) + 꼭짓점 열지도
//   절차: ① 칠한 화소 ② 1 화소 뼈대로 가늘게 ③ 마디 = 열지도 봉우리 + 뼈대 갈림/끝 화소 ④ 마디 사이 화소 사슬 따라가기
//         ⑤ 현에서 가장 먼 화소 = 휨 · 휨 ≥ 2 px → 원호(가운데 점 보관) · 아니면 직선 ⑥ 토큰 [뷰, 종류, 시작x, 시작y, 끝x, 끝y, 휨, 숨은선?]
//   채점: CAD 정답 선 목록과 짝 맞춤 → 재현 · 정밀 · 종류
//   판 140 은 아직 돌지 않았다 — 결과 숫자는 그리지 않는다. 화소판은 설명용 24×15 격자, 좌표는 이 판의 칸 번호,
//   가짜 마디 · 놓친 숨은선 · 채점 분수는 채점 방식을 보이려 지어 넣은 예시다.
// 그림 요소: 확대 화소판 + XY 플로터(펜이 뼈대를 걷는다) · 테이프 인쇄기(토큰 한 줄씩) · 정답 카드(CAD 선 + 짝 고리) · 번호판 ①~⑦
// 사용: node build.mjs [--light] [--record]
//   → out/설명/anatomy/vec140/vec140[-light].html · --record 는 light 판을 8 fps × 2 배로 찍어 이 폴더에 vec140.mp4 · .gif
import { mkdirSync, writeFileSync, readdirSync, unlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../../out/설명/anatomy/vec140");
const RECORD = process.argv.includes("--record");
const theme = RECORD || process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

// ── 도면(칸 좌표) ─────────────────────────────────────────────
const G = 6, COLS = 24, ROWS = 15;
const BOARD = { x: -186, y: -74, w: COLS * G, d: ROWS * G, r: 1.5 };
const ARC = { c: 13, r: 10, R: 8 };
const key = (c, r) => c + "," + r;
function lineCells([c0, r0], [c1, r1]) {   // 곧은 사슬(가로 · 세로만 씀)
  const n = Math.max(Math.abs(c1 - c0), Math.abs(r1 - r0)), o = [];
  for (let i = 0; i <= n; i++) o.push([Math.round(c0 + (c1 - c0) * i / n), Math.round(r0 + (r1 - r0) * i / n)]);
  return o;
}
function arcCells() {   // (13,2) → (21,10), 중심 (13,10) 반지름 8 의 사분원
  const o = [];
  for (let a = -90; a <= 0; a += 0.5) {
    const t = a * Math.PI / 180, p = [Math.round(ARC.c + ARC.R * Math.cos(t)), Math.round(ARC.r + ARC.R * Math.sin(t))];
    if (!o.length || key(...o[o.length - 1]) !== key(...p)) o.push(p);
  }
  return o;
}
// 우리 벡터화가 낸 가지(가짜 마디 (7,2) 가 윗변을 둘로 쪼갠다)
const BR = [
  lineCells([2, 2], [7, 2]), lineCells([7, 2], [13, 2]), arcCells(), lineCells([21, 10], [21, 13]),
  lineCells([21, 13], [9, 13]), lineCells([9, 13], [2, 13]), lineCells([2, 13], [2, 2]), lineCells([9, 13], [9, 8]),
];
for (const ch of BR) for (let i = 1; i < ch.length; i++) if (Math.max(Math.abs(ch[i][0] - ch[i - 1][0]), Math.abs(ch[i][1] - ch[i - 1][1])) !== 1) throw new Error("사슬이 끊겼다");
// 휨 = 현에서 가장 먼 화소 거리(칸)
const FIT = BR.map((ch) => {
  const [a, b] = [ch[0], ch[ch.length - 1]], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  let bend = 0, far = a;
  for (const p of ch) { const d = Math.abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / L; if (d > bend) { bend = d; far = p; } }
  return { a, b, bend: Math.round(bend * 10) / 10, far, kind: bend >= 2 ? "arc" : "line" };
});
if (FIT[2].kind !== "arc" || FIT.some((f, i) => i !== 2 && f.kind !== "line")) throw new Error("휨 판정이 그림과 다르다: " + FIT.map((f) => f.bend));
const TOKENS = FIT.map((f) => `[앞,${f.kind === "arc" ? "원호" : "직선"},${f.a[0]},${f.a[1]},${f.b[0]},${f.b[1]},${f.bend},아니오]`);
const SKEL = new Map();
BR.forEach((ch) => ch.forEach((p) => { if (!SKEL.has(key(...p))) SKEL.set(key(...p), p); }));
const THICK = new Map();
for (const [c, r] of SKEL.values()) for (const q of [[c + 1, r], [c, r + 1]]) if (!SKEL.has(key(...q)) && q[0] < COLS && q[1] < ROWS) THICK.set(key(...q), q);
const HEAT = [[2, 2], [7, 2], [13, 2], [21, 10], [21, 13], [2, 13]];   // 열지도 봉우리((7,2) 는 가짜)
const JUNC = [[9, 13], [9, 8]];                                       // 뼈대: 갈림 · 끝
// CAD 정답 선 목록: 윗변 한 줄 · 숨은선 하나는 판 137 이 칠하지 않았다
const CAD = [
  { a: [2, 2], b: [13, 2], ok: false, why: "split" }, { arc: true, ok: true }, { a: [21, 10], b: [21, 13], ok: true },
  { a: [21, 13], b: [9, 13], ok: true }, { a: [9, 13], b: [2, 13], ok: true }, { a: [2, 13], b: [2, 2], ok: true },
  { a: [9, 13], b: [9, 8], ok: true }, { a: [11, 9], b: [17, 9], hidden: true, ok: false, why: "miss" },
];
const cellXY = ([c, r]) => [BOARD.x + (c + 0.5) * G, BOARD.y + (r + 0.5) * G];
const arcPts = (map) => { const o = []; for (let a = -90; a <= 0; a += 3) { const t = a * Math.PI / 180; o.push(map([ARC.c + ARC.R * Math.cos(t), ARC.r + ARC.R * Math.sin(t)])); } return o; };

// ── 배치 ───────────────────────────────────────────────────────
const PLATE = { x: -222, y: -118, w: 386, d: 258, r: 10 };
const PLATE_H = 10, FOOT_H = 5, ST = 0.8;
const RAIL_L = BOARD.x - 24, RAIL_R = BOARD.x + BOARD.w + 10, RAIL_Y0 = BOARD.y - 20, RAIL_D = BOARD.d + 30;
const BEAM_Z = 20, PEN_DY = 8;                       // 펜 끝은 들보 앞 PEN_DY
const PARK = [BOARD.x + BOARD.w - 4, BOARD.y + 6];   // 쉬는 자리(오른쪽 위 구석)
const PR = { x: 0, y: -106, w: 152, d: 48, r: 3 }, PR_H = 16;   // 인쇄기
const TAPE = { x: 4, w: 146 }, TAPE_Y = PR.y + PR.d, ROWH = 12, LEAD = 5;
const CS = 0.72, CARD = { x: -200, y: 46, w: BOARD.w * CS, d: BOARD.d * CS, r: 1 };
const HOLD = { x: CARD.x - 4, y: CARD.y - 11, w: CARD.w + 8, d: CARD.d + 31, r: 2 };
const cardPt = ([x, y]) => [CARD.x + (x - BOARD.x) * CS, CARD.y + (y - BOARD.y) * CS];
const cardCell = (p) => cardPt(cellXY(p));
const KEYS = { x: -44, y: 60, w: 136, d: 20, r: 2 }, NKEY = 7, KEY_W = 16;

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [RAIL_L, RAIL_Y0, BEAM_Z + 4], [RAIL_R, RAIL_Y0, BEAM_Z + 4]], WIDTH, HEIGHT, { pad: 26, azimuth: 60, elevation: 40 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const T = (x, y, z, text, size, tone = "mid", anchor = "middle") => k.faceTextSvg(k.topMatrix([x, y], z, P, "x"), text, { size, tone, anchor });
const depth = (x, y, z = 0) => k.depthOf([x, y, z], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth(a[0], a[1]) - depth(b[0], b[1]));
const quad = (x0, y0, x1, y1, z) => k.onTop([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], z, P, true);
const cellQuad = ([c, r], z, m = 0.6) => quad(BOARD.x + c * G + m, BOARD.y + r * G + m, BOARD.x + (c + 1) * G - m, BOARD.y + (r + 1) * G - m, z);

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
  // 자 두 개 — 칸마다 눈금, 5 칸마다 큰 눈금
  const strip = { x: BOARD.x, y: BOARD.y - 13, w: BOARD.w, d: 7, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 6, strip.x + strip.w - 6, G, 5, strip.y + strip.d - 0.8, 0.6, [-2, -3.6], P);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  const side = { x: BOARD.x - 13, y: BOARD.y, w: 7, d: BOARD.d, r: 1 };
  o.push(S(k.slabOf(side, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const s2 = k.topTicks(side.y + 6, side.y + side.d - 6, G, 5, side.x + side.w - 0.8, 0.6, [-2, -3.6], P, "y");
  if (s2 && s2.minor) o.push(L(s2.minor, { tone: "lo" }), L(s2.major, { tone: "mid" }));
  // 이름판 — 세 줄은 인쇄 글자
  const plate = { x: 102, y: 66, w: 46, d: 11, r: 1.2 };
  o.push(S(k.slabOf(plate, 0, 0.8, P, 4), { tone: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(plate, 1.6), 0.8, P), { tone: "faint" }));
  [[5, 34], [5, 24], [5, 29]].forEach(([dx, len], i) => o.push(L(k.lineOnTop([plate.x + dx, plate.y + 2.8 + i * 2.6], [plate.x + dx + len, plate.y + 2.8 + i * 2.6], 0.8, P), { tone: "lo", free: true })));
  o.push(D([at([plate.x + 2.4, plate.y + plate.d / 2, 0.8]), at([plate.x + plate.w - 2.4, plate.y + plate.d / 2, 0.8])], { size: 0.45 }));
  return o.join("");
}
function board() {   // 화소판: 종이 + 격자 + 두꺼운 획 · 뼈대 칸 · 열지도 · 마디 · 맞춘 선
  const o = [S(k.slabOf(BOARD, 0, ST, P, 4), { tone: "hi", crease: "lo" })];
  const z = ST + 0.02;
  const grid = [];
  for (let c = 1; c < COLS; c++) grid.push(k.lineOnTop([BOARD.x + c * G, BOARD.y], [BOARD.x + c * G, BOARD.y + BOARD.d], z, P));
  for (let r = 1; r < ROWS; r++) grid.push(k.lineOnTop([BOARD.x, BOARD.y + r * G], [BOARD.x + BOARD.w, BOARD.y + r * G], z, P));
  o.push(L(grid.join(""), { tone: "faint" }));
  o.push(`<path class="ink-cell" data-part="thick" d="${[...THICK.values()].map((p) => cellQuad(p, z + 0.02)).join("")}"/>`);
  // 뼈대 칸 — 가지마다 따라간 시각을 붙이려고 칸마다 따로
  for (const [s, p] of SKEL) o.push(`<path class="ink-cell" data-cell="${s}" d="${cellQuad(p, z + 0.02)}"/>`);
  // 열지도: 봉우리마다 번진 빨강 두 겹
  o.push(`<g data-part="heat">${HEAT.map((p) => { const [x, y] = cellXY(p); return `<path class="heat" d="${k.ring(x, y, G * 1.5, z + 0.03, P, 28)}"/><path class="heat" d="${k.ring(x, y, G * 0.85, z + 0.03, P, 24)}"/>`; }).join("")}</g>`);
  // 맞춘 선: 현 · 휨 자 · 직선/원호
  const zf = z + 0.08;
  FIT.forEach((f, i) => {
    o.push(`<g data-chord="${i}" style="opacity:0">${L(k.lineOnTop(cellXY(f.a), cellXY(f.b), zf, P), { tone: "lit", className: "chord" })}</g>`);
    const d = f.kind === "arc" ? k.onTop(arcPts((q) => [BOARD.x + (q[0] + 0.5) * G, BOARD.y + (q[1] + 0.5) * G]), zf, P) : k.lineOnTop(cellXY(f.a), cellXY(f.b), zf, P);
    o.push(`<path class="iso-line fit fit-${f.kind}" data-fit="${i}" style="opacity:0" d="${d}"/>`);
  });
  // 원호의 휨 자: 현 가운데 → 가장 먼 화소
  const fa = FIT[2], mid = [(fa.a[0] + fa.b[0]) / 2, (fa.a[1] + fa.b[1]) / 2];
  const [fx, fy] = cellXY(fa.far), [mx, my] = cellXY(mid);
  o.push(`<g data-part="sag" style="opacity:0">${L(k.lineOnTop([mx, my], [fx, fy], zf, P), { tone: "red", className: "sag" })}${D([at([fx, fy, zf])], { size: 1.6, tone: "lit" })}${T(BOARD.x + 15 * G, BOARD.y + 5.6 * G, zf, `휨 ${fa.bend} ≥ 2 → 원호`, 6.4, "hi", "end")}</g>`);
  o.push(`<g data-part="sag0" style="opacity:0">${T(BOARD.x + 10.4 * G, BOARD.y + 11 * G, zf, "휨 0 → 직선", 6.4, "hi", "start")}</g>`);
  // 원호 가운데 점(보관)
  o.push(`<g data-part="arcmid" style="opacity:0">${D([at([fx, fy, zf])], { size: 1.5, tone: "green" })}</g>`);
  // 마디: 열지도 봉우리 → 빨강 점 · 뼈대 갈림/끝 → 빨강 고리 점
  o.push(`<g data-part="node-heat" style="opacity:0">${D(HEAT.map((p) => at([...cellXY(p), zf + 0.02])), { size: 2.1, tone: "red" })}</g>`);
  o.push(`<g data-part="node-skel" style="opacity:0">${L(JUNC.map((p) => k.ring(...cellXY(p), 3.2, zf + 0.02, P, 20)).join(""), { tone: "red", className: "node-ring" })}${D(JUNC.map((p) => at([...cellXY(p), zf + 0.02])), { size: 1.6, tone: "red" })}</g>`);
  return o.join("");
}
function rails() {
  const o = [];
  for (const x of [RAIL_L, RAIL_R]) {
    const r = { x, y: RAIL_Y0, w: 7, d: RAIL_D, r: 1.5 };
    o.push(S(k.slabOf(r, 0, 4, P, 4, 0.5), { tone: "mid" }));
    o.push(L(k.lineOnTop([x + 3.5, RAIL_Y0 + 5], [x + 3.5, RAIL_Y0 + RAIL_D - 5], 4, P), { tone: "faint" }));
    for (const y of [RAIL_Y0 - 3, RAIL_Y0 + RAIL_D - 4]) {
      o.push(S(k.slabOf({ x: x - 2, y, w: 11, d: 7, r: 1.2 }, 0, 7, P, 3, 0.5), { tone: "mid" }));
      o.push(D([at([x + 1, y + 3.5, 7]), at([x + 6, y + 3.5, 7])], { size: 0.42 }));
    }
  }
  return o.join("");
}
// 들보는 쉬는 자리(PARK)의 y 에 짓고 y 로 옮긴다 · 머리는 PARK 의 x 에 짓고 들보째 + x 로 옮긴다
const BY = PARK[1] - PEN_DY;
function beam() {
  const o = [];
  for (const x of [RAIL_L, RAIL_R]) {   // 다리(수레)
    o.push(S(k.slabOf({ x: x - 1.5, y: BY - 6, w: 10, d: 12, r: 1.6 }, 4, 3, P, 3, 0.4), { tone: "mid" }));
    o.push(S(k.slabOf({ x: x + 0.5, y: BY - 3, w: 6, d: 6, r: 1 }, 7, BEAM_Z - 7, P, 3, 0.3), { tone: "mid" }));
  }
  o.push(S(k.slabOf({ x: RAIL_L - 1, y: BY - 3.5, w: RAIL_R - RAIL_L + 9, d: 7, r: 1.2 }, BEAM_Z, 4, P, 4, 0.5), { tone: "mid", inner: L(k.sideSeam({ x: RAIL_L - 1, y: BY - 3.5, w: RAIL_R - RAIL_L + 9, d: 7, r: 1.2 }, BEAM_Z + 2, P, 4), { tone: "faint" }) }));
  o.push(D([at([RAIL_L + 3.5, BY, BEAM_Z + 4]), at([RAIL_R + 3.5, BY, BEAM_Z + 4])], { size: 0.45 }));
  return o.join("");
}
function head() {
  const [hx] = PARK, py = PARK[1], o = [];
  // 펜(위아래로 들림): 몸통 · 끝(빛나는 점)
  o.push(`<g data-part="pen">${S(k.cylinder(hx, py, 1.6, 1.0, 1.2, P, 20, 0.3), { tone: "hi", lit: true })}${S(k.cylinder(hx, py, 0.7, 2.2, 9, P, 14), { tone: "mid", crease: "none" })}${S(k.cylinder(hx, py, 1.9, 11, 3, P, 20, 0.3), { tone: "mid" })}</g>`);
  // 머리 상자: 들보 앞에 걸린다
  const hb = { x: hx - 5.5, y: BY + 3.5, w: 11, d: PEN_DY - 1.5, r: 1.2 };
  o.push(S(k.slabOf(hb, 14, BEAM_Z + 7 - 14, P, 3, 0.5), { tone: "hi", crease: "lo" }));
  o.push(D(k.corners(hb, 1.8).map(([x, y]) => at([x, y, BEAM_Z + 7])), { size: 0.4 }));
  o.push(S(k.cylinder(hx, BY + 5.5, 1.8, BEAM_Z + 7, 1.6, P, 20, 0.3), { tone: "mid" }));
  return o.join("");
}
function printer() {   // 테이프 인쇄기: 몸통 · 뚜껑 이음 · 실패 창 · 손잡이 · 등 · 앞 틈
  const o = [S(k.slabOf(PR, 0, PR_H, P, 6, 0.8), { tone: "mid", inner: L(k.sideSeam(PR, 4, P, 6), { tone: "faint" }) })];
  const lid = k.insetPlan(PR, 3);
  o.push(L(k.planOutline(lid, PR_H, P, 4), { tone: "lo" }));
  o.push(D(k.corners(PR, 2.2).map(([x, y]) => at([x, y, PR_H])), { size: 0.45 }));
  o.push(T(PR.x + 7, PR.y + 13, PR_H, "토큰 = [뷰, 종류, 시작x, 시작y,", 7, "hi", "start"), T(PR.x + 21, PR.y + 23, PR_H, "끝x, 끝y, 휨, 숨은선?]", 7, "hi", "start"));
  // 실패 창 + 실패
  o.push(S(k.cylinder(PR.x + 16, PR.y + 37, 6.5, PR_H, 0.6, P, 36, 0.3), { tone: "lo" }));
  o.push(S(k.cylinder(PR.x + 16, PR.y + 37, 4.6, PR_H + 0.6, 1.6, P, 36, 0.3), { tone: "hi" }));
  o.push(L(k.ring(PR.x + 16, PR.y + 37, 1.6, PR_H + 2.2, P, 16), { tone: "lo" }));
  // 손잡이(돌기) · 등
  o.push(S(k.cylinder(PR.x + PR.w - 14, PR.y + 37, 5, PR_H, 3.4, P, 40, 0.5), { tone: "hi", crease: "lo", inner: L(k.knurl(PR.x + PR.w - 14, PR.y + 37, 5, PR_H + 0.6, PR_H + 3, 22, P), { tone: "faint" }) }));
  o.push(`<g data-part="led">${S(k.cylinder(PR.x + PR.w - 30, PR.y + 37, 2.4, PR_H, 1.2, P, 24, 0.3), { tone: "hi", className: "lens" })}</g>`);
  // 앞 틈(테이프가 나오는 곳)
  o.push(L(k.segment([TAPE.x - 1, PR.y + PR.d, 1.4], [TAPE.x + TAPE.w + 1, PR.y + PR.d, 1.4], P), { tone: "hi", className: "slot" }));
  return o.join("");
}
function tapes() {   // n 줄 찍힌 테이프 상태 0..8 — 가장 새 줄이 틈 쪽, 먼저 찍은 줄이 바깥쪽
  const clip = k.onTop([[TAPE.x - 6, TAPE_Y], [TAPE.x + TAPE.w + 6, TAPE_Y], [TAPE.x + TAPE.w + 6, TAPE_Y + 200], [TAPE.x - 6, TAPE_Y + 200]], 0.6, P, true);
  const o = [`<clipPath id="tape-clip"><path d="${clip}"/></clipPath><g clip-path="url(#tape-clip)">`];
  for (let n = 0; n <= TOKENS.length; n++) {
    const len = LEAD + n * ROWH + 2;
    const g = [S(k.slabOf({ x: TAPE.x, y: TAPE_Y - 8, w: TAPE.w, d: len + 8, r: 0.6 }, 0, 0.5, P, 2), { tone: "hi", crease: "none" })];
    for (let j = 0; j < n; j++) {
      const i = n - 1 - j, y = TAPE_Y + LEAD + j * ROWH + ROWH - 3;
      g.push(`<g data-row="${i}">${T(TAPE.x + 4, y, 0.5, TOKENS[i], 7.4, "hi", "start")}</g>`);
      if (j < n - 1) g.push(L(k.lineOnTop([TAPE.x, TAPE_Y + LEAD + (j + 1) * ROWH], [TAPE.x + TAPE.w, TAPE_Y + LEAD + (j + 1) * ROWH], 0.5, P), { tone: "faint" }));
    }
    o.push(`<g data-tape="${n}" style="display:none">${g.join("")}</g>`);
  }
  o.push(`</g>`);
  return o.join("");
}
function answer() {   // 정답 카드: CAD 선 목록(회색) · ⑦ 에 우리 선을 얹고 짝 고리
  const o = [S(k.slabOf(HOLD, 0, 2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(HOLD, 2).map(([x, y]) => at([x, y, 2])), { size: 0.42 }));
  o.push(S(k.slabOf(CARD, 2, 0.8, P, 4), { tone: "hi", crease: "lo" }));
  const z = 2.82, cad = [], hid = [];
  for (const c of CAD) {
    if (c.arc) cad.push(k.onTop(arcPts((q) => cardCell(q)), z, P));
    else (c.hidden ? hid : cad).push(k.lineOnTop(cardCell(c.a), cardCell(c.b), z, P));
  }
  o.push(L(cad.join(""), { tone: "mid", className: "cad" }), L(hid.join(""), { tone: "mid", dotted: true, className: "cad-hid" }));
  o.push(T(HOLD.x + 4, CARD.y - 2.6, 2, "정답 카드 · CAD 선 목록", 5.6, "mid", "start"));
  // 우리 선 얹기
  const ours = FIT.map((f) => f.kind === "arc" ? `<path class="iso-line fit fit-arc" d="${k.onTop(arcPts((q) => cardCell(q)), z + 0.05, P)}"/>` : `<path class="iso-line fit fit-line" d="${k.lineOnTop(cardCell(f.a), cardCell(f.b), z + 0.05, P)}"/>`);
  o.push(`<g data-part="ours" style="opacity:0">${ours.join("")}${D([at([...cardCell([7, 2]), z + 0.06])], { size: 1.5, tone: "red" })}</g>`);
  // 짝 고리: 맞음 = 검정 고리 · 쪼개짐 / 놓침 = 빨강 고리 + ×
  const rr = 3.4;
  const mids = CAD.map((c) => c.arc ? cardCell([ARC.c + ARC.R * Math.cos(-Math.PI / 4), ARC.r + ARC.R * Math.sin(-Math.PI / 4)]) : cardCell([(c.a[0] + c.b[0]) / 2, (c.a[1] + c.b[1]) / 2]));
  CAD.forEach((c, i) => {
    const [cx, cy] = c.why === "split" ? cardCell([7, 2]) : mids[i];
    const cross = c.ok ? "" : L(k.lineOnTop([cx + rr + 0.6, cy - rr - 3.6], [cx + rr + 3.6, cy - rr - 0.6], z, P) + k.lineOnTop([cx + rr + 0.6, cy - rr - 0.6], [cx + rr + 3.6, cy - rr - 3.6], z, P), { className: "check-x", free: true });
    const word = c.ok ? "" : (c.why === "split" ? T(cx - 1, cy + 9.5, z, "쪼개짐", 5.6, "mid", "start") : T(cx, cy + 9, z, "놓침", 5.6, "mid", "middle")).replace('class="iso-face-text"', 'class="iso-face-text red-text"');
    const miss = c.why === "miss" ? L(k.lineOnTop(cardCell(c.a), cardCell(c.b), z + 0.04, P), { dotted: true, className: "miss-line" }) : "";
    o.push(`<g data-check="${i}" data-ok="${c.ok ? 1 : 0}" style="opacity:0">${miss}<path class="iso-line ${c.ok ? "check-ok" : "check-no"}" d="${k.ring(cx, cy, rr, z, P, 24)}"/>${cross}${word}</g>`);
  });
  // 받침 아래 채점 줄(예시)
  const ry = CARD.y + CARD.d + 8;
  o.push(`<g data-part="score" style="opacity:0">${T(HOLD.x + 4, ry + 1.5, 2, "예시 채점 · 재현 6/8 · 정밀 6/8", 6, "hi", "start")}${T(HOLD.x + 4, ry + 10.5, 2, "종류 6/6 (짝 중 종류가 맞음)", 6, "hi", "start")}</g>`);
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

// ── 시간표 ─────────────────────────────────────────────────────
const LOOP = 41;
const TR0 = 11, TRB = 1.25, TRAVEL = 0.35;   // ④ 가지마다 1.25 초(이동 0.35 + 따라가기 0.9)
const PEN = [[0, ...PARK, 3, 0], [TR0, ...PARK, 3, 0]];   // [t, x, y, 들림, 부드럽게?]
const CELL_T = {};
BR.forEach((ch, i) => {
  const t0 = TR0 + i * TRB, s = cellXY(ch[0]);
  PEN.push([t0 + TRAVEL - 0.08, ...s, 3, 1], [t0 + TRAVEL, ...s, 0, 1]);
  ch.forEach((p, j) => {
    const tc = t0 + TRAVEL + 0.05 + (0.82 * j) / (ch.length - 1);
    PEN.push([tc, ...cellXY(p), 0, 0]);
    const s2 = key(...p); if (!(s2 in CELL_T)) CELL_T[s2] = tc;
  });
});
const TR1 = TR0 + BR.length * TRB;   // 21
PEN.push([TR1 + 0.15, ...cellXY(BR[7][BR[7].length - 1]), 3, 1], [TR1 + 1.2, ...PARK, 3, 1]);
const PR0 = 28, PRB = 0.7;            // ⑥ 토큰마다 0.7 초

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "판 140 벡터화를 XY 플로터와 테이프 인쇄기로 그린 그림. 확대한 화소판에 칠한 두꺼운 획이 1 화소 뼈대로 깎이고, 꼭짓점 열지도 봉우리와 뼈대의 갈림·끝 화소에 빨강 마디가 찍힌다. 펜이 마디 사이 화소 사슬을 하나씩 걷고, 현에서 가장 먼 화소까지의 휨이 2 화소 이상이면 초록 원호, 아니면 파랑 직선으로 맞춘다. 인쇄기는 선마다 토큰 한 줄을 찍는다. 정답 카드에서 CAD 선 목록과 짝을 맞추고, 가짜 마디로 쪼개진 선과 놓친 숨은선은 빨강으로 표시한다.",
  body: [base(), answer(), printer(), tapes(), board(), rails(), `<g data-part="beam">${beam()}</g>`, `<g data-part="head">${head()}</g>`, steps()],
});

const live = `
const P = ${JSON.stringify(P)};
const PARK = ${JSON.stringify(PARK)}, PEN = ${JSON.stringify(PEN)}, CELL_T = ${JSON.stringify(CELL_T)};
const LOOP = ${LOOP}, TR0 = ${TR0}, TRB = ${TRB}, TR1 = ${TR1}, PR0 = ${PR0}, PRB = ${PRB}, NT = ${TOKENS.length}, ROWH = ${ROWH};
const svg = document.querySelector(".iso-stage svg"), stage = document.querySelector(".iso-stage");
const $ = (s) => svg.querySelector(s), $$ = (s) => [...svg.querySelectorAll(s)];
const beam = $('[data-part="beam"]'), head = $('[data-part="head"]'), pen = $('[data-part="pen"]');
const thick = $('[data-part="thick"]'), heat = $('[data-part="heat"]'), nodeHeat = $('[data-part="node-heat"]'), nodeSkel = $('[data-part="node-skel"]');
const sag = $('[data-part="sag"]'), sag0 = $('[data-part="sag0"]'), arcmid = $('[data-part="arcmid"]'), led = $('[data-part="led"]');
const ours = $('[data-part="ours"]'), score = $('[data-part="score"]');
const cells = $$("[data-cell]"), chords = $$("[data-chord]"), fits = $$("[data-fit]").sort((a, b) => a.dataset.fit - b.dataset.fit);
const tapesG = $$("[data-tape]").sort((a, b) => a.dataset.tape - b.dataset.tape), checks = $$("[data-check]");
const keys = $$("[data-step]").sort((a, b) => a.dataset.step - b.dataset.step);
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const ramp = (t, t0, d = 0.5) => ease((t - t0) / d);
const win = (t, t0, t1, d = 0.5) => ramp(t, t0, d) * (1 - ramp(t, t1, d));
const END = LOOP - 1.4;   // 되감기 시작
function penAt(t) {
  if (t <= PEN[0][0]) return PEN[0].slice(1, 4);
  for (let i = 1; i < PEN.length; i++) if (t <= PEN[i][0]) {
    const a = PEN[i - 1], b = PEN[i], u0 = (t - a[0]) / Math.max(1e-6, b[0] - a[0]), u = b[4] ? ease(u0) : u0;
    return [a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u];
  }
  return PEN[PEN.length - 1].slice(1, 4);
}
function text(t) {
  if (t < 3.5) return "① 입력: 판 137 이 화소마다 칠한 선 도면(확대)";
  if (t < 7) return "② 가늘게: 두꺼운 획을 1 화소 뼈대로 깎는다";
  if (t < 9.4) return "③ 마디: 꼭짓점 열지도의 봉우리에 빨강 점";
  if (t < TR0) return "③ 마디: 뼈대의 갈림 화소 · 끝 화소도 마디";
  if (t < TR1) return "④ 따라가기: 펜이 마디에서 마디까지 화소 사슬을 걷는다";
  if (t < 23.4) return "⑤ 맞추기: 양 끝을 잇는 현에서 가장 먼 화소 = 휨";
  if (t < PR0) return "⑤ 휨 ≥ 2 px → 원호(가운데 점 보관) · 아니면 직선";
  if (t < PR0 + NT * PRB + 0.2) return "⑥ 찍기: 선 하나 = 토큰 한 줄 · " + Math.min(NT, Math.max(1, Math.ceil((t - PR0) / PRB))) + "/" + NT;
  if (t < 34.6) return "⑦ 채점: CAD 정답 선 목록과 짝을 맞춘다";
  if (t < 35.8) return "⑦ 가짜 마디가 선을 쪼갬 · 안 칠한 숨은선 놓침 → 빨강";
  if (t < 37.6) return "⑦ 재현 = 정답 중 찾은 몫 · 정밀 = 우리 선 중 맞은 몫";
  return "칠한 화소를 꼭짓점에서 끊어, 선마다 숫자 한 줄로 적는다";
}
function draw(t) {
  const out = 1 - ramp(t, END, 0.8);
  // 플로터
  const [px, py, lift] = penAt(t);
  beam.setAttribute("transform", translateAlong(P, [0, py - PARK[1], 0]));
  head.setAttribute("transform", translateAlong(P, [px - PARK[0], py - PARK[1], 0]));
  pen.setAttribute("transform", translateAlong(P, [0, 0, lift]));
  // ① ② 두꺼운 획 → 뼈대
  thick.style.opacity = (1 - ramp(t, 4.0, 1.8)) + ramp(t, END, 0.8);
  // ③ 열지도 · 마디
  heat.style.opacity = 0.9 * win(t, 7.0, TR0 + 0.5, 0.9);
  nodeHeat.style.opacity = ramp(t, 8.1, 0.5) * out;
  nodeSkel.style.opacity = ramp(t, 9.6, 0.5) * out;
  // ④ 뼈대 칸: 따라가기 전엔 흐리게 · 펜이 지나가면 진하게 · ⑤ 맞춘 뒤 다시 흐리게
  for (const c of cells) {
    const tc = CELL_T[c.dataset.cell];
    const dim = t < TR0 ? ramp(t, TR0 - 0.5, 0.5) : t < tc ? 1 : t < 24.2 ? 0 : ramp(t, 24.2, 0.8);
    c.style.opacity = 1 - 0.72 * dim * out;
  }
  // ⑤ 현 · 휨 · 맞춘 선
  chords.forEach((g, i) => g.style.opacity = win(t, TR1 + 0.1 + i * 0.1, 24.4, 0.4));
  sag.style.opacity = win(t, 22.2, PR0, 0.5);
  sag0.style.opacity = win(t, 22.9, PR0, 0.5);
  arcmid.style.opacity = ramp(t, 24.6, 0.5) * out;
  fits.forEach((f, i) => {
    f.style.opacity = ramp(t, 24.2 + i * 0.12, 0.5) * out;
    f.toggleAttribute("data-now", t >= PR0 + i * PRB && t < PR0 + (i + 1) * PRB);
  });
  // ⑥ 테이프: n 줄 상태를 한 줄 길이만큼 밀어낸다
  const n = t < PR0 ? 0 : Math.min(NT, Math.floor((t - PR0) / PRB) + 1);
  const slide = n ? 1 - ramp(t, PR0 + (n - 1) * PRB, 0.35) : 0;
  tapesG.forEach((g, i) => { g.style.display = i === n ? "" : "none"; });
  tapesG[n].setAttribute("transform", translateAlong(P, [0, -ROWH * slide, 0]));
  tapesG[n].style.opacity = t >= END ? out : 1;
  led.toggleAttribute("data-on", t >= PR0 && t < PR0 + NT * PRB && ((t - PR0) % PRB) < 0.4);
  // ⑦ 정답 카드
  ours.style.opacity = ramp(t, 32.6, 0.6) * out;
  checks.forEach((g, i) => { const t0 = g.dataset.ok === "1" ? 33.4 + i * 0.15 : 34.8; g.style.opacity = ramp(t, t0, 0.35) * out; });
  score.style.opacity = ramp(t, 35.8, 0.5) * out;
  const step = t < 3.5 ? 0 : t < 7 ? 1 : t < TR0 ? 2 : t < TR1 ? 3 : t < PR0 ? 4 : t < 32.4 ? 5 : t < END ? 6 : -1;
  keys.forEach((g, i) => g.toggleAttribute("data-active", i === step));
  readout.textContent = text(t);
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible && !held ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__seek = (t) => { held = true; cancelAnimationFrame(frame); frame = 0; draw(((t % LOOP) + LOOP) % LOOP); };   // 녹화용
if (still.matches) draw(36.5); else draw(0);
`;
const css = `<style>
.iso{--k-st:var(--anatomy-blue);--k-cu:var(--anatomy-green);--k-v:var(--anatomy-red)}
.ink-cell{fill:var(--anatomy-hi);stroke:none}
.heat{fill:var(--k-v);fill-opacity:.16;stroke:none}
.iso-dots[data-tone="red"] circle{fill:var(--k-v);opacity:1}.iso-dots[data-tone="green"] circle{fill:var(--k-cu);opacity:1}.iso-dots[data-tone="lit"] circle{fill:var(--anatomy-lit);opacity:1}
.iso-line.node-ring{stroke:var(--k-v);stroke-width:1}
.iso-line.chord{stroke-width:.9;stroke-dasharray:2 1.6}
.iso-line.sag{stroke:var(--k-v);stroke-width:1.2}
.iso-line.fit{stroke-width:2.2}.fit-line{stroke:var(--k-st)}.fit-arc{stroke:var(--k-cu)}
.iso-line.fit[data-now]{stroke-width:3.6}
.iso-line.cad{stroke-width:2.6;stroke:var(--anatomy-lo)}
.iso-line.cad-hid{stroke-width:1.6;stroke:var(--anatomy-mid)}
.iso-line.miss-line{stroke:var(--k-v);stroke-width:1.8}
.slot{stroke-width:1.6}
[data-part="led"][data-on] .lens>.iso-top{fill:var(--k-v)}
.check-ok{stroke:var(--anatomy-lit);stroke-width:1.1}.iso-line.check-no,.iso-line.check-x{stroke:var(--k-v);stroke-width:1.3}
.iso-face-text.red-text{fill:var(--k-v);font-weight:700}
[data-step][data-active] .iso-edge{stroke:var(--anatomy-lit)}[data-step][data-active] .iso-top{fill:var(--anatomy-lit-top)}
[data-step][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
</style>`;
const body = k.plateHtml({
  fig: "그림 4", title: "벡터화 · 판 140",
  hint: `저절로 돈다 · 한 바퀴 ${LOOP} 초`,
  readout: "① 입력: 판 137 이 화소마다 칠한 선 도면(확대)",
  keys: [
    { mark: "flat", label: "번호판 ① 칠한 화소 ② 뼈대 ③ 마디 ④ 따라가기 ⑤ 맞추기 ⑥ 토큰 찍기 ⑦ 채점" },
    { mark: "raised", label: "XY 플로터 = 사슬 따라가기 · 펜이 마디에서 마디까지 뼈대 화소를 걷는다" },
    { mark: "lit", label: "빨강 = 꼭짓점(열지도 봉우리 점 · 뼈대 갈림/끝 고리) · 파랑 = 직선 · 초록 = 원호(휨 ≥ 2 px)" },
    { mark: "flat", label: "테이프 인쇄기 = 선 하나에 토큰 한 줄 [뷰, 종류, 시작x, 시작y, 끝x, 끝y, 휨, 숨은선?]" },
    { mark: "dotted", label: "정답 카드 = CAD 선 목록 · 짝이 맞으면 검정 고리, 쪼개짐 · 놓침은 빨강" },
  ],
  caption: "판 140 은 학습 없이 계산만 한다. 판 137 CNN 이 128×128 선 도면에 화소마다 칠한 선(종류 포함)과 꼭짓점 열지도를 받아, 획을 1 화소 뼈대로 깎고, 열지도 봉우리와 뼈대의 갈림 · 끝 화소를 마디로 삼아 마디 사이 화소 사슬을 하나씩 떼어 낸다. 사슬마다 양 끝을 잇는 현에서 가장 먼 화소까지 거리를 휨으로 재어 2 px 이상이면 원호(가운데 점 보관), 아니면 직선으로 맞추고, 선 하나를 토큰 [뷰, 종류, 시작x, 시작y, 끝x, 끝y, 휨, 숨은선?] 한 줄로 적는다. 채점은 CAD 정답 선 목록과 짝을 맞춰 재현(정답 중 찾은 몫) · 정밀(우리 선 중 맞은 몫) · 종류(짝 중 종류가 맞은 몫)를 잰다. 판 140 은 아직 돌지 않았다 — 화소판은 설명용 24×15 격자이고 좌표는 그 칸 번호이며, 가짜 마디 · 놓친 숨은선 · 채점 분수는 채점 방식을 보이려 넣은 예시다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="판 140 벡터화 동작 그림">${svg}</div>`,
});
mkdirSync(OUT, { recursive: true });
const html = join(OUT, theme === "light" ? "vec140-light.html" : "vec140.html");
writeFileSync(html, k.pageHtml({ title: "판 140 벡터화", theme, body, script: kitScript() + live }));
console.log("wrote", html, "· 휨", FIT.map((f) => f.bend).join(" "), "· 뼈대", SKEL.size, "· 두꺼운 덧칸", THICK.size);

if (RECORD) {   // 8 fps · 2 배 · light → mp4(libx264 yuv420p crf20) + gif(800 폭, 같은 프레임)
  const FPS = 8, DRIVE = "C:/Users/zesky/.claude/skills/anatomy/scripts/drive.mjs", FR = join(OUT, "frames");
  mkdirSync(FR, { recursive: true }); for (const f of readdirSync(FR)) unlinkSync(join(FR, f));   // rmSync 재귀는 한글 경로에서 node 가 죽었다
  const acts = [];
  for (let i = 0; i < LOOP * FPS; i++) acts.push(["eval", `__seek(${(i / FPS).toFixed(3)})`], ["shot", `frames/f${String(i).padStart(3, "0")}.png`, null, 2]);
  writeFileSync(join(OUT, "frames.json"), JSON.stringify(acts));
  execFileSync(process.execPath, [DRIVE, html, "--actions", "frames.json"], { cwd: OUT, stdio: ["ignore", "ignore", "inherit"] });
  const mp4 = join(HERE, "vec140.mp4"), gif = join(HERE, "vec140.gif");
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], { stdio: "inherit" });
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse", gif], { stdio: "inherit" });
  console.log("wrote", mp4, gif);
}
