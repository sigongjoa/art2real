// 판 142 「세 뷰 짝」 — 한 장에서 겹친 선을 다른 두 장으로 가른다. 계산만, 학습 없음.
// 근거(이 그림이 쓰는 사실만):
//   입력: 부품 하나의 3 면도(위 · 앞 · 옆, 정투영). 좌표가 묶인다: 앞 x = 위 x · 앞 높이 = 옆 높이 · 위 깊이 = 옆 깊이.
//   한 장에서는 깊이가 다른 3D 모서리 여럿이 같은 2D 선에 겹치고, 곡면의 테(원기둥 옆 테두리)도 모서리처럼 보인다.
//   다른 두 장이 가른다: A 층(앞 한 줄 → 위 평행선 둘 = 모서리 2) · B 곡면 테(위에서 원에 닿을 뿐 끝이 꼭짓점 아님 = 모서리 0)
//                        · C 진짜 모서리(양 끝이 위 · 옆 꼭짓점과 맞음 = 모서리 1)
//   잴 것(아직 안 돎 — 숫자는 그리지 않는다): 3D 모서리 ≥ 2 를 숨긴 2D 선의 몫 · 그중 다른 두 장이 가른 몫
// 부품(설명용, 단위 = 칸): 바닥 블록 60×40×12(앞 오른쪽 모서리를 깎음) · 뒤쪽 층 60×20×12 · 원기둥 보스 Ø12 높이 10
// 그림 요소: 유리 상자(바닥 = 위 · 뒤 벽 = 앞 · 왼 벽 = 옆) · 가운데 뜬 부품 · 투영 빛줄 · 상자 모서리 자의 슬라이더(좌표 묶음)
//           · 번호판 ①~④ · 정답 카드(3D 모서리 목록)
// 사용: node build.mjs [--light] [--record]
//   → out/설명/anatomy/threeview142/threeview142[-light].html · --record 는 light 판을 8 fps × 2 배로 찍어 이 폴더에 .mp4 · .gif
import { mkdirSync, writeFileSync, readdirSync, unlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../../out/설명/anatomy/threeview142");
const RECORD = process.argv.includes("--record");
const theme = RECORD || process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

// ── 부품(부품 좌표: x 오른쪽 · y 앞쪽 · z 위) ───────────────────
const BASE = [[0, 0], [60, 0], [60, 30], [50, 40], [0, 40]];   // z 0..12
const UPPER = { x: 0, y: 0, w: 60, d: 20, r: 0 };                // z 12..24
const CYL = { c: [20, 30], r: 6, z0: 12, z1: 22 };
// 세 장의 선(보이는 선만) — 부품 좌표
const FRONT = [ // (x, z)
  [[0, 0], [60, 0]], [[0, 0], [0, 24]], [[60, 0], [60, 24]], [[0, 24], [60, 24]], [[0, 12], [60, 12]], [[50, 0], [50, 12]],
  [[14, 22], [26, 22]], [[14, 12], [14, 22]], [[26, 12], [26, 22]],
];
const TOPV = [ // (x, y)
  [[0, 0], [60, 0]], [[0, 0], [0, 40]], [[60, 0], [60, 30]], [[60, 30], [50, 40]], [[0, 40], [50, 40]], [[0, 20], [60, 20]],
];
const SIDE = [ // (y, z)
  [[0, 0], [40, 0]], [[40, 0], [40, 12]], [[20, 12], [40, 12]], [[20, 12], [20, 24]], [[0, 24], [20, 24]], [[0, 0], [0, 24]],
  [[30, 0], [30, 12]], [[24, 12], [24, 22]], [[36, 12], [36, 22]], [[24, 22], [36, 22]],
];
// 세 경우(앞 선 번호 · 3D 모서리)
const CASES = {
  A: { front: 3, edges: [[[0, 0, 24], [60, 0, 24]], [[0, 20, 24], [60, 20, 24]]] },
  B: { front: 8, edges: [] },
  C: { front: 5, edges: [[[50, 40, 0], [50, 40, 12]]] },
};
// 자체 확인: A 의 두 모서리는 앞에서 같은 선, 위에서 다른 선 · C 의 끝은 위 꼭짓점 · B 의 x 는 원의 접점
const sameFront = (e) => e.map(([a, b]) => `${a[0]},${a[2]}-${b[0]},${b[2]}`);
if (new Set(sameFront(CASES.A.edges)).size !== 1) throw new Error("A 가 앞에서 한 줄이 아니다");
if (new Set(CASES.A.edges.map(([a]) => a[1])).size !== 2) throw new Error("A 가 위에서 두 줄이 아니다");
if (!BASE.some(([x, y]) => x === 50 && y === 40)) throw new Error("C 끝이 위 꼭짓점이 아니다");
if (CYL.c[0] + CYL.r !== FRONT[CASES.B.front][0][0]) throw new Error("B 가 원기둥 테가 아니다");

// ── 배치(세계 좌표) ───────────────────────────────────────────
const OX = 50, OY = 62, OZ = 46;                 // 부품이 뜬 자리
const BW = 132, BD = 122, BH = 88, WT = 3;       // 유리 상자: 바닥 BW×BD · 벽 높이 BH
const PLATE = { x: -22, y: -22, w: BW + 46, d: BD + 86, r: 8 }, PLATE_H = 8, FOOT_H = 4;
const CARD = { x: -4, y: BD + 11, w: 112, d: 50, r: 1 };
const HOLD = { x: CARD.x - 3, y: CARD.y - 3, w: CARD.w + 6, d: CARD.d + 6, r: 2 };
const KEYS = { x: 114, y: BD + 20, w: 34, d: 34, r: 2 };
const O = ([x, y, z]) => [OX + x, OY + y, OZ + z];
const onFront = ([x, z]) => [OX + x, 0.05, OZ + z];
const onTop = ([x, y]) => [OX + x, OY + y, 0.05];
const onSide = ([y, z]) => [0.05, OY + y, OZ + z];

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [0, -WT, BH + 4], [BW, -WT, BH + 4], [-WT, BD, BH + 4]], WIDTH, HEIGHT, { pad: 22, azimuth: 58, elevation: 30 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const seg = (a, b) => k.segment(a, b, P);
const path = (pts, closed) => k.pathOf(pts.map(at), closed);
const Ttop = (x, y, z, text, size, tone = "mid", anchor = "start") => k.faceTextSvg(k.topMatrix([x, y], z, P, "x"), text, { size, tone, anchor });
const Tback = (x, z, text, size, tone = "mid") => k.faceTextSvg(k.sideMatrix([x, 0.05], z, P, "left"), text, { size, tone, anchor: "start" });
const Tleft = (y, z, text, size, tone = "mid") => k.faceTextSvg(k.sideMatrix([0.05, y], z, P, "right"), text, { size, tone, anchor: "start" });
const circlePts = (cx, cy, r, z, n = 48) => Array.from({ length: n + 1 }, (_, i) => [cx + r * Math.cos(i / n * 2 * Math.PI), cy + r * Math.sin(i / n * 2 * Math.PI), z]);

function base() {
  const o = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of k.corners(PLATE, 16).sort((a, b) => k.depthOf([...a, 0], P) - k.depthOf([...b, 0], P))) {
    o.push(S(k.cylinder(x, y, 6, -PLATE_H - FOOT_H, 1.4, P, 28), { tone: "lo" }));
    o.push(S(k.cylinder(x, y, 4.6, -PLATE_H - FOOT_H + 1.4, FOOT_H - 1.4, P, 28), { tone: "mid" }));
  }
  o.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H - 1.2, P, 8, 1.4), { tone: "mid" }));
  o.push(L(k.planOutline(k.insetPlan(PLATE, 4.5), -1.2, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 8);
  o.push(L(screws.map(([x, y]) => k.ring(x, y, 2, -1.2, P, 16)).join(""), { tone: "lo" }));
  o.push(D(screws.map(([x, y]) => at([x, y, -1.2])), { size: 0.5 }));
  return o.join("");
}
function walls() {   // 뒤 벽(앞 뷰) · 왼 벽(옆 뷰) · 모서리 기둥(높이 자)
  const o = [];
  const back = { x: 0, y: -WT, w: BW, d: WT, r: 0.4 }, left = { x: -WT, y: 0, w: WT, d: BD, r: 0.4 };
  o.push(S(k.slabOf(left, -1.2, BH + 1.2, P, 2, 0.3), { tone: "mid", inner: L(k.planOutline(k.insetPlan(left, 0.6), BH, P, 2), { tone: "faint" }) }));
  o.push(S(k.slabOf(back, -1.2, BH + 1.2, P, 2, 0.3), { tone: "mid" }));
  // 화면 면: 벽 안쪽 면에 종이 + 테두리 + 옅은 격자(10 칸)
  const paperB = [[3, 0.02, 3], [BW - 3, 0.02, 3], [BW - 3, 0.02, BH - 3], [3, 0.02, BH - 3]];
  const paperL = [[0.02, 3, 3], [0.02, BD - 3, 3], [0.02, BD - 3, BH - 3], [0.02, 3, BH - 3]];
  o.push(`<path class="paper" d="${path(paperB, true)}"/><path class="paper" d="${path(paperL, true)}"/>`);
  const grid = [];
  for (let x = 10; x < BW - 3; x += 10) grid.push(seg([x, 0.03, 3], [x, 0.03, BH - 3]));
  for (let z = 10; z < BH - 3; z += 10) grid.push(seg([3, 0.03, z], [BW - 3, 0.03, z]), seg([0.03, 3, z], [0.03, BD - 3, z]));
  for (let y = 10; y < BD - 3; y += 10) grid.push(seg([0.03, y, 3], [0.03, y, BH - 3]));
  o.push(L(grid.join(""), { tone: "faint" }));
  o.push(L(path(paperB, true) + path(paperL, true), { tone: "lo" }));
  o.push(Tback(BW - 18, BH - 7, "앞", 7, "mid"), Tleft(BD - 18, BH - 7, "옆", 7, "mid"));
  // 모서리 기둥: 높이 자(5 칸 눈금)
  const post = { x: -WT - 2.5, y: -WT - 2.5, w: 6, d: 6, r: 0.8 };
  o.push(S(k.slabOf(post, -1.2, BH + 4, P, 3, 0.4), { tone: "mid" }));
  const ticks = [];
  for (let z = 5; z < BH; z += 5) ticks.push(seg([post.x + post.w, post.y + post.d, z], [post.x + post.w - (z % 25 ? 1.2 : 2.4), post.y + post.d, z]));
  o.push(L(ticks.join(""), { tone: "lo" }));
  o.push(S(k.slabOf({ x: post.x - 0.8, y: post.y - 0.8, w: 7.6, d: 7.6, r: 1 }, BH + 2.8, 1.6, P, 3, 0.4), { tone: "mid" }));
  return o.join("");
}
function floor() {   // 바닥 = 위 뷰 화면 · 두 이음 자(x 자 · y 자)
  const o = [S(k.slabOf({ x: 0, y: 0, w: BW, d: BD, r: 0.6 }, -1.2, 1.2, P, 2), { tone: "lo", crease: "none" })];
  o.push(`<path class="paper" d="${path([[3, 3, 0.02], [BW - 3, 3, 0.02], [BW - 3, BD - 3, 0.02], [3, BD - 3, 0.02]], true)}"/>`);
  const grid = [];
  for (let x = 10; x < BW - 3; x += 10) grid.push(k.lineOnTop([x, 3], [x, BD - 3], 0.03, P));
  for (let y = 10; y < BD - 3; y += 10) grid.push(k.lineOnTop([3, y], [BW - 3, y], 0.03, P));
  o.push(L(grid.join(""), { tone: "faint" }));
  o.push(L(path([[3, 3, 0.02], [BW - 3, 3, 0.02], [BW - 3, BD - 3, 0.02], [3, BD - 3, 0.02]], true), { tone: "lo" }));
  o.push(Ttop(BW - 16, BD - 6, 0.03, "위", 7, "mid"));
  // 이음 자: 뒤 이음(x) · 왼 이음(y) — 얇은 띠 + 눈금
  const rx = { x: 3, y: 0.4, w: BW - 6, d: 2.4, r: 0.4 }, ry = { x: 0.4, y: 3, w: 2.4, d: BD - 6, r: 0.4 };
  o.push(S(k.slabOf(rx, 0, 0.5, P, 2), { tone: "lo", crease: "none" }), S(k.slabOf(ry, 0, 0.5, P, 2), { tone: "lo", crease: "none" }));
  const t = [];
  for (let x = 5; x < BW - 3; x += 5) t.push(k.lineOnTop([x, 2.8], [x, 2.8 - (x % 25 ? 1 : 2)], 0.5, P));
  for (let y = 5; y < BD - 3; y += 5) t.push(k.lineOnTop([2.8, y], [2.8 - (y % 25 ? 1 : 2), y], 0.5, P));
  o.push(L(t.join(""), { tone: "mid" }));
  return o.join("");
}
// 세 장의 그림: 선마다 따로(켜기용) · 원은 초록
function drawings() {
  const o = [];
  FRONT.forEach(([a, b], i) => o.push(L(seg(onFront(a), onFront(b)), { className: "dr", tone: "hi" }).replace("<path", `<path data-f="${i}"`)));
  TOPV.forEach(([a, b], i) => o.push(L(seg(onTop(a), onTop(b)), { className: "dr", tone: "hi" }).replace("<path", `<path data-t="${i}"`)));
  o.push(`<path class="iso-line dr dr-arc" data-t="circ" d="${path(circlePts(OX + CYL.c[0], OY + CYL.c[1], CYL.r, 0.05), true)}"/>`);
  SIDE.forEach(([a, b], i) => o.push(L(seg(onSide(a), onSide(b)), { className: "dr", tone: "hi" }).replace("<path", `<path data-s="${i}"`)));
  return `<g data-part="drawings">${o.join("")}</g>`;
}
// 좌표 묶음 안내선: 같은 x(앞 벽 → 바닥) · 같은 높이(앞 벽 → 옆 벽) · 같은 깊이(옆 벽 → 바닥)
const railX = (x) => seg([OX + x, 0.1, OZ + 30], [OX + x, 0.1, 0.1]) + seg([OX + x, 0.1, 0.1], [OX + x, OY + 46, 0.1]);
const railZ = (z) => seg([OX + 66, 0.1, OZ + z], [0.1, 0.1, OZ + z]) + seg([0.1, 0.1, OZ + z], [0.1, OY + 46, OZ + z]);
const railY = (y) => seg([0.1, OY + y, OZ + 30], [0.1, OY + y, 0.1]) + seg([0.1, OY + y, 0.1], [OX + 66, OY + y, 0.1]);
const RAILS = { "z24": railZ(24), "y0": railY(0), "y20": railY(20), "x26": railX(26), "x50": railX(50), "y40": railY(40), "z0": railZ(0), "z12": railZ(12) };
function rails() { return Object.entries(RAILS).map(([n, d]) => `<path class="iso-line rail" data-rail="${n}" style="opacity:0" d="${d}"/>`).join(""); }
// 슬라이더: 뒤 이음(x) · 기둥(z) · 왼 이음(y). 쉬는 자리에 짓고 옮긴다.
const SL0 = { x: 0, y: 0, z: 0 };
function sliders() {
  const sx = { x: OX - 2.5, y: 0, w: 5, d: 4, r: 0.6 }, sy = { x: 0, y: OY - 2.5, w: 4, d: 5, r: 0.6 };
  const sz = { x: -WT - 3.3, y: -WT - 3.3, w: 7.6, d: 7.6, r: 1 };
  const pin = (p) => D([at(p)], { size: 0.9, tone: "red" });
  return [
    `<g data-slider="x">${S(k.slabOf(sx, 0, 2.6, P, 2, 0.3), { tone: "hi", crease: "lo" })}${pin([OX, 4, 2.6])}</g>`,
    `<g data-slider="y">${S(k.slabOf(sy, 0, 2.6, P, 2, 0.3), { tone: "hi", crease: "lo" })}${pin([4, OY, 2.6])}</g>`,
    `<g data-slider="z">${S(k.slabOf(sz, OZ - 1.5, 3, P, 3, 0.3), { tone: "hi", crease: "lo" })}${pin([sz.x + sz.w, sz.y + sz.d, OZ])}</g>`,
  ];
}
// 투영 빛줄(물체보다 먼저 그린다 — 물체 속을 지나는 부분은 물체가 가린다)
function rays() {
  const o = [];
  const three = (p) => { const w = O(p); return seg(w, [w[0], 0.1, w[2]]) + seg(w, [0.1, w[1], w[2]]) + seg(w, [w[0], w[1], 0.1]); };
  const land = (p) => { const w = O(p); return [[w[0], 0.1, w[2]], [0.1, w[1], w[2]], [w[0], w[1], 0.1]].map(at); };
  const intro = [[60, 20, 24], [50, 40, 0], [26, 30, 22]];
  o.push(`<g data-ray="intro" style="opacity:0">${L(intro.map(three).join(""), { className: "ray" })}${D(intro.flatMap(land), { size: 1.1, tone: "gold" })}</g>`);
  // A: 두 모서리에서 앞 벽으로(한 줄에 모인다) · 옆 벽으로(점 둘)
  const toFront = (p) => seg(O(p), [OX + p[0], 0.1, OZ + p[2]]), toSide = (p) => seg(O(p), [0.1, OY + p[1], OZ + p[2]]), toFloor = (p) => seg(O(p), [OX + p[0], OY + p[1], 0.1]);
  const aPts = CASES.A.edges.flatMap(([a, b]) => [a, [30, a[1], a[2]], b]);
  o.push(`<g data-ray="A" style="opacity:0">${L(aPts.map(toFront).join("") + CASES.A.edges.map(([a]) => toSide(a)).join(""), { className: "ray" })}</g>`);
  const cPts = CASES.C.edges[0];
  o.push(`<g data-ray="C" style="opacity:0">${L(cPts.map(toFront).join("") + cPts.map(toSide).join("") + toFloor(cPts[0]), { className: "ray" })}</g>`);
  o.push(`<g data-ray="B" style="opacity:0">${L(toFront([26, 30, 22]) + toFront([26, 30, 12]) + toFloor([26, 30, 12]), { className: "ray" })}</g>`);
  return o.join("");
}
function arm() {   // 모서리 기둥에서 부품 뒤 왼쪽 모서리로 뻗은 팔(보는 방향과 나란해 거의 숨는다)
  const o = [];
  for (let s = 0; s <= 1; s += 0.25) o.push(S(k.cylinder(-1.5 + (OX + 1.5) * s, -1.5 + (OY + 1.5) * s, 1.6, OZ + 16, 3, P, 18), { tone: "mid", crease: "none" }));
  return o.join("");
}
function part() {
  const o = [];
  const bring = BASE.map(([x, y]) => [OX + x, OY + y]);
  o.push(S(k.extrude(bring, OZ, 12, P, { convex: true }), { tone: "hi", crease: "lo" }));
  o.push(S(k.slabOf({ x: OX + UPPER.x, y: OY + UPPER.y, w: UPPER.w, d: UPPER.d, r: 0 }, OZ + 12, 12, P, 1), { tone: "hi", crease: "lo" }));
  o.push(S(k.cylinder(OX + CYL.c[0], OY + CYL.c[1], CYL.r, OZ + CYL.z0, CYL.z1 - CYL.z0, P, 40), { tone: "hi", crease: "lo" }));
  // 3D 모서리(금) · B 의 테(초록 점선 + 빨강 ×)
  const gold = (list, id) => `<g data-gold="${id}" style="opacity:0">${L(list.map(([a, b]) => seg(O(a), O(b))).join(""), { className: "gold" })}${D(list.flat().map((p) => at(O(p))), { size: 1.3, tone: "red" })}</g>`;
  o.push(gold(CASES.A.edges, "A"), gold(CASES.C.edges, "C"));
  const [bx, by] = [OX + 26, OY + 30], m = at([bx, by, OZ + 17]);
  const x = `M${m[0] + 3} ${m[1] - 5}l4 4m0 -4l-4 4`;
  o.push(`<g data-gold="B" style="opacity:0">${L(seg([bx, by, OZ + 12], [bx, by, OZ + 22]), { className: "rim", dotted: true })}<path class="iso-line xmark" data-free="" d="${x}"/></g>`);
  return o.join("");
}
// 화면 위 표시: 꼭짓점(빨강) · 접점(빈 고리)
function marks() {
  const o = [];
  const vtx = (id, pts) => `<g data-mark="${id}" style="opacity:0">${D(pts.map(at), { size: 1.7, tone: "red" })}</g>`;
  o.push(vtx("sA", [onSide([0, 24]), onSide([20, 24])]));
  o.push(vtx("tC", [onTop([50, 40])]));
  o.push(vtx("sC", [onSide([40, 0]), onSide([40, 12])]));
  const tp = onTop([26, 30]);
  o.push(`<g data-mark="tB" style="opacity:0"><path class="iso-line hollow" d="${k.ring(tp[0], tp[1], 2.6, 0.08, P, 20)}"/></g>`);
  return o.join("");
}
function answer() {   // 정답 카드: 3D 모서리 목록
  const o = [S(k.slabOf(HOLD, -1.2, 2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(HOLD, 1.6).map(([x, y]) => at([x, y, 0.8])), { size: 0.42 }));
  o.push(S(k.slabOf(CARD, 0.8, 0.8, P, 4), { tone: "hi", crease: "lo" }));
  const z = 1.62, x0 = CARD.x + 4;
  o.push(Ttop(x0, CARD.y + 7, z, "정답 · 앞의 선에 숨은 3D 모서리", 6, "mid"));
  o.push(L(k.lineOnTop([CARD.x + 2, CARD.y + 9.5], [CARD.x + CARD.w - 2, CARD.y + 9.5], z, P), { tone: "faint" }));
  const rows = [
    ["A", "A 층 → 모서리 2", "", 2],
    ["B", "B 곡면 테 → 모서리 0", "", 0],
    ["C", "C 진짜 → 모서리 1", "", 1],
  ];
  rows.forEach(([id, l, r, n], i) => {
    const y = CARD.y + 18 + i * 9;
    const pips = Array.from({ length: n }, (_, j) => k.lineOnTop([CARD.x + 4 + j * 6, y - 2], [CARD.x + 8.5 + j * 6, y - 2], z, P)).join("");
    o.push(`<g data-row="${id}" style="opacity:0">${Ttop(x0 + 14, y, z, l, 6, "hi")}${pips ? L(pips, { className: "gold pip" }) : L(k.lineOnTop([CARD.x + 5, y - 4], [CARD.x + 9, y], z, P) + k.lineOnTop([CARD.x + 5, y], [CARD.x + 9, y - 4], z, P), { className: "xmark", free: true })}</g>`);
  });
  o.push(`<g data-row="M" style="opacity:0">${L(k.lineOnTop([CARD.x + 2, CARD.y + 40.5], [CARD.x + CARD.w - 2, CARD.y + 40.5], z, P), { tone: "faint" })}${Ttop(x0, CARD.y + 47, z, "잴 것 · 겹친 선의 몫 · 그중 갈린 몫", 5.6, "mid")}</g>`);
  return o.join("");
}
function steps() {   // 번호판 ①~④ (2 × 2)
  const o = [S(k.slabOf(KEYS, -1.2, 2.2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(KEYS, 1.8).map(([x, y]) => at([x, y, 1])), { size: 0.42 }));
  for (let i = 0; i < 4; i++) {
    const kp = { x: KEYS.x + 3.5 + (i % 2) * 14.5, y: KEYS.y + 3.5 + Math.floor(i / 2) * 14.5, w: 12.5, d: 12.5, r: 1.4 };
    o.push(`<g data-step="${i}">${S(k.slabOf(kp, 1, 2.6, P, 3, 0.5), { tone: "mid" })}${k.faceTextSvg(k.topMatrix([kp.x + kp.w / 2, kp.y + kp.d / 2 + 2.6], 3.6, P, "x"), String(i + 1), { size: 7, tone: "mid", anchor: "middle" })}</g>`);
  }
  return o.join("");
}

// ── 시간표 ─────────────────────────────────────────────────────
const LOOP = 42;
const TA = 6, TB = 17, TC = 26.5, TF = 35.5;   // A · B · C · 정답 시작
// 슬라이더 열쇠틀 [t, 값] — 부품 좌표(0 = 쉬는 자리: 부품 원점)
const KF = {
  z: [[0, 0], [TA + 1.6, 0], [TA + 2.6, 24], [TC + 3.6, 24], [TC + 4.6, 6], [TF + 1, 6], [LOOP - 1, 0]],
  y: [[0, 0], [TA + 4.2, 0], [TA + 5.2, 20], [TC + 3.4, 20], [TC + 4.4, 40], [TF + 1, 40], [LOOP - 1, 0]],
  x: [[0, 0], [TB + 1.6, 0], [TB + 2.6, 26], [TC + 1.6, 26], [TC + 2.6, 50], [TF + 1, 50], [LOOP - 1, 0]],
};

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "판 142 세 뷰 짝을 유리 상자로 그린 그림. 계단과 원기둥 보스가 있는 부품이 상자 가운데 떠 있고, 바닥에 위 뷰, 뒤 벽에 앞 뷰, 왼 벽에 옆 뷰가 비친다. 앞 뷰의 선 하나가 켜지면 상자 모서리 자의 슬라이더가 같은 x, 같은 높이, 같은 깊이를 다른 두 장으로 잇는다. A 층: 앞의 가로선 하나가 위에서 평행선 둘이 되어 3D 모서리 둘. B 곡면 테: 원기둥 옆 세로선은 위에서 원에 닿을 뿐 끝이 꼭짓점이 아니라 모서리가 아니다. C 진짜 모서리: 양 끝이 위와 옆의 꼭짓점과 맞아 모서리 하나. 정답 카드에 3D 모서리 수가 적힌다.",
  body: [base(), walls(), floor(), drawings(), rails(), marks(), ...sliders(), rays(), part(), answer(), steps()],
});

const live = `
const P = ${JSON.stringify(P)}, KF = ${JSON.stringify(KF)};
const LOOP = ${LOOP}, TA = ${TA}, TB = ${TB}, TC = ${TC}, TF = ${TF};
const svg = document.querySelector(".iso-stage svg"), stage = document.querySelector(".iso-stage");
const $ = (s) => svg.querySelector(s), $$ = (s) => [...svg.querySelectorAll(s)];
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const keys = $$("[data-step]").sort((a, b) => a.dataset.step - b.dataset.step);
const sl = { x: $('[data-slider="x"]'), y: $('[data-slider="y"]'), z: $('[data-slider="z"]') };
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const ramp = (t, t0, d = 0.5) => ease((t - t0) / d);
const win = (t, t0, t1, d = 0.5) => ramp(t, t0, d) * (1 - ramp(t, t1, d));
const END = LOOP - 1.4;
const kf = (list, t) => { if (t <= list[0][0]) return list[0][1]; for (let i = 1; i < list.length; i++) if (t <= list[i][0]) { const a = list[i - 1], b = list[i]; return a[1] + (b[1] - a[1]) * ease((t - a[0]) / (b[0] - a[0])); } return list[list.length - 1][1]; };
const op = (sel, v) => { for (const e of $$(sel)) e.style.opacity = v; };
const lit = (sel, on, cls = "on") => { for (const e of $$(sel)) e.classList.toggle(cls, on); };
function text(t) {
  if (t < 2.6) return "부품 하나를 위 · 앞 · 옆 세 판에 비춘다 (3 면도)";
  if (t < TA) return "앞 · 위는 x 를, 앞 · 옆은 높이를, 위 · 옆은 깊이를 같이 쓴다";
  if (t < TA + 1.6) return "① A: 앞의 가로선 하나 — 모서리가 몇 개 겹쳤나?";
  if (t < TA + 4.2) return "② 같은 높이를 옆에서 찾는다 → 꼭짓점 둘 (깊이가 다르다)";
  if (t < TA + 6.6) return "② 그 두 깊이를 위로 옮기면 → 평행선 둘";
  if (t < TB) return "③ A 층: 앞 한 줄 = 3D 모서리 2 (앞 · 뒤에 하나씩)";
  if (t < TB + 1.6) return "① B: 원기둥 옆의 세로선 — 이것도 모서리일까?";
  if (t < TB + 4.8) return "② 같은 x 를 위에서 보면 → 원에 닿을 뿐, 꼭짓점이 없다";
  if (t < TC) return "③ B 곡면 테: 보는 쪽 따라 옮겨 가는 테두리 = 모서리 아님";
  if (t < TC + 1.6) return "① C: 깎은 자리의 세로선";
  if (t < TC + 3.4) return "② 같은 x 를 위에서 → 꼭짓점 하나 (깊이 40)";
  if (t < TC + 5.6) return "② 그 깊이를 옆에서 → 양 끝이 꼭짓점과 맞는다";
  if (t < TF) return "③ C 진짜 모서리: 앞 한 줄 = 3D 모서리 1";
  return "한 장에서 겹친 선은 다른 두 장이 가른다";
}
function draw(t) {
  const out = 1 - ramp(t, END, 0.8);
  for (const a of ["x", "y", "z"]) {
    const v = kf(KF[a], t);
    sl[a].setAttribute("transform", translateAlong(P, a === "x" ? [v, 0, 0] : a === "y" ? [0, v, 0] : [0, 0, v]));
  }
  // 도입: 세 판이 비친다
  $('[data-part="drawings"]').style.opacity = 0.15 + 0.85 * ramp(t, 0.6, 1.4);
  op('[data-ray="intro"]', win(t, 0.3, 4.6, 0.8));
  // A
  lit('[data-f="3"]', t >= TA && t < TB);
  op('[data-rail="z24"]', win(t, TA + 2.4, TB - 0.4, 0.5));
  op('[data-mark="sA"]', win(t, TA + 3, TB - 0.4, 0.4));
  op('[data-rail="y0"]', win(t, TA + 4.6, TB - 0.4, 0.5));
  op('[data-rail="y20"]', win(t, TA + 5.0, TB - 0.4, 0.5));
  lit('[data-t="0"], [data-t="5"]', t >= TA + 5.4 && t < TB);
  op('[data-ray="A"]', win(t, TA + 6.8, TB - 0.4, 0.6));
  op('[data-gold="A"]', ramp(t, TA + 7.2, 0.6) * out);
  op('[data-row="A"]', ramp(t, TA + 8.2, 0.5) * out);
  // B
  lit('[data-f="8"]', t >= TB && t < TC);
  op('[data-rail="x26"]', win(t, TB + 2.4, TC - 0.4, 0.5));
  lit('[data-t="circ"]', t >= TB + 3 && t < TC);
  op('[data-mark="tB"]', win(t, TB + 3.2, TC - 0.4, 0.4));
  op('[data-ray="B"]', win(t, TB + 4.8, TC - 0.4, 0.6));
  op('[data-gold="B"]', ramp(t, TB + 5.4, 0.6) * out);
  op('[data-row="B"]', ramp(t, TB + 6.4, 0.5) * out);
  // C
  lit('[data-f="5"]', t >= TC && t < TF);
  op('[data-rail="x50"]', win(t, TC + 2.4, TF - 0.4, 0.5));
  op('[data-mark="tC"]', win(t, TC + 2.8, TF - 0.4, 0.4));
  op('[data-rail="y40"]', win(t, TC + 4.2, TF - 0.4, 0.5));
  op('[data-rail="z0"], [data-rail="z12"]', win(t, TC + 4.4, TF - 0.4, 0.5));
  lit('[data-s="1"]', t >= TC + 4.6 && t < TF);
  op('[data-mark="sC"]', win(t, TC + 4.8, TF - 0.4, 0.4));
  op('[data-ray="C"]', win(t, TC + 5.8, TF - 0.4, 0.6));
  op('[data-gold="C"]', ramp(t, TC + 6.2, 0.6) * out);
  op('[data-row="C"]', ramp(t, TC + 7, 0.5) * out);
  op('[data-row="M"]', ramp(t, TF + 0.6, 0.5) * out);
  // 번호판: 경우마다 ①②③ · 정답 ④
  const loc = (t0) => t - t0 < 1.6 ? 0 : t - t0 < (t0 === TB ? 4.8 : t0 === TA ? 6.6 : 5.6) ? 1 : 2;
  const step = t < TA ? -1 : t < TB ? loc(TA) : t < TC ? loc(TB) : t < TF ? loc(TC) : t < END ? 3 : -1;
  keys.forEach((g, i) => g.toggleAttribute("data-active", i === step));
  readout.textContent = text(t);
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible && !held ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__seek = (t) => { held = true; cancelAnimationFrame(frame); frame = 0; draw(((t % LOOP) + LOOP) % LOOP); };   // 녹화용
if (still.matches) draw(38); else draw(0);
`;
const css = `<style>
.iso{--k-st:var(--anatomy-blue);--k-cu:var(--anatomy-green);--k-v:var(--anatomy-red);--k-au:#c98a00}
.iso[data-theme="dark"],[data-theme="dark"] .iso{--k-au:#f0b429}
.paper{fill:var(--anatomy-lit-top);stroke:none}
.iso-line.dr{stroke-width:1.1;stroke:var(--anatomy-mid);transition:none}
.iso-line.dr-arc{stroke:var(--k-cu);stroke-width:1.1}
.iso-line.dr.on{stroke:var(--k-st);stroke-width:2.6}
.iso-line.dr-arc.on{stroke:var(--k-cu);stroke-width:2.6}
.iso-line.rail{stroke:var(--k-st);stroke-width:.8;stroke-dasharray:3 2}
.iso-line.ray{stroke:var(--k-au);stroke-width:.8;stroke-dasharray:2 1.6}
.iso-line.gold{stroke:var(--k-au);stroke-width:3}
.iso-line.gold.pip{stroke-width:2.4}
.iso-line.rim{stroke:var(--k-cu);stroke-width:2}
.iso-line.xmark{stroke:var(--k-v);stroke-width:1.5;fill:none}
.iso-line.hollow{stroke:var(--k-v);stroke-width:1.3}
.iso-dots[data-tone="red"] circle{fill:var(--k-v);opacity:1}.iso-dots[data-tone="gold"] circle{fill:var(--k-au);opacity:1}
[data-step][data-active] .iso-edge{stroke:var(--anatomy-lit)}[data-step][data-active] .iso-top{fill:var(--anatomy-lit-top)}
[data-step][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
</style>`;
const body = k.plateHtml({
  fig: "그림 6", title: "세 뷰 짝 · 판 142",
  hint: `저절로 돈다 · 한 바퀴 ${LOOP} 초`,
  readout: "부품 하나를 위 · 앞 · 옆 세 판에 비춘다 (3 면도)",
  keys: [
    { mark: "flat", label: "번호판 ① 앞의 선 하나 ② 같은 x · 높이 · 깊이를 다른 두 장에서 ③ 판정 ④ 정답" },
    { mark: "raised", label: "유리 상자 = 3 면도 · 바닥 = 위 · 뒤 벽 = 앞 · 왼 벽 = 옆 · 이음 자의 슬라이더 = 묶인 좌표" },
    { mark: "blue", label: "파랑 = 직선 · 초록 = 원호(원기둥) · 빨강 = 꼭짓점 · 금 = 3D 모서리와 투영 빛줄" },
    { mark: "flat", label: "정답 카드 = 앞의 선마다 숨은 3D 모서리 수 (A 층 2 · B 곡면 테 0 · C 진짜 1)" },
  ],
  caption: "판 142 는 학습 없이 계산만 한다. 3 면도의 세 장은 좌표가 묶여 있다 — 앞 x = 위 x, 앞 높이 = 옆 높이, 위 깊이 = 옆 깊이. 한 장에서는 깊이가 다른 3D 모서리 여럿이 같은 2D 선에 겹치고, 원기둥 옆 테두리 같은 곡면의 테도 모서리와 똑같이 보인다. 그 선의 x 를 위에서, 높이를 옆에서 찾으면 갈린다: 평행선 둘이면 모서리 둘(A 층), 원에 닿을 뿐 끝이 꼭짓점이 아니면 곡면 테(B), 양 끝이 위 · 옆 꼭짓점과 맞으면 진짜 모서리(C). 잴 것은 3D 모서리 둘 이상을 숨긴 2D 선의 몫과, 그중 다른 두 장이 가른 몫이다. 판 142 는 아직 돌지 않았다 — 부품은 설명용이고 숫자는 그리지 않았다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="판 142 세 뷰 짝 동작 그림">${svg}</div>`,
});
mkdirSync(OUT, { recursive: true });
const html = join(OUT, theme === "light" ? "threeview142-light.html" : "threeview142.html");
writeFileSync(html, k.pageHtml({ title: "판 142 세 뷰 짝", theme, body, script: kitScript() + live }));
console.log("wrote", html);

if (RECORD) {   // 8 fps · 2 배 · light → mp4(libx264 yuv420p crf20) + gif(800 폭, 같은 프레임)
  const FPS = 8, DRIVE = "C:/Users/zesky/.claude/skills/anatomy/scripts/drive.mjs", FR = join(OUT, "frames");
  mkdirSync(FR, { recursive: true }); for (const f of readdirSync(FR)) unlinkSync(join(FR, f));   // rmSync 재귀는 한글 경로에서 node 가 죽었다
  const acts = [];
  for (let i = 0; i < LOOP * FPS; i++) acts.push(["eval", `__seek(${(i / FPS).toFixed(3)})`], ["shot", `frames/f${String(i).padStart(3, "0")}.png`, null, 2]);
  writeFileSync(join(OUT, "frames.json"), JSON.stringify(acts));
  execFileSync(process.execPath, [DRIVE, html, "--actions", "frames.json"], { cwd: OUT, stdio: ["ignore", "ignore", "inherit"] });
  const mp4 = join(HERE, "threeview142.mp4"), gif = join(HERE, "threeview142.gif");
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], { stdio: "inherit" });
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse", gif], { stdio: "inherit" });
  console.log("wrote", mp4, gif);
}
