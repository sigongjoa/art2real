// GAT-CADNet (Zheng · Tan · Gao · Wang · Zhang, CVPR 2022) 핵심 동작 — 말판: 도면 프리미티브마다 말 하나(그래프 꼭짓점),
// 가까운 말끼리 실로 묶음(간선), 8 단계 동안 실을 따라 신호가 오가며(그래프 주의) 말 램프가 범주로 가라앉음,
// 끝에 「같은 인스턴스」 실만 남기고(인접 행렬 · 문턱 0.7) 같은 범주 안 연결 덩어리 = 기호 하나.
//
// 사실과 출처 (arXiv 2201.00625v2 HTML, 2026-10-23 읽음):
//  - 3.1: 꼭짓점 = 프리미티브 하나(선분 · 호 · 원 · 타원). 호는 양 끝점을 잇는 현, 원은 가로 지름, 타원은 장축으로 선분 근사.
//  - 3.1: 간선 = 두 꼭짓점 거리 d_ij < ε(300 mm), 같은 직선 위(공선) 프리미티브에 간선 추가, 꼭짓점당 최대 K = 30(무작위로 버림).
//  - 3.1: 꼭짓점 특징 7 차원 [cos2α, sin2α, 길이, 종류 원-핫 4], 간선 특징 7 차원(위치 차 · 각 · 길이 비 · 평행/직교/끝점 공유).
//  - 3.2 · 4: GAT 8 단계, 머리 8 개, 128 차원. RSE(상대 공간 부호화)가 간선 특징 → 주의 점수에 더함(소프트맥스 전, 매 단계).
//  - 3.2: 꼭짓점마다 의미 범주 소프트맥스(식 12). CEE: 모든 단계 주의를 합쳐 N×N 인접 행렬 Z 예측(시그모이드, 식 14–16) = 두 프리미티브가 같은 인스턴스인가.
//  - 4: Z 를 문턱 0.7 로 자르고, 예측 범주별로 묶은 뒤 연결 성분 = 인스턴스. 손실 = sem + 2·ins.
//  - 4: FloorPlanCAD 11,602 도면, thing 30 · stuff 5 범주. 표 3: PQ 0.737 · SQ 0.914 · RQ 0.807 (PanCADNet PQ 0.553).
//  - claudedocs/research_선검출모델_20261023.md: 입력이 이미 벡터 프리미티브 — 래스터 그림에는 바로 못 씀. [한계]
// 그림의 숫자 중 주의 가중치 · 확신도는 설명용 작은 모형(아래 model)이 만든 값이다. 학습된 값이 아니다.
// 사용: node build.mjs [--light] → gatcadnet.html / gatcadnet-light.html
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

// ---------- 도면: 벽(stuff) · 문 1 · 창 2 — 프리미티브 18 개 ----------
const SC = 1.5, YO = 36 * SC, YM = 29 * SC, YI = 22 * SC;   // 벽 바깥 · 창 가운데 · 벽 안쪽 (축척 1.5)
const WALL = 0, DOOR = 1, WIN = 2, NAMES = ["벽", "문", "창"];
const sc = ([x, y]) => [x === -44 || x === -10 || x === 18 || x === 44 || x === 70 || x === -92 || x === 92 ? x * SC : x, y];
const line = (a, b, cls, inst) => ({ type: "line", a: sc(a), b: sc(b), cls, inst });
const ARC = { c: [-44 * SC, YI], r: 34 * SC, from: 0, to: -Math.PI / 2 };
const prims = [
  line([-92, YO], [-44, YO], WALL, 0), line([-92, YI], [-44, YI], WALL, 0), line([-44, YI], [-44, YO], WALL, 0),
  line([-44, YI], [-44, YI - 34 * SC], DOOR, 1),
  { type: "arc", a: [-10 * SC, YI], b: [-44 * SC, YI - 34 * SC], cls: DOOR, inst: 1 },       // 호 → 현(양 끝점)으로 근사 (3.1)
  line([-10, YO], [18, YO], WIN, 2), line([-10, YM], [18, YM], WIN, 2), line([-10, YI], [18, YI], WIN, 2),
  line([18, YI], [18, YO], WALL, 0), line([18, YO], [44, YO], WALL, 0), line([18, YI], [44, YI], WALL, 0), line([44, YI], [44, YO], WALL, 0),
  line([44, YO], [70, YO], WIN, 3), line([44, YM], [70, YM], WIN, 3), line([44, YI], [70, YI], WIN, 3),
  line([70, YI], [70, YO], WALL, 0), line([70, YO], [92, YO], WALL, 0), line([70, YI], [92, YI], WALL, 0),
];
const N = prims.length;
const mid = (p) => [(p.a[0] + p.b[0]) / 2, (p.a[1] + p.b[1]) / 2];
const len = (p) => Math.hypot(p.b[0] - p.a[0], p.b[1] - p.a[1]);
const ang = (p) => Math.atan2(p.b[1] - p.a[1], p.b[0] - p.a[0]);

// ---------- 그래프: 거리 < ε 또는 공선 (3.1) ----------
const EPS = 8 * SC, COLLINEAR_GAP = 40 * SC;   // 그림 축척의 ε (논문 300 mm)
function segDist(p, q) {   // 두 현 사이 최소 거리 (표본)
  let best = Infinity;
  for (let i = 0; i <= 24; i++) for (let j = 0; j <= 24; j++) {
    const u = i / 24, v = j / 24;
    const x = p.a[0] + (p.b[0] - p.a[0]) * u - (q.a[0] + (q.b[0] - q.a[0]) * v);
    const y = p.a[1] + (p.b[1] - p.a[1]) * u - (q.a[1] + (q.b[1] - q.a[1]) * v);
    best = Math.min(best, Math.hypot(x, y));
  }
  return best;
}
const collinear = (p, q) => {
  const d = Math.abs(Math.sin(ang(p) - ang(q)));
  if (d > Math.sin(5 * Math.PI / 180)) return false;
  const [mx, my] = mid(q), t = ang(p);
  return Math.abs(-(mx - p.a[0]) * Math.sin(t) + (my - p.a[1]) * Math.cos(t)) < 0.5;
};
const EDGES = [];
for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
  const d = segDist(prims[i], prims[j]);
  if (d < EPS || (collinear(prims[i], prims[j]) && d < COLLINEAR_GAP)) EDGES.push([i, j]);
}

// ---------- 설명용 모형: 8 단계 주의 전달 ----------
const STAGES = 8;
// 0 단계 확신도: 종류 · 길이 · 방향만 보고 정한 값 (꼭짓점 특징 7 차원이 담는 정보 수준) — 호는 문 쪽, 나머지는 모호
const prior = (p) => p.type === "arc" ? [0.15, 0.7, 0.15]
  : Math.abs(Math.sin(ang(p))) > 0.9 ? (len(p) > 20 ? [0.56, 0.34, 0.1] : [0.5, 0.15, 0.35])
  : p.cls === WIN && p.a[1] === YM ? [0.2, 0.05, 0.75] : p.cls === WIN ? (p.inst === 3 ? [0.63, 0.05, 0.32] : [0.55, 0.05, 0.4]) : [0.55, 0.1, 0.35];
const norm = (v) => { const s = v.reduce((a, b) => a + b, 0); return v.map((x) => x / s); };
function model() {
  const H = [prims.map(prior)], A = [];
  const nb = Array.from({ length: N }, () => []);
  EDGES.forEach(([i, j], e) => { nb[i].push([j, e]); nb[j].push([i, e]); });
  for (let s = 1; s <= STAGES; s++) {
    const h = H[s - 1], a = new Array(EDGES.length).fill(0);
    const next = h.map((hi, i) => {
      // 주의 점수 = RSE 몫(간선 기하: 평행 · 끝점 공유) + 특징 유사도(단계가 갈수록 날카로워짐) → 소프트맥스
      const sc = nb[i].map(([j]) => {
        const geo = (Math.abs(Math.sin(ang(prims[i]) - ang(prims[j]))) < 0.1 ? 0.4 : 0) + (segDist(prims[i], prims[j]) < 0.5 ? 0.3 : 0);
        const sim = hi.reduce((acc, x, c) => acc + x * h[j][c], 0);
        const g = 0.5 + 0.5 * s / STAGES;
        return geo + 4 * sim * g + (prims[i].inst === prims[j].inst ? 3 : -2) * g;
      });
      const m = Math.max(...sc), ex = sc.map((x) => Math.exp(x - m)), z = ex.reduce((x, y) => x + y, 0);
      const msg = [0, 0, 0];
      nb[i].forEach(([j, e], q) => { const w = ex[q] / z; a[e] += w / 2; for (let c = 0; c < 3; c++) msg[c] += w * h[j][c]; });
      return norm(hi.map((x, c) => Math.pow(0.8 * x + 0.2 * msg[c], 1.35)));
    });
    H.push(next); A.push(a);
  }
  // 인접 행렬 Z(같은 인스턴스?) — CEE 는 모든 단계 주의를 합친다 (식 14)
  const sum = EDGES.map((_, e) => A.reduce((acc, a) => acc + a[e], 0) / STAGES);
  const top = Math.max(...sum);
  const Z = EDGES.map(([i, j], e) => (prims[i].inst === prims[j].inst ? 0.75 + 0.25 * sum[e] / top : 0.6 * sum[e] / top));
  return { H, A, Z };
}
const M = model();
const label = (h) => h.indexOf(Math.max(...h));
// 한 가지 확인: 8 단계 뒤 모든 말이 참 범주로 가라앉고, 문턱 0.7 의 연결 성분이 참 인스턴스와 같다
prims.forEach((p, i) => { if (label(M.H[STAGES][i]) !== p.cls) throw new Error(`말 ${i} 가 ${NAMES[label(M.H[STAGES][i])]} 로 감 (참 ${NAMES[p.cls]})`); });
const KEEP = EDGES.map(([i, j], e) => M.Z[e] >= 0.7 && label(M.H[STAGES][i]) === label(M.H[STAGES][j]));
{
  const root = [...Array(N).keys()], f = (x) => (root[x] === x ? x : (root[x] = f(root[x])));
  EDGES.forEach(([i, j], e) => { if (KEEP[e]) root[f(i)] = f(j); });
  prims.forEach((p, i) => prims.forEach((q, j) => { if (p.cls !== WALL && q.cls !== WALL && (f(i) === f(j)) !== (p.inst === q.inst)) throw new Error(`인스턴스 어긋남 ${i}-${j}`); }));
}
const thingInst = new Set(prims.filter((p) => p.cls !== WALL).map((p) => p.inst));
const doorN = new Set(prims.filter((p) => p.cls === DOOR).map((p) => p.inst)).size, winN = new Set(prims.filter((p) => p.cls === WIN).map((p) => p.inst)).size;

// ---------- 그림 ----------
const PLATE = { x: -166, y: -48, w: 332, d: 174, r: 9 };
const PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -150, y: -26, w: 300, d: 88, r: 2 }, SHEET_T = 0.8;
const TOK_H = 4.2, LAMP_T = 0.7, PIN_TOP = 10, THREAD_Z = 9.4;
const DIAL = { c: [140, 98], R: 10 };
const STEPS = [["1", "잇기"], ["2", "주고받기"], ["3", "묶기"], ["4", "채점"]], STEP = (i) => ({ x: -152 + i * 32, y: 80, w: 29, d: 28, r: 2 });
const CARD = { x: -20, y: 70, w: 140, d: 48, r: 2 }, MS = 0.45, MO = [CARD.x + CARD.w / 2, CARD.y + 12 + 18 * MS];   // 정답 판 · 작은 도면 축척
const mini = ([x, y]) => [MO[0] + x * MS, MO[1] + y * MS];
const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...k.boxCorners(SHEET, 0, PIN_TOP + 2)], WIDTH, HEIGHT, { pad: 22, azimuth: 60, elevation: 38 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const depth2 = ([x, y]) => k.depthOf([x, y, 0], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth2(a) - depth2(b));

function tokenRing(p) {   // 선분 말 = 방향 따라 누운 둥근 막대, 호 말 = 둥근 퍽
  const [cx, cy] = mid(p);
  if (p.type === "arc") return k.circleRing(cx, cy, 6.2, 32);
  const L2 = Math.min(20, Math.max(8, len(p) * 0.42)) / 2, W2 = 3.3, t = ang(p), c = Math.cos(t), s = Math.sin(t);
  const pts = [];
  for (const [ex, a0] of [[L2, -Math.PI / 2], [-L2, Math.PI / 2]]) for (let q = 0; q <= 6; q++) {
    const a = a0 + (q / 6) * Math.PI, lx = ex + W2 * Math.cos(a), ly = W2 * Math.sin(a);
    pts.push([cx + lx * c - ly * s, cy + lx * s + ly * c]);
  }
  return pts;
}
const inset = (ring, by) => { const [cx, cy] = ring.reduce(([a, b], [x, y]) => [a + x / ring.length, b + y / ring.length], [0, 0]); return ring.map(([x, y]) => { const dx = x - cx, dy = y - cy, l = Math.hypot(dx, dy) || 1; return [x - (dx / l) * by, y - (dy / l) * by]; }); };

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
  // 뒤쪽 자(가로) — 눈금은 자 가장자리에서
  const strip = { x: -146, y: PLATE.y + 9, w: 292, d: 8, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + 0.8, 0.6, [2, 3.6], P);
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  return o.join("");
}
function sheet() {   // 입력 = 벡터 도면(종이) — 프리미티브가 새겨져 있음
  const o = [S(k.slabOf(SHEET, 0, SHEET_T, P, 4), { tone: "hi", crease: "lo" })];
  o.push(L(k.planOutline(k.insetPlan(SHEET, 3), SHEET_T, P), { tone: "faint" }));
  o.push(D(k.corners(SHEET, 5).map(([x, y]) => at([x, y, SHEET_T])), { size: 0.45 }));
  const d = prims.map((p) => {
    if (p.type === "line") return k.lineOnTop(p.a, p.b, SHEET_T, P);
    const pts = []; for (let q = 0; q <= 24; q++) { const a = ARC.from + (ARC.to - ARC.from) * q / 24; pts.push([ARC.c[0] + ARC.r * Math.cos(a), ARC.c[1] + ARC.r * Math.sin(a)]); }
    return k.onTop(pts, SHEET_T, P);
  }).join("");
  o.push(L(d, { tone: "mid", free: true }));   // 도면에 인쇄된 선(입력) — 끝이 종이 위에서 끝나는 게 맞다
  // 도면 표제란(오른쪽 뒤 모서리) — 칸 나눔은 테두리에서 테두리로, 글자 줄은 free
  const tb = { x: SHEET.x + SHEET.w - 62, y: SHEET.y + 5, w: 56, d: 20, r: 0 };
  o.push(L(k.planOutline(tb, SHEET_T, P, 1), { tone: "lo" }));
  o.push(L(k.lineOnTop([tb.x, tb.y + 10], [tb.x + tb.w, tb.y + 10], SHEET_T, P) + k.lineOnTop([tb.x + 34, tb.y], [tb.x + 34, tb.y + tb.d], SHEET_T, P), { tone: "lo" }));
  [[3, 24, 4], [3, 18, 7], [3, 26, 14], [3, 14, 17], [37, 14, 5], [37, 10, 15]].forEach(([dx, l, dy]) => o.push(L(k.lineOnTop([tb.x + dx, tb.y + dy], [tb.x + dx + l, tb.y + dy], SHEET_T, P), { tone: "faint", free: true })));
  return o.join("");
}
function dial() {   // 단계 다이얼: 8 칸, 바늘 = 지금 단계
  const [x, y] = DIAL.c, R = DIAL.R, top = 8;
  const o = [S(k.cylinder(x, y, R + 2.4, 0, 2, P, 48), { tone: "lo" })];
  o.push(S(k.cylinder(x, y, R, 2, top - 2, P, 64, 0.8), { tone: "hi", crease: "lo" }));
  o.push(L(k.knurl(x, y, R, top - 2.6, top, 72, P, 0.3), { tone: "lo" }));
  o.push(L(k.ring(x, y, R - 2, top, P, 64), { tone: "lo" }));
  const t = k.radialTicks(x, y, R - 2.6, 8, 1, top, [2.2, 2.2], P, -Math.PI * 0.75, Math.PI * 1.5 * 8 / 7);
  if (t && t.major) o.push(L(t.major, { tone: "mid" }));
  if (t && t.minor) o.push(L(t.minor, { tone: "mid" }));
  o.push(`<path data-part="needle" class="iso-line" data-tone="lit" data-free="" style="stroke-width:1.1" d=""/>`);
  o.push(L(k.ring(x, y, 1.4, top, P, 16), { tone: "hi" }));
  return o.join("");
}
function steps() {   // 단계 번호판 ①–④: 지금 단계 단추가 켜짐
  return STEPS.map((n, i) => {
    const b = STEP(i), cap = k.insetPlan(b, 2.4), c = [cap.x + cap.w / 2, cap.y + cap.d / 2];
    const g = [S(k.slabOf(b, 0, 1.4, P, 4, 0.4), { tone: "lo" }),
      `<g class="st-off">${S(k.slabOf(cap, 1.4, 2.2, P, 4, 0.5), { tone: "mid" })}</g>`,
      `<g class="st-on">${S(k.slabOf(cap, 1.4, 2.2, P, 4, 0.5), { tone: "hi", lit: true })}</g>`,
      k.faceTextSvg(k.topMatrix([c[0] - 10.5, c[1] + 1], 3.6, P), n[0], { size: 10, tone: "hi" }),
      k.faceTextSvg(k.topMatrix([c[0] - 4, c[1] + 0.6], 3.6, P), n[1], { size: 3.6, tone: "mid" }),
      D([at([b.x + 1.2, b.y + b.d / 2, 1.4]), at([b.x + b.w - 1.2, b.y + b.d / 2, 1.4])], { size: 0.4 })];
    return `<g data-step="${i}" data-state="off">${g.join("")}</g>`;
  }).join("");
}
function answerCard() {   // 정답 판: 같은 도면을 작게, 말 자리에 정답 범주 색, 둘레 고리 = 모델 답이 맞음/틀림
  const o = [S(k.slabOf(k.insetPlan(CARD, -2), 0, 1.2, P, 4, 0.4), { tone: "lo" }), S(k.slabOf(CARD, 1.2, 1.6, P, 4, 0.5), { tone: "hi", crease: "lo" })];
  const z = 2.8;
  o.push(L(k.planOutline(k.insetPlan(CARD, 2.5), z, P), { tone: "faint" }));
  o.push(D(k.corners(CARD, 4).map(([x, y]) => at([x, y, z])), { size: 0.45 }));
  o.push(k.faceTextSvg(k.topMatrix([CARD.x + 6, CARD.y + 12], z, P), "정답", { size: 7, tone: "hi" }));
  const d = prims.map((p) => {
    if (p.type === "line") return k.lineOnTop(mini(p.a), mini(p.b), z, P);
    const pts = []; for (let q = 0; q <= 16; q++) { const a = ARC.from + (ARC.to - ARC.from) * q / 16; pts.push(mini([ARC.c[0] + ARC.r * Math.cos(a), ARC.c[1] + ARC.r * Math.sin(a)])); }
    return k.onTop(pts, z, P);
  }).join("");
  o.push(L(d, { tone: "faint", free: true }));
  byDepth(prims.map((p, i) => [...mini(mid(p)), i])).forEach(([x, y, i]) => {
    o.push(`<g data-mk="${i}"><path class="mk" data-ok="1" d="${k.ring(x, y, 3.3, z, P, 20)}" style="opacity:0"/><path class="mk" data-ok="0" d="${k.ring(x, y, 3.3, z, P, 20)}" style="opacity:0"/></g>`);
    o.push(S(k.cylinder(x, y, 2.1, z, 0.8, P, 18), { tone: "mid", crease: "none" }));
    o.push(`<path class="lamp" data-c="${prims[i].cls}" d="${k.ring(x, y, 1.6, z + 0.8, P, 18)}"/>`);
  });
  return o.join("");
}
const order = byDepth(prims.map((p, i) => [...mid(p), i])).map((q) => q[2]);
function tokens() {
  return order.map((i) => {
    const p = prims[i], ring = tokenRing(p), [cx, cy] = mid(p);
    const top = k.onTop(inset(ring, 0.9), SHEET_T + TOK_H + LAMP_T, P, true);
    const g = [S(k.extrude(ring, SHEET_T, TOK_H, P, { bevel: 0.5 }), { tone: "mid" }),
      S(k.extrude(inset(ring, 0.9), SHEET_T + TOK_H, LAMP_T, P), { tone: "lo", crease: "none" }),
      ...[0, 1, 2].map((c) => `<path class="lamp" data-c="${c}" d="${top}" style="opacity:0"/>`),
      S(k.cylinder(cx, cy, 1, SHEET_T + TOK_H + LAMP_T, PIN_TOP - SHEET_T - TOK_H - LAMP_T, P, 12), { tone: "mid", crease: "none" }),
      S(k.cylinder(cx, cy, 1.6, PIN_TOP - 1.1, 1.1, P, 18), { tone: "hi" })];
    return `<g data-tok="${i}">${g.join("")}</g>`;
  }).join("");
}
const tz = (i) => [...mid(prims[i]), THREAD_Z];
function threads() {   // 간선 = 말 기둥 꼭대기끼리 잇는 실 (끝은 고리 점)
  return EDGES.map(([i, j], e) => `<g data-edge="${e}">${k.wireSvg(at(tz(i)), at(tz(j)), { tone: "lo", size: 0.7 })}</g>`).join("");
}

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "GAT-CADNet 동작을 말판으로 그린 그림. 벡터 도면의 프리미티브마다 말이 하나 서 있고, 가까운 말끼리 실로 묶여 있다. 여덟 단계 동안 실을 따라 신호가 오가며 말의 램프가 벽 · 문 · 창 색으로 가라앉고, 끝에 같은 기호에 속한 실만 남는다.",
  body: [base(), sheet(), steps(), answerCard(), dial(), `<g data-part="tokens">${tokens()}</g>`, `<g data-part="threads">${threads()}</g>`, `<g data-part="pulses"></g>`],
});

const live = `
const P = ${JSON.stringify(P)};
const EDGES = ${JSON.stringify(EDGES)}, H = ${JSON.stringify(M.H.map((h) => h.map((v) => v.map((x) => +x.toFixed(3)))))}, A = ${JSON.stringify(M.A.map((a) => a.map((x) => +x.toFixed(3))))};
const Z = ${JSON.stringify(M.Z.map((x) => +x.toFixed(3)))}, KEEP = ${JSON.stringify(KEEP)}, CLS = ${JSON.stringify(prims.map((p) => p.cls))};
const TZ = ${JSON.stringify(prims.map((_, i) => tz(i)))}, DIAL = ${JSON.stringify(DIAL)}, NAMES = ${JSON.stringify(NAMES)}, S = ${STAGES};
const NDOOR = ${doorN}, NWIN = ${winN};
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const steps = [...svg.querySelectorAll("[data-step]")], mks = []; svg.querySelectorAll("[data-mk]").forEach((g) => { mks[+g.dataset.mk] = [...g.querySelectorAll(".mk")]; });
const toks = []; svg.querySelectorAll("[data-tok]").forEach((g) => { toks[+g.dataset.tok] = [...g.querySelectorAll(".lamp")]; });
const edges = [...svg.querySelectorAll("[data-edge]")], pulses = svg.querySelector('[data-part="pulses"]'), needle = svg.querySelector('[data-part="needle"]');
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const T0 = 2.5, TS = 1.35, TI = 2.6, HOLD = 3.6, LOOP = T0 + S * TS + TI + HOLD;
const aMax = Math.max(...A.flat());
const lerp = (a, b, u) => a + (b - a) * u;
function draw(t) {
  // s: 연속 단계(0 … S)
  const s = Math.max(0, Math.min(S, (t - T0) / TS)), si = Math.min(S - 1, Math.floor(s)), u = s - si;
  const h = H[si].map((v, i) => v.map((x, c) => lerp(x, H[si + 1][i][c], ease(u))));
  const ans = h.map((v) => v.indexOf(Math.max(...v))), ok = ans.filter((c, i) => c === CLS[i]).length;
  const phase = t < T0 ? 0 : t < T0 + S * TS ? 1 : t < T0 + S * TS + TI ? 2 : 3;
  steps.forEach((g, i) => { g.dataset.state = i === phase ? "on" : "off"; });
  // 정답 판 고리: ② 매 바퀴 시작에 깜빡(판정), ③ 흐리게, ④ 다 켬
  const blink = phase === 1 ? 0.3 + 0.7 * (1 - ease(u / 0.55)) : phase === 2 ? 0.3 : phase === 3 ? ease((t - T0 - S * TS - TI) / 0.6) : 0;
  ans.forEach((c, i) => mks[i].forEach((el) => { el.style.opacity = ((el.dataset.ok === "1") === (c === CLS[i]) ? blink : 0).toFixed(3); }));
  h.forEach((v, i) => toks[i].forEach((el, c) => { el.style.opacity = ease((v[c] - 0.4) / 0.45).toFixed(3); }));
  const ti = ease((t - T0 - S * TS) / 1.6);   // 인스턴스 단계 0 → 1
  let dots = "";
  edges.forEach((g, e) => {
    const a = s > 0 ? A[Math.min(S - 1, Math.floor(Math.max(0, s - 1e-6)))][e] / aMax : 0.35;
    const w = 0.35 + 0.95 * a, keep = KEEP[e], thing = keep && CLS[EDGES[e][0]] !== 0;
    g.style.opacity = (lerp(0.45 + 0.55 * a, keep ? 1 : 0.06, ti)).toFixed(3);
    const path = g.firstChild.firstChild; path.style.strokeWidth = lerp(w, thing ? 1.15 : 0.6, ti).toFixed(2);
    g.firstChild.dataset.tone = path.dataset.tone = ti > 0.5 && thing ? "lit" : a > 0.6 && ti < 0.5 ? "hi" : "mid";
    if (s > 0 && s < S && t < T0 + S * TS) {   // 신호: 단계마다 실 양쪽에서 가운데로
      const [i, j] = EDGES[e], p = ease(Math.min(1, u / 0.7));
      for (const [from, to] of [[i, j], [j, i]]) {
        const q = iso([lerp(TZ[from][0], TZ[to][0], p), lerp(TZ[from][1], TZ[to][1], p), TZ[from][2] + 0.2], P);
        if (p < 1) dots += '<circle cx="' + q[0].toFixed(2) + '" cy="' + q[1].toFixed(2) + '" r="' + (0.8 + 0.9 * a).toFixed(2) + '" class="iso-dot" data-tone="lit" opacity="' + (0.3 + 0.7 * a).toFixed(2) + '"/>';
      }
    }
  });
  pulses.innerHTML = dots;
  const ang = -Math.PI * 0.75 + (Math.PI * 1.5 * 8 / 7) * (Math.max(0, s - 1) / 7) * (s >= 1 ? 1 : 0);
  const [x, y] = DIAL.c, r = DIAL.R - 3.4;
  const a0 = iso([x - Math.cos(ang) * 2.4, y - Math.sin(ang) * 2.4, 8.05], P), a1 = iso([x + Math.cos(ang) * r, y + Math.sin(ang) * r, 8.05], P);
  needle.setAttribute("d", "M" + a0[0].toFixed(2) + " " + a0[1].toFixed(2) + "L" + a1[0].toFixed(2) + " " + a1[1].toFixed(2));
  if (phase === 0) readout.textContent = "1 잇기 · 선 · 호 " + h.length + " 개를 말로, 가까운 것끼리 실로";
  else if (phase === 1) readout.textContent = "2 이웃과 정보 주고받는 중 " + Math.min(S, Math.floor(s) + 1) + "/" + S + " 바퀴 · 정답과 맞음 " + ok + "/" + h.length;
  else if (phase === 2) readout.textContent = "3 묶기 · 같은 기호끼리의 실만 남김";
  else readout.textContent = "4 채점 · 맞음 " + ok + " · 틀림 " + (h.length - ok) + " · 문 " + NDOOR + " · 창 " + NWIN + " 찾음";
}
let frame = 0, last = 0, clock = 0, visible = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
draw(still.matches ? LOOP - 0.5 : 0);
`;
const css = `<style>
.iso{--c0:#8b9099;--c1:#d9480f;--c2:#1c7ed6}
.iso[data-theme="dark"]{--c0:#d4d4d8;--c1:#ff8a3d;--c2:#5aa9ff}
.iso{--ok:#2f9e44;--bad:#e03131}.iso[data-theme="dark"]{--ok:#51cf66;--bad:#ff6b6b}
.mk{fill:none;stroke-width:1.6}.mk[data-ok="1"]{stroke:var(--ok)}.mk[data-ok="0"]{stroke:var(--bad)}
[data-step] .st-on{opacity:0;transition:opacity .3s}[data-step][data-state="on"] .st-on{opacity:1}
.lamp{stroke:none}.lamp[data-c="0"]{fill:var(--c0)}.lamp[data-c="1"]{fill:var(--c1)}.lamp[data-c="2"]{fill:var(--c2)}
.iso-key:nth-child(n+2) .iso-swatch path{stroke-width:3}
.iso-key:nth-child(2) .iso-swatch path{stroke:var(--c1)}.iso-key:nth-child(3) .iso-swatch path{stroke:var(--c2)}.iso-key:nth-child(4) .iso-swatch path{stroke:var(--c0)}.iso-key:nth-child(5) .iso-swatch path{stroke:var(--ok)}.iso-key:nth-child(6) .iso-swatch path{stroke:var(--bad)}
</style>`;
const body = k.plateHtml({
  fig: "그림 1", title: "GAT-CADNet · 그래프 주의로 기호 찾기",
  hint: "자동 · 약 20 초",
  readout: "1 잇기 · 선 · 호 18 개를 말로",
  keys: [{ mark: "raised", label: "말 = 프리미티브 하나(막대 = 선분 · 퍽 = 호), 실 = 거리 ε 안 · 공선 이웃" },
    { mark: "line", label: "문" }, { mark: "line", label: "창" }, { mark: "line", label: "벽(스터프)" },
    { mark: "line", label: "정답 판 고리: 모델 답 = 정답" }, { mark: "line", label: "모델 답 ≠ 정답" },
    { mark: "lit", label: "실 굵기 = 주의 가중치 · 끝에 남는 실 = 같은 인스턴스(Z ≥ 0.7)" }],
  caption: "이 모델은 CAD 도면의 선 · 호(이미 벡터인 프리미티브)를 입력받아, 선 하나하나가 어떤 기호(문 · 창 · 벽 …)에 속하는지와 어떤 선들이 묶여 기호 하나를 이루는지를 맞힌다. 앞쪽 정답 판은 사람이 붙인 정답이고, 그 둘레 고리가 바퀴마다 모델 답이 정답과 같은지(초록) 다른지(빨강)를 보여 준다. GAT-CADNet(CVPR 2022)은 도면을 그래프로 본다. 선분 · 호 · 원 · 타원 하나가 꼭짓점이고(호는 현으로 근사), 거리 ε(300 mm) 안이거나 같은 직선 위의 프리미티브끼리 간선으로 잇는다(3.1). 그래프 주의 8 단계가 이웃의 특징을 모으고, 간선의 상대 위치 · 각도(RSE)가 주의 점수에 더해진다. 꼭짓점마다 범주를 내고, 모든 단계의 주의를 합쳐(CEE) 「같은 인스턴스인가」 인접 행렬을 낸 뒤 0.7 로 잘라 같은 범주 안 연결 덩어리를 기호 하나로 묶는다(3.2 · 4). FloorPlanCAD 에서 PQ 0.737(표 3). 한계: 입력이 이미 벡터 프리미티브라 래스터 그림에는 바로 못 쓴다. 그림 속 가중치와 확신도는 설명용 작은 모형의 값이다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="GAT-CADNet 동작 그림">${svg}</div>`,
});
const out = join(HERE, theme === "light" ? "gatcadnet-light.html" : "gatcadnet.html");
writeFileSync(out, k.pageHtml({ title: "GAT-CADNet", theme, body, script: kitScript() + live }));
console.log("wrote", out, "· 간선", EDGES.length, "· 남김", KEEP.filter(Boolean).length);
