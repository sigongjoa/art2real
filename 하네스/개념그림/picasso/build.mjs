// PICASSO (Karadeniz 외, WACV 2025, arXiv 2407.13394v2) 핵심 동작 — 16 칸 배출기: 질의 칸마다 프리미티브 하나(또는 빈칸)를 밀어내 도면판에 내려놓고, 헝가리안 매칭이 칸과 정답을 일대일로 잇는다.
// 쓴 사실(출처):
//   입력 128×128 이진 스케치 이미지 — 논문 §5 Implementation Details · §3
//   스케치당 프리미티브 최대 n = 16 — §5 · 출력은 n 개 집합(8n×73 토큰 행렬) — §3, §4.2
//   프리미티브 넷: line(시작 · 끝점) · arc(시작 · 중간 · 끝점) · circle(중심 · 반지름) · point(좌표) — §3
//   프리미티브 하나 = 토큰 8 개 · 토큰 0 = 패딩(빈칸) · 매개변수는 64 단계 양자화(토큰 7..70) · 보조선 표시 토큰 71/72 — §3
//   헝가리안 매칭: n 개 위의 일대일 대응 π 중 Σ L_param(p_i, p̂_π(i)) 최소, L_param = 토큰 교차 엔트로피 — §4.4 식 (2)
//   렌더링 자기지도: 고정된 SRN 이 예측 토큰을 그림으로 그려 입력과 다중 스케일 L2 — §4.3 식 (1) (캡션에만)
//   데이터: SketchGraphs 거른 뒤 약 153 만 스케치 — §5 Dataset · 백본 ResNet34 U-Net + 트랜스포머 인코더 · 디코더 각 4 층 8 헤드 256 차원 — §5
//   교차 정리 문서: claudedocs/research_선검출모델_20261023.md §2
// 그림 속 도면(9 프리미티브 · 빈칸 7)과 칸 배정 순서는 설명용으로 지은 것이다(논문 예시 아님).
// 사용: node build.mjs [--light] → picasso.html / picasso-light.html
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

const PLATE = { x: -162, y: -101, w: 280, d: 209, r: 8 };
const PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -60, y: -30, w: 120, d: 120, r: 1.5 };   // 128×128 화소 = 120 단위
const SHEET_T = 0.8;
const PX = 120 / 128;
const W = ([px, py]) => [SHEET.x + px * PX, SHEET.y + py * PX], WS = W, PXS = PX;   // 화소(위가 0 = 뒤쪽) → 판 좌표
const N = 16, PITCH = 13, TX = (i) => -97.5 + i * PITCH;
const RACK = { x: -108, y: -94, w: 216, d: 32, r: 2 }, RACK_H = 3;
const FLOOR_Y = -90, FLOOR_D = 26, FLOOR_Z = RACK_H + 1.5, MOUTH_Y = FLOOR_Y + FLOOR_D;   // 칸 입구 = 앞(+y)
const REST_Y = MOUTH_Y - 6;                          // 칸 안 토큰 자리
const PEG_RAIL = { x: -108, y: -48, w: 216, d: 16, r: 2 }, PEG_Y = -42, PEG_Z = 2, PEG_H = 5, PEG_R = 3.6;
const TOK_H = 1.6, TOK_W = 2.6;

// ── 도면: 선 5 · 호 2 · 원 1 · 점 1 (화소 좌표) — 겹침: 가로 · 세로 중심선이 원과 서로를, 세로선이 밑변을 지난다
const PRIMS = [
  { id: "L1", type: "line", p: [[16, 96], [112, 96]], z: 0 },
  { id: "L2", type: "line", p: [[16, 96], [16, 40]], z: 0 },
  { id: "L3", type: "line", p: [[112, 96], [112, 40]], z: 0 },
  { id: "A4", type: "arc", p: [[16, 40], [64, 14], [112, 40]], z: 0 },
  { id: "A5", type: "arc", p: [[40, 44], [64, 32], [88, 44]], z: 0 },
  { id: "C6", type: "circle", c: [64, 66], r: 19, z: 0 },
  { id: "L7", type: "line", p: [[30, 66], [98, 66]], z: TOK_H },
  { id: "L8", type: "line", p: [[64, 30], [64, 110]], z: TOK_H * 2 },
  { id: "P9", type: "point", c: [64, 66], z: TOK_H * 3 },
];
// 칸 i 가 낸 것(-1 = 빈칸). 순서는 일부러 섞었다 — 집합이라 칸 순서에 뜻이 없다
const SLOT = [0, -1, 5, 6, -1, 3, 8, -1, 1, 4, -1, 7, -1, 2, -1, -1];
// 정답 목록(못 줄) — 종류별로 놓고, 남는 7 자리는 패딩
const GT = [0, 1, 2, 6, 7, 3, 4, 5, 8, -1, -1, -1, -1, -1, -1, -1];
// 매칭 결과 π: 칸 i → 못 j (프리미티브는 같은 것끼리, 빈칸은 패딩끼리)
const MATCH = (() => { const pads = GT.map((g, j) => (g < 0 ? j : -1)).filter((j) => j >= 0); let q = 0; return SLOT.map((s) => (s >= 0 ? GT.indexOf(s) : pads[q++])); })();
const KIND = { line: "선", arc: "호", circle: "원", point: "점" };
// 모델의 답: 9 개 중 8 개는 정답과 같고, 작은 호(A5)만 직선으로 잘못 낸다(틀림 하나를 보이려고 지은 예)
const PRED = PRIMS.map((p) => (p.id === "A5" ? { id: "A5x", type: "line", p: [[40, 44], [88, 44]], z: 0 } : p));
const OK = PRIMS.map((p, i) => PRED[i].type === p.type);
// 정답 카드(왼쪽): 같은 도면을 작게
const CARD = { x: -154, y: -14, w: 72, d: 72, r: 2 }, CARD_Z = 2.2;
const CPX = (CARD.w - 8) / 128, CW = ([px, py]) => [CARD.x + 4 + px * CPX, CARD.y + 4 + py * CPX];
const STEPS = [-146, -127, -108, -89].map((x) => [x, 78]);

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...k.boxCorners(RACK, 0, 14)], WIDTH, HEIGHT, { pad: 14, azimuth: 58 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const depth2 = ([x, y]) => k.depthOf([x, y, 0], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth2(a) - depth2(b));

// ── 기하 도우미
function circle3([ax, ay], [bx, by], [cx, cy]) {
  const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
  const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
  const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;
  return [ux, uy, Math.hypot(ax - ux, ay - uy)];
}
function arcPts(a, m, b, steps = 40) {   // 세 점을 지나는 호의 점열(판 좌표)
  const [cx, cy, r] = circle3(a, m, b);
  const ang = (p) => Math.atan2(p[1] - cy, p[0] - cx);
  let a0 = ang(a), am = ang(m), a1 = ang(b);
  const norm = (x) => ((x % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  let span = norm(a1 - a0); if (norm(am - a0) > span) span -= 2 * Math.PI;
  return { c: [cx, cy], r, a0, span, pts: Array.from({ length: steps + 1 }, (_, i) => { const t = a0 + span * i / steps; return [cx + r * Math.cos(t), cy + r * Math.sin(t)]; }) };
}
function capsule(a, b, w, steps = 8) {
  const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy), th = Math.atan2(dy, dx), h = w / 2, o = [];
  for (let i = 0; i <= steps; i++) { const t = th - Math.PI / 2 + Math.PI * i / steps; o.push([b[0] + h * Math.cos(t), b[1] + h * Math.sin(t)]); }
  for (let i = 0; i <= steps; i++) { const t = th + Math.PI / 2 + Math.PI * i / steps; o.push([a[0] + h * Math.cos(t), a[1] + h * Math.sin(t)]); }
  return o;
}
function band(c, r, a0, span, w, steps) {   // 호 띠(바깥 → 안쪽 거꾸로)
  const out = [], inn = [];
  for (let i = 0; i <= steps; i++) { const t = a0 + span * i / steps; out.push([c[0] + (r + w / 2) * Math.cos(t), c[1] + (r + w / 2) * Math.sin(t)]); inn.push([c[0] + (r - w / 2) * Math.cos(t), c[1] + (r - w / 2) * Math.sin(t)]); }
  return [...out, ...inn.reverse()];
}
// 프리미티브 → 판 위 좌표 점열 · 중심
function geomOf(pr, W = WS, PX = PXS) {
  if (pr.type === "line") { const a = W(pr.p[0]), b = W(pr.p[1]); return { pts: [a, b], c: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], size: Math.hypot(b[0] - a[0], b[1] - a[1]) }; }
  if (pr.type === "arc") { const A = arcPts(W(pr.p[0]), W(pr.p[1]), W(pr.p[2])); const xs = A.pts.map((p) => p[0]), ys = A.pts.map((p) => p[1]); return { ...A, cc: A.c, c: [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2], size: Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) }; }
  if (pr.type === "circle") { const c = W(pr.c), r = pr.r * PX; return { c, r, size: 2 * r }; }
  return { c: W(pr.c), size: 5 };
}
const GEO = PRIMS.map((p) => geomOf(p)), PGEO = PRED.map((p) => geomOf(p)), CGEO = PRIMS.map((p) => geomOf(p, CW, CPX));
function sketchD(pr, G, z, dot = 1.2) {   // 도형 하나를 면 위 선으로
  if (pr.type === "line") return k.lineOnTop(G.pts[0], G.pts[1], z, P);
  if (pr.type === "arc") return k.onTop(G.pts, z, P);
  if (pr.type === "circle") return k.ring(G.c[0], G.c[1], G.r, z, P, 64);
  return k.ring(G.c[0], G.c[1], dot, z, P, 16);
}

// ── 받침
function base() {
  const o = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 20))) {
    o.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    o.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  o.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  o.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  o.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  o.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // 앞 자(가로 128 화소) · 왼쪽 자(세로) — 8 화소마다 눈금, 32 화소마다 큰 눈금, 자 가장자리에서 자람
  const fr = { x: SHEET.x - 2, y: SHEET.y + SHEET.d + 4, w: SHEET.w + 4, d: 7, r: 1 };
  o.push(S(k.slabOf(fr, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  let t = k.topTicks(SHEET.x, SHEET.x + SHEET.w + 0.01, 8 * PX, 4, fr.y + 0.8, 0.6, [2, 3.6], P);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  const lr = { x: SHEET.x - 11, y: SHEET.y - 2, w: 7, d: SHEET.d + 4, r: 1 };
  o.push(S(k.slabOf(lr, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  t = k.topTicks(SHEET.y, SHEET.y + SHEET.d + 0.01, 8 * PX, 4, lr.x + lr.w - 0.8, 0.6, [-2, -3.6], P, "y");
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  // 이름판(오른쪽 앞) — 세 줄은 인쇄 글자
  const plate = { x: 70, y: 78, w: 40, d: 12, r: 1.2 };
  o.push(S(k.slabOf(plate, 0, 0.8, P, 4), { tone: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(plate, 1.6), 0.8, P), { tone: "faint" }));
  [[5, 30], [5, 22], [5, 26]].forEach(([dx, len], i) => o.push(L(k.lineOnTop([plate.x + dx, plate.y + 3.4 + i * 2.6], [plate.x + dx + len, plate.y + 3.4 + i * 2.6], 0.8, P), { tone: "lo", free: true })));
  o.push(D([at([plate.x + 2.4, plate.y + plate.d / 2, 0.8]), at([plate.x + plate.w - 2.4, plate.y + plate.d / 2, 0.8])], { size: 0.45 }));
  return o.join("");
}
// ── 도면판: 종이 + 8 화소 격자 + 입력 스케치(새긴 선) + 모서리 누름쇠
function sheet() {
  const o = [S(k.slabOf(SHEET, 0, SHEET_T, P, 4), { tone: "hi", crease: "lo" })];
  const g = [];
  for (let i = 1; i < 16; i++) {
    const x = SHEET.x + i * 8 * PX, y = SHEET.y + i * 8 * PX;
    g.push(k.lineOnTop([x, SHEET.y], [x, SHEET.y + SHEET.d], SHEET_T, P), k.lineOnTop([SHEET.x, y], [SHEET.x + SHEET.w, y], SHEET_T, P));
  }
  o.push(L(g.join(""), { tone: "faint" }));
  const sk = PRIMS.map((pr, i) => sketchD(pr, GEO[i], SHEET_T)).join("");
  o.push(L(sk, { tone: "mid" }));
  // 끝점 점(CAD 스케치처럼 선 · 호 끝마다)
  const ends = PRIMS.flatMap((pr, i) => pr.type === "line" ? GEO[i].pts : pr.type === "arc" ? [GEO[i].pts[0], GEO[i].pts.at(-1)] : []);
  o.push(D(ends.map(([x, y]) => at([x, y, SHEET_T])), { size: 0.6, tone: "mid" }));
  for (const [x, y] of byDepth(k.corners(SHEET, 0))) {
    const c = { x: x - 4, y: y - 4, w: 8, d: 8, r: 1.6 };
    o.push(S(k.slabOf(c, SHEET_T, 1.4, P, 4, 0.4), { tone: "mid" }));
    o.push(D([at([x, y, SHEET_T + 1.4])], { size: 0.5 }));
  }
  return o.join("");
}
// ── 배출기: 16 칸(바닥 · 뒷벽 · 밀대 · 손잡이) + 칸마다 토큰 8 개 점
function rack() {
  const o = [S(k.slabOf(RACK, 0, RACK_H, P, 4, 0.5), { tone: "lo" })];
  for (const x of [RACK.x + 3, RACK.x + RACK.w - 3]) o.push(D([at([x, RACK.y + 3, RACK_H]), at([x, RACK.y + RACK.d - 3, RACK_H])], { size: 0.45 }));
  const trays = byDepth(Array.from({ length: N }, (_, i) => [TX(i), FLOOR_Y, i]));
  const pushers = [];
  for (const [x, , i] of trays) {
    const fl = { x: x - 5.5, y: FLOOR_Y, w: 11, d: FLOOR_D, r: 1 };
    o.push(S(k.slabOf(fl, RACK_H, 1.5, P, 3, 0.3), { tone: "mid" }));
    o.push(L(k.lineOnTop([x - 5.5, REST_Y + 3.6], [x + 5.5, REST_Y + 3.6], FLOOR_Z, P), { tone: "faint" }));   // 앞 문턱 홈(바닥 끝에서 끝까지)
    const wall = { x: x - 5.5, y: FLOOR_Y, w: 11, d: 4, r: 0.8 };
    o.push(S(k.slabOf(wall, FLOOR_Z, 9, P, 3, 0.4), { tone: "mid" }));
    // 토큰 8 개 = 뒷벽 위 점 여덟(프리미티브 하나의 토큰 수)
    o.push(D(Array.from({ length: 8 }, (_, q) => at([x - 4.2 + q * 1.2, FLOOR_Y + 2, FLOOR_Z + 9])), { size: 0.38, tone: "lo" }));
    // 밀대: 원점에 짓고 칸 자리로 옮김
    const ps = { x: x - 4, y: FLOOR_Y + 6, w: 8, d: 5, r: 0.8 };
    const knob = k.cylinder(x, FLOOR_Y + 8.5, 1.4, FLOOR_Z + 4, 2.4, P, 16, 0.3);
    o.push(`<g data-push="${i}">${S(k.slabOf(ps, FLOOR_Z, 4, P, 3, 0.4), { tone: "hi" })}${S(knob, { tone: "mid" })}</g>`);
    if (SLOT[i] < 0) {   // 빈칸: 칸 바닥에 남는 빈 패
      const card = { x: x - 3.4, y: REST_Y - 3, w: 6.8, d: 6, r: 0.8 };
      o.push(S(k.slabOf(card, FLOOR_Z, 0.6, P, 3), { tone: "lo", crease: "none" }));
      o.push(L(k.planOutline(k.insetPlan(card, 1.2), FLOOR_Z + 0.6, P), { tone: "faint" }));
    }
  }
  return o.join("");
}
// ── 정답 못 줄: 못마다 정답 하나의 종류 표시(패딩은 빈 고리)
function pegs() {
  const o = [S(k.slabOf(PEG_RAIL, 0, PEG_Z, P, 4, 0.5), { tone: "lo" })];
  o.push(L(k.planOutline(k.insetPlan(PEG_RAIL, 1.6), PEG_Z, P), { tone: "faint" }));
  for (const [x, , j] of byDepth(Array.from({ length: N }, (_, j) => [TX(j), PEG_Y, j]))) {
    const g = GT[j], top = PEG_Z + PEG_H;
    o.push(S(k.cylinder(x, PEG_Y, PEG_R + 0.9, PEG_Z, 1, P, 24), { tone: "lo" }));
    o.push(S(k.cylinder(x, PEG_Y, PEG_R, PEG_Z + 1, PEG_H - 1, P, 28, 0.4), { tone: g < 0 ? "mid" : "hi" }));
    const ty = g < 0 ? null : PRIMS[g].type;
    if (ty === "line") o.push(L(k.lineOnTop([x - 2.2, PEG_Y - 1.2], [x + 2.2, PEG_Y + 1.2], top, P), { tone: "mid", free: true }));
    else if (ty === "arc") o.push(L(k.onTop(Array.from({ length: 9 }, (_, q) => { const a = Math.PI * (0.15 + 0.7 * q / 8); return [x + 2.2 * Math.cos(a), PEG_Y - 1 + 2.2 * Math.sin(a)]; }), top, P), { tone: "mid", free: true }));
    else if (ty === "circle") o.push(L(k.ring(x, PEG_Y, 1.8, top, P, 20), { tone: "mid" }));
    else if (ty === "point") o.push(D([at([x, PEG_Y, top])], { size: 0.8, tone: "hi" }));
    else o.push(L(k.ring(x, PEG_Y, 1.6, top, P, 16), { tone: "faint" }));
    // 지금 짝지어지는 못: 밝은 머리 덮개
    o.push(`<g data-pl="${j}" style="opacity:0">${S(k.cylinder(x, PEG_Y, PEG_R, PEG_Z + 1, PEG_H - 1, P, 28, 0.4), { tone: "hi", lit: true })}</g>`);
    // 판정 표시(못 앞 레일 위): 맞음 = 점, 틀림 = ×
    const vy = PEG_Y + 6.4, bad = g >= 0 && !OK[g];
    const mark = bad
      ? L(k.lineOnTop([x - 1.6, vy - 1.6], [x + 1.6, vy + 1.6], PEG_Z, P) + k.lineOnTop([x - 1.6, vy + 1.6], [x + 1.6, vy - 1.6], PEG_Z, P), { tone: "lit", free: true })
      : D([at([x, vy, PEG_Z])], { size: 1.1, tone: "hi" });
    o.push(`<g data-v="${j}" style="opacity:0">${mark}</g>`);
  }
  return o.join("");
}
// ── 매칭 실: 칸 입구 → 못 머리
const MOUTH = (i) => [TX(i), MOUTH_Y - 0.4, FLOOR_Z];
const PEGTOP = (j) => [TX(j), PEG_Y, PEG_Z + PEG_H];
function threads() {
  return SLOT.map((_, i) => {
    const a = MOUTH(i), b = PEGTOP(MATCH[i]);
    return `<g data-th="${i}" style="opacity:0"><path class="iso-line" data-tone="mid" style="stroke-width:.7" d="${k.segment(a, b, P)}"/>${D([at(a), at(b)], { size: 0.7, tone: "mid" })}</g>`;
  }).join("");
}
// ── 토큰(프리미티브 조각): 착지 자리에서 짓고, 실시간으로 칸에서 날아와 펴짐
function tokenPaths(pr, G) {
  const z = SHEET_T + pr.z;
  if (pr.type === "line") return [k.extrude(capsule(G.pts[0], G.pts[1], TOK_W), z, TOK_H, P)];
  if (pr.type === "arc") return [k.extrude(band(G.cc, G.r, G.a0, G.span, TOK_W, 48), z, TOK_H, P, { convex: false })];
  if (pr.type === "circle") {   // 고리는 뒤 반 → 앞 반
    const [vx, vy] = k.towardViewer(P), v = Math.atan2(vy, vx);   // 보는 쪽 방향으로 앞 반 · 뒤 반을 가름
    return [v + Math.PI / 2, v - Math.PI / 2].map((a0) => k.extrude(band(G.c, G.r, a0, Math.PI, TOK_W, 40), z, TOK_H, P, { convex: false }));
  }
  const [x, y] = G.c;   // 점 = 핀: 받침 · 기둥 · 머리
  return [k.cylinder(x, y, 2.6, z, 1, P, 24, 0.3), k.cylinder(x, y, 0.9, z + 1, 3.6, P, 14), k.cylinder(x, y, 1.9, z + 4.6, 1.4, P, 20, 0.4)];
}
function tokens() {
  return PRED.map((pr, i) => [pr, i]).sort((a, b) => a[0].z - b[0].z || depth2(PGEO[a[1]].c) - depth2(PGEO[b[1]].c)).map(([pr, i]) => {
    const ps = tokenPaths(pr, PGEO[i]);
    const plain = ps.map((p) => S(p, { tone: "hi", crease: "lo" })).join("");
    const lit = ps.map((p) => S(p, { tone: "hi", lit: true })).join("");
    return `<g data-tok="${i}" style="opacity:0"><g class="tok-plain">${plain}</g><g class="tok-lit">${lit}</g></g>`;
  }).join("");
}

// ── 정답 카드(왼쪽): 받침틀 · 카드 · 정답 도형 · 지금 짝지어지는 정답만 밝게
function answerCard() {
  const frame = k.insetPlan(CARD, -2.5);
  const o = [S(k.slabOf(frame, 0, 1.6, P, 4, 0.4), { tone: "lo" })];
  o.push(S(k.slabOf(CARD, 1.6, CARD_Z - 1.6, P, 4), { tone: "hi", crease: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(CARD, 2), CARD_Z, P), { tone: "faint" }));
  o.push(L(PRIMS.map((pr, i) => sketchD(pr, CGEO[i], CARD_Z, 0.8)).join(""), { tone: "mid" }));
  const ends = PRIMS.flatMap((pr, i) => pr.type === "line" ? CGEO[i].pts : pr.type === "arc" ? [CGEO[i].pts[0], CGEO[i].pts.at(-1)] : []);
  o.push(D(ends.map(([x, y]) => at([x, y, CARD_Z])), { size: 0.45, tone: "mid" }));
  PRIMS.forEach((pr, i) => o.push(`<g data-gt="${i}" style="opacity:0">${L(sketchD(pr, CGEO[i], CARD_Z, 0.8), { tone: "lit" })}</g>`));
  // 뒤쪽 누름쇠 둘
  for (const x of [CARD.x + 12, CARD.x + CARD.w - 12]) {
    o.push(S(k.slabOf({ x: x - 5, y: CARD.y - 3, w: 10, d: 6, r: 1.2 }, CARD_Z, 1.2, P, 3, 0.3), { tone: "mid" }));
    o.push(D([at([x, CARD.y, CARD_Z + 1.2])], { size: 0.45 }));
  }
  return o.join("");
}
// ── 단계 번호판(기계 앞): 1 입력 · 2 예측 · 3 채점 · 4 겹쳐 보기
function steps() {
  const o = [S(k.slabOf({ x: -156, y: 70, w: 77, d: 16, r: 3 }, 0, 1.2, P, 4, 0.3), { tone: "lo" })];
  STEPS.forEach(([x, y], i) => {
    o.push(S(k.cylinder(x, y, 6, 1.2, 1, P, 28), { tone: "lo" }));
    const cap = (lit) => S(k.cylinder(x, y, 5, 2.2, 2.2, P, 32, 0.5), { tone: lit ? "hi" : "mid", lit });
    o.push(`<g data-step="${i}">${cap(false)}<g class="st-on">${cap(true)}</g>${k.faceTextSvg(k.topMatrix([x - 1.1, y + 1.9], 4.4, P), String(i + 1), { size: 5.4, tone: "hi", anchor: "start" })}</g>`);
  });
  return o.join("");
}
// ── 겹쳐 보기: 정답 도형을 조각 윗면 높이에 점선으로(빗나간 정답은 종이 위에)
function overlay() {
  const d = PRIMS.map((pr, i) => sketchD(pr, GEO[i], SHEET_T + (OK[i] ? pr.z + (pr.type === "point" ? 6 : TOK_H) : 0) + 0.05, 2)).join("");
  return `<g data-part="overlay" style="opacity:0">${L(d, { tone: "lit", dashed: true, free: true })}</g>`;
}

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "PICASSO 핵심 동작을 16 칸 배출기로 그린 그림. 뒤쪽 16 칸이 차례로 밀대를 밀어 선 · 호 · 원 · 점 조각을 하나씩(또는 아무것도 없이) 내보내고, 조각은 128×128 도면판 위 제 매개변수 자리에 내려앉는다. 이어서 실이 칸마다 정답 못 하나를 일대일로 잇는다(헝가리안 매칭).",
  body: [base(), answerCard(), steps(), sheet(), rack(), pegs(), `<g data-part="threads">${threads()}</g>`, `<g data-part="tokens">${tokens()}</g>`, overlay()],
});

const SPEC = SLOT.map((s, i) => {
  if (s < 0) return null;
  const G = PGEO[s], pr = PRED[s];
  return { ok: OK[s], gt: PRIMS[s].type, land: [G.c[0], G.c[1], SHEET_T + pr.z], rest: [TX(i), REST_Y, FLOOR_Z], s0: Math.min(1, 7 / G.size), kind: pr.type };
});

const live = `
const P = ${JSON.stringify(P)};
const SPEC = ${JSON.stringify(SPEC)}, SLOT = ${JSON.stringify(SLOT)}, MATCH = ${JSON.stringify(MATCH)}, GT = ${JSON.stringify(GT)};
const KIND = ${JSON.stringify(KIND)};
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const pick = (sel, key) => { const m = {}; svg.querySelectorAll(sel).forEach((g) => (m[g.getAttribute(key)] = g)); return m; };
const toks = pick("[data-tok]", "data-tok"), push = pick("[data-push]", "data-push"), gts = pick("[data-gt]", "data-gt");
const pls = pick("[data-pl]", "data-pl"), vs = pick("[data-v]", "data-v"), stepsEl = pick("[data-step]", "data-step");
const ths = [...svg.querySelectorAll("[data-th]")].sort((a, b) => a.dataset.th - b.dataset.th);
const over = svg.querySelector('[data-part="overlay"]');
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const T0 = 2.0, EACH = 0.3, DUR = 1.4, TM = T0 + 15 * EACH + DUR + 0.3, ME = 0.42, TH = TM + 16 * ME + 0.3, TR = TH + 3.2, LOOP = TR + 1.0;
function draw(t) {
  let out = 0, now = -1;
  const fadeIn = ease(t / 0.8), fadeOut = 1 - ease((t - TR) / 0.8);
  for (let i = 0; i < 16; i++) {
    const u = (t - T0 - i * EACH) / DUR;
    const shove = ease(u / 0.28) - ease((u - 0.55) / 0.35);
    push[i].setAttribute("transform", translateAlong(P, [0, 7 * shove, 0]));
    if (u >= 0.28) out++;
    if (u >= 0 && u < 1) now = i;
    const sp = SPEC[i]; if (!sp) continue;
    const g = toks[SLOT[i]];
    const slide = ease(u / 0.28), fly = ease((u - 0.28) / 0.72);
    const r = sp.rest, l = sp.land;
    const start = [r[0], r[1] + 5 * slide, r[2]];
    const p = [start[0] + (l[0] - start[0]) * fly, start[1] + (l[1] - start[1]) * fly, start[2] + (l[2] - start[2]) * fly + 26 * Math.sin(Math.PI * fly)];
    const s = sp.s0 + (1 - sp.s0) * fly;
    const c = iso(l, P), q = iso(p, P);
    g.setAttribute("transform", "translate(" + q[0].toFixed(2) + " " + q[1].toFixed(2) + ") scale(" + s.toFixed(4) + ") translate(" + (-c[0]).toFixed(2) + " " + (-c[1]).toFixed(2) + ")");
    g.style.opacity = Math.min(fadeIn, fadeOut);
  }
  let cur = -1, right = 0, wrong = 0;
  ths.forEach((el, i) => {
    const m = (t - TM - i * ME) / ME;
    el.style.opacity = (m < 0 ? 0 : ease(m * 2)) * fadeOut;
    const on = m >= 0 && m < 1;
    el.firstElementChild.dataset.tone = on ? "lit" : "mid";
    el.firstElementChild.style.strokeWidth = on ? "1.1" : ".7";
    if (on) cur = i;
    const j = MATCH[i];
    vs[j].style.opacity = (m < 0.5 ? 0 : 1) * fadeOut;
    if (m >= 0.5 && SLOT[i] >= 0) SPEC[i].ok ? right++ : wrong++;
  });
  const blink = 0.55 + 0.45 * Math.cos(t * Math.PI * 6);
  const curGt = cur >= 0 ? GT[MATCH[cur]] : -1;
  for (const id in gts) gts[id].style.opacity = +id === curGt ? blink : 0;
  for (const j in pls) pls[j].style.opacity = cur >= 0 && MATCH[cur] === +j ? 1 : 0;
  for (const id in toks) toks[id].classList.toggle("on", cur >= 0 && SLOT[cur] === +id);
  const ov = ease((t - TH) / 0.6) * fadeOut;
  over.style.opacity = ov;
  const step = t < T0 ? 0 : t < TM ? 1 : t < TH ? 2 : 3;
  for (const s in stepsEl) stepsEl[s].classList.toggle("on", +s === step);
  let text;
  if (step === 0) text = "1단계 입력 · 128×128 스케치 그림 한 장이 들어온다";
  else if (step === 1) {
    if (now < 0) text = "2단계 예측 · 16 칸이 모두 답을 냈다 (" + out + " / 16)";
    else if (SLOT[now] < 0) text = "2단계 예측 · " + (now + 1) + " 번째 칸은 「없음」이라고 답한다";
    else text = "2단계 예측 · " + (now + 1) + " 번째 칸이 " + KIND[SPEC[now].kind] + " 하나를 그 자리에 내놓는다";
  } else if (step === 2) {
    if (cur < 0) text = "3단계 채점 · 16 칸 모두 정답 하나씩과 짝지었다";
    else if (SLOT[cur] < 0) text = "3단계 채점 · " + (cur + 1) + " 번째 칸 「없음」 ↔ 빈 정답 · 맞음";
    else { const sp = SPEC[cur]; text = "3단계 채점 · " + (cur + 1) + " 번째 칸 " + KIND[sp.kind] + " ↔ 정답 " + KIND[sp.gt] + " · " + (sp.ok ? "맞음" : "틀림"); }
  } else text = "4단계 겹쳐 보기 · 정답 9 개 중 맞힘 " + right + " · 틀림 " + wrong;
  readout.textContent = text;
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { if (held) { frame = 0; return; } const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__loop = LOOP;
window.__seek = (t) => { held = true; draw(((t % LOOP) + LOOP) % LOOP); };
draw(still.matches ? TH + 2 : 0);
`;
const css = `<style>[data-tok] .tok-lit,[data-step] .st-on{opacity:0;transition:opacity .2s}[data-tok].on .tok-lit,[data-step].on .st-on{opacity:1}</style>`;
const body = k.plateHtml({
  fig: "그림 2", title: "PICASSO · 칸마다 도형 하나",
  hint: "저절로 돈다 · 한 바퀴 약 18 초",
  readout: "1단계 입력 · 128×128 스케치 그림 한 장이 들어온다",
  keys: [
    { mark: "lit", label: "① 입력: 가운데 도면판 = 모델이 받는 128×128 그림" },
    { mark: "raised", label: "② 예측: 뒤쪽 16 칸이 각각 도형 하나(선 · 호 · 원 · 점) 또는 「없음」을 내고, 도형은 판 위 제 자리에 앉는다" },
    { mark: "dotted", label: "③ 채점: 실이 칸마다 정답 못 하나를 일대일로 잇는다(헝가리안 매칭) · 왼쪽 정답 카드에서 그 정답이 깜빡이고, 못 앞에 맞음(점) / 틀림(×)" },
    { mark: "dotted", label: "④ 겹쳐 보기: 정답(점선)을 모델 답 위에 겹친다 · 이 예에서는 작은 호를 직선으로 낸 칸 하나가 틀림" },
  ],
  caption: "이 모델은 CAD 스케치 그림 한 장(128×128)을 받아, 그 안의 선 · 호 · 원 · 점이 몇 개이고 각각 어디에 있는지(매개변수)를 한 번에 맞힌다(§3, §5). 출력 칸은 최대 16 개이고, 칸마다 도형 하나를 적거나 비워 둔다. 선은 시작 · 끝점, 호는 시작 · 중간 · 끝점, 원은 중심 · 반지름, 점은 좌표이며, 도형 하나는 토큰 8 개다(§3). 칸 순서에는 뜻이 없으므로 학습 때는 손실 합(토큰 교차 엔트로피)이 가장 작아지는 칸 ↔ 정답 일대일 짝을 헝가리안 매칭으로 먼저 정하고, 그 짝끼리 틀린 만큼 고친다(§4.4 식 2). 선 하나가 칸 하나라서 교차하거나 겹친 선도 화소를 두고 다투지 않는다. 고정한 렌더러로 예측을 다시 그려 입력 그림과 비교하면 정답 매개변수 없이도 학습할 수 있다(§4.3). 데이터는 SketchGraphs 를 거른 약 153 만 스케치(§5). 그림 속 도면과 틀린 칸 하나는 설명용으로 지은 예다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="PICASSO 동작 그림">${svg}</div>`,
});
const out = join(HERE, theme === "light" ? "picasso-light.html" : "picasso.html");
writeFileSync(out, k.pageHtml({ title: "PICASSO", theme, body, script: kitScript() + live }));
console.log("wrote", out);
