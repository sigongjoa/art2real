// 판정기준65 면 맞춤 — 핀 아트 누름틀: 핀 하나 = 화소 하나 · 핀 높이 = 깊이(가까울수록 높다) · 푸른 칸 = 도면 선으로 막힌 영역 하나
// 다이얼 = 영역 안 뚫린 핀 비율(초록 0–20 % 면 맞춤 · 회색 20–80 % 손 안 댐 · 빨강 80 % 넘음 전부 뚫림) → 누름판이 맞춘 면으로 내려와 핀을 맞춘다
// 세 장면(실제 핀 값 · 핀값.json · 면65.면묶기 그대로): ① 꺾인 판 0 % → 기운 평면 ② 관 49 % → 잠금 · 덩어리 남음 ③ ㄱ자 0 % → 튀는 다리 핀을 잡음으로 보고 눌러 버림(버그)
// node face_fit.mjs → shorts/면맞춤/out/프레임_NNN.png (투명 1000×700 · 180 장 · 30 fps)
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as k from "../anatomy_src/repo/kit/iso-kit.mjs";
import * as G from "../anatomy_src/repo/kit/lathe.mjs";
import { chromePort } from "../anatomy_src/repo/scripts/chrome-port.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(HERE, "shorts", "면맞춤"), OUT = join(DIR, "out");
mkdirSync(OUT, { recursive: true });
const PIN = JSON.parse(readFileSync(join(HERE, "핀값.json"), "utf-8"));
const CASES = [
  { key: "판", name: "꺾인 판", act: "fit", note: "기운 평면으로 맞춤" },
  { key: "관", name: "관", act: "lock", note: "손 안 댐 · 덩어리 남음" },
  { key: "ㄱ", name: "ㄱ자 막대", act: "cut", note: "튀는 핀을 잡음으로 보고 눌러 버림" },
];
{ // 스스로 검사: 다이얼 구간이 판정기준65 규칙과 같다
  const zone = (t) => (t > 0.8 ? "all" : t > 0.2 ? "lock" : "fit");
  console.assert(zone(PIN["판"].통) === "fit" && zone(PIN["관"].통) === "lock" && zone(PIN["ㄱ"].통) === "fit", "zones");
  console.assert(PIN["ㄱ"].pred[0].at(-1) === 0 && PIN["ㄱ"].after[0].at(-1) === 14 && PIN["ㄱ"].truth[0].at(-1) === 0, "ㄱ 다리 핀");
}

// ── 세계 ──  바닥 침대 x 를 따라 14 열 · y 를 따라 10 줄 · 핀 간격 7
const PITCH = 7, COLS = 14, ROWS = 10, BED = { x: -PITCH * COLS / 2 - 6, y: -PITCH * ROWS / 2 - 6, w: PITCH * COLS + 12, d: PITCH * ROWS + 12 }, BED_Z = 14, BED_H = 8;
const HPL = 1.9, topOf = (v) => BED_Z + BED_H + (v === 17 ? 0 : (17 - v) * HPL); // 층 0 = 가장 가까움 = 가장 높은 핀
const cellXY = (r, c, rows, cols) => [(c - (cols - 1) / 2) * PITCH, ((rows - 1) / 2 - r) * PITCH];
const POST = [[BED.x - 4, BED.y + BED.d - 8], [BED.x + BED.w + 4, BED.y + BED.d - 8]], ARM_Z = 82, DIAL = [BED.x + BED.w + 40, -14];
const W = 600, HH = 420;
const fit = [...k.boxCorners({ x: BED.x - 12, y: BED.y - 10, w: BED.w + 78, d: BED.d + 20 }, 0, 0), ...k.boxCorners({ x: BED.x, y: BED.y, w: BED.w, d: BED.d }, 0, ARM_Z + 10), ...k.boxCorners({ x: DIAL[0] - 20, y: DIAL[1] - 3, w: 40, d: 6 }, 0, 84)];
const P = k.fitProjection(fit, W, HH, { pad: 12, azimuth: 38 });
const S = (paths, style) => k.solidSvg(paths, style), at = (p) => k.iso(p, P), d2 = (pts, closed = false) => k.pathOf(pts.map(at), closed);
const F = (o, a) => G.frameAlong(o, a), g = (cls, inner) => (inner ? `<g class="${cls}">${inner}</g>` : "");
const ease = (t) => 1 - (1 - Math.min(1, Math.max(0, t))) ** 3, span = (i, a, b) => (i - a) / (b - a), lerp = (a, b, t) => a + (b - a) * t;
const slab = (pl, z0, h, tone = "mid", bevel = 0.4) => S(k.slabOf({ r: 0.6, ...pl }, z0, h, P, 3, bevel), { tone });
const txt = (p, s, cls = "", size = 16) => { const [x, y] = at(p); return `<text class="lbl ${cls}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" font-size="${size}">${s}</text>`; };

// ── 고정 부품 ──
function bench() {
  const pl = { x: BED.x - 12, y: BED.y - 10, w: BED.w + 78, d: BED.d + 20, r: 4 };
  let s = `<path class="iso-halo" d="${k.haloOf(k.insetPlan(pl, 6), -3, 3, P)}"/>` + g("bench", slab(pl, -3, 3, "mid", 0.8) + k.lineSvg(k.planOutline(k.insetPlan(pl, 4), 0, P, 3), { tone: "faint" }));
  for (const [x, y] of [[pl.x + 4, pl.y + 4], [pl.x + pl.w - 4, pl.y + 4], [pl.x + 4, pl.y + pl.d - 4], [pl.x + pl.w - 4, pl.y + pl.d - 4]]) s += g("stand", S(k.cylinder(x, y, 1.1, 0, 0.4, P, 12), { tone: "lo" }));
  s += g("plate", slab({ x: pl.x + pl.w - 30, y: pl.y + 3, w: 22, d: 8 }, 0, 0.6)) + k.lineSvg([0, 1, 2].map((j) => d2([[pl.x + pl.w - 27, pl.y + 5 + j * 2, 0.7], [pl.x + pl.w - 11 - j * 3, pl.y + 5 + j * 2, 0.7]])).join(""), { tone: "lo", free: true });
  return s;
}
function bed(cs) { // 침대 + 칸 타일(영역 안 = 푸름) + 구멍
  const { rows, cols, m } = cs;
  let s = g("plate", slab(BED, BED_Z, BED_H, "mid", 0.6));
  for (const [x, y] of [[BED.x + 3, BED.y + 3], [BED.x + BED.w - 3, BED.y + 3], [BED.x + 3, BED.y + BED.d - 3], [BED.x + BED.w - 3, BED.y + BED.d - 3]]) s += `<circle class="screw" cx="${at([x, y, BED_Z + BED_H])[0]}" cy="${at([x, y, BED_Z + BED_H])[1]}" r="1.1"/>`;
  let tiles = "", holes = "";
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    if (!m[r][c]) continue;
    const [x, y] = cellXY(r, c, rows, cols);
    tiles += d2([[x - PITCH / 2, y - PITCH / 2, BED_Z + BED_H + 0.05], [x + PITCH / 2, y - PITCH / 2, BED_Z + BED_H + 0.05], [x + PITCH / 2, y + PITCH / 2, BED_Z + BED_H + 0.05], [x - PITCH / 2, y + PITCH / 2, BED_Z + BED_H + 0.05]], true);
    holes += k.ring(x, y, 2.6, BED_Z + BED_H + 0.1, P, 20);
  }
  s += `<path class="tile" d="${tiles}"/><path class="hole" d="${holes}"/>`;
  return s;
}
const posts = () => POST.map(([x, y]) => g("stand", S(k.cylinder(x, y, 3.2, 0, 1.5, P, 20), { tone: "lo" }) + S(k.cylinder(x, y, 2.2, 1.5, ARM_Z - 1.5, P, 16), { tone: "mid", crease: "none" }))).join("") +
  g("plate", slab({ x: POST[0][0] - 3, y: POST[0][1] - 3, w: POST[1][0] - POST[0][0] + 6, d: 6 }, ARM_Z, 5));
function arm() { // 가로대에서 앞으로 나온 팔 + 나사대 + 손잡이(knurl)
  const y0 = POST[0][1] - 3, y1 = 2;
  return g("plate", slab({ x: -5, y: y1 - 4, w: 10, d: y0 - y1 + 4 }, ARM_Z, 5)) + g("stand", S(k.cylinder(0, 0, 4.2, ARM_Z, 5, P, 24, 0.4), { tone: "mid", crease: "lo" })) +
    g("gold", S(k.cylinder(0, 0, 3.4, ARM_Z + 5, 4, P, 24, 0.4), { tone: "mid", crease: "lo" }));
}
function stem(zp) { return g("stand", S(k.cylinder(0, 0, 1.6, zp + 2, ARM_Z - zp - 2, P, 14), { tone: "mid", crease: "none" })); }

// ── 핀 ──  cls: pin · real(초록 · 정답이 맞다고 하는 튀는 핀) · cut(빨강 · 눌려 버려짐) · fixed(파랑 · 맞춤으로 바뀜) · lump(빨강 테 · 정답은 뚫림인데 막힘)
function pins(cs, top, cls) {
  const { rows, cols, m } = cs, items = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    if (!m[r][c]) continue;
    const [x, y] = cellXY(r, c, rows, cols), z1 = top[r][c], h = z1 - (BED_Z + BED_H);
    if (h < 0.3) continue;
    items.push({ d: k.depthOf([x, y, z1], P), s: `<g class="pin ${cls[r][c]}">${S(k.cylinder(x, y, 2.2, BED_Z + BED_H, h, P, 16, 0.3), { tone: "hi", crease: "lo" })}</g>` });
  }
  return items.sort((a, b) => a.d - b.d).map((o) => o.s).join("");
}
function press(cs, plane, zLift, tone = "gold") { // 누름판: 영역 상자 위 · plane(x, y) = 판 밑면 높이 · zLift 만큼 위
  const { rows, cols } = cs, [xa, ya] = cellXY(rows - 1, 0, rows, cols), [xb, yb] = cellXY(0, cols - 1, rows, cols);
  const x0 = xa - PITCH / 2, x1 = xb + PITCH / 2, y0 = ya - PITCH / 2, y1 = yb + PITCH / 2, T = 2.4;
  const z = (x, y) => plane(x, y) + zLift;
  const c = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
  const top = d2(c.map(([x, y]) => [x, y, z(x, y) + T]), true);
  const front = d2([[x0, y0, z(x0, y0)], [x1, y0, z(x1, y0)], [x1, y0, z(x1, y0) + T], [x0, y0, z(x0, y0) + T]], true);
  const side = d2([[x1, y0, z(x1, y0)], [x1, y1, z(x1, y1)], [x1, y1, z(x1, y1) + T], [x1, y0, z(x1, y0) + T]], true);
  const rim = d2(c.map(([x, y]) => [x + Math.sign(x - (x0 + x1) / 2) * -2, y + Math.sign(y - (y0 + y1) / 2) * -2, z(x, y) + T + 0.05]), true);
  return `<g class="press ${tone}"><path class="pf" d="${front}"/><path class="ps" d="${side}"/><path class="pt" d="${top}"/><path class="pr" d="${rim}"/></g>`;
}

// ── 다이얼: 뚫림 비율 · 세 구간 띠 ──
function dial(v) {
  const [cx, cy] = DIAL, cz = 60, r = 17, tv = k.towardViewer(P), L = Math.hypot(tv[0], tv[1]), n = [tv[0] / L, tv[1] / L, 0], u = [n[1], -n[0], 0];   // 다이얼은 보는 쪽을 향함
  const ang = (q) => Math.PI * (1.1 - 1.2 * q), on = (q, rr) => [cx + rr * Math.cos(ang(q)) * u[0] + 1.25 * n[0], cy + rr * Math.cos(ang(q)) * u[1] + 1.25 * n[1], cz + rr * Math.sin(ang(q))];
  let s = g("stand", S(k.cylinder(cx, cy, 3.4, 0, 1.5, P, 20), { tone: "lo" }) + S(k.cylinder(cx, cy, 1.8, 1.5, cz - r - 1.5, P, 14), { tone: "mid", crease: "none" }));
  s += g("paper", S(G.disc(-1.2, 1.2, r, F([cx, cy, cz], n), P), { tone: "hi", crease: "lo" }));
  for (const [a, b, cls] of [[0, 0.2, "zfit"], [0.2, 0.8, "zlock"], [0.8, 1, "zall"]]) s += `<path class="zone ${cls}" d="${d2(Array.from({ length: 13 }, (_, j) => on(lerp(a, b, j / 12), r - 2.2)))}"/>`;
  let ticks = "", major = "";
  for (let j = 0; j <= 10; j++) (j % 5 ? (ticks += d2([on(j / 10, r - 0.8), on(j / 10, r - 1.6)])) : (major += d2([on(j / 10, r - 0.8), on(j / 10, r - 3.2)])));
  s += k.lineSvg(ticks, { tone: "lo" }) + k.lineSvg(major, { tone: "hi" });
  s += `<path class="needle" d="${d2([on(v, -2.5), on(v, r - 3)])}"/><circle class="hub" cx="${at(on(0, 0))[0]}" cy="${at(on(0, 0))[1]}" r="1.8"/>`;
  s += txt([cx, cy, cz + r + 5], `뚫림 ${Math.round(v * 100)} %`, "num", 18);
  s += txt(on(0.02, r + 8), "면 맞춤", "zf", 13) + txt(on(0.5, -8), "손 안 댐", "zl", 12) + txt(on(0.98, r + 8), "전부 뚫림", "za", 13);
  return s;
}
function latch(p) { // 잠금 막대: 팔 옆에서 줄기 쪽으로 미끄러져 들어옴 · ✕
  const x = lerp(-22, -3, p), z = ARM_Z - 7;
  if (p <= 0) return "";
  const [sx, sy] = at([x - 4, 0, z + 1.5]);
  return g("red", slab({ x: x - 10, y: -1.6, w: 10, d: 3.2 }, z, 3)) + `<path class="shut" d="M${sx - 7} ${sy - 7}L${sx + 7} ${sy + 7}M${sx + 7} ${sy - 7}L${sx - 7} ${sy + 7}"/>`;
}

// ── 장면 ──
function caseData(c) {
  const d = PIN[c.key], rows = d.pred.length, cols = d.pred[0].length, m = d.pred.map((r) => r.map((v) => v >= 0));
  return { ...c, rows, cols, m, pred: d.pred, after: d.after, truth: d.truth, 통: d.통 };
}
const DATA = CASES.map(caseData), LEN = 60;
function planeOf(cs) { // 맞춘 뒤 핀 꼭대기에 최소제곱 평면(누름판 밑면) · 뚫림 핀 뺌
  const A = [], b = [];
  for (let r = 0; r < cs.rows; r++) for (let c = 0; c < cs.cols; c++) if (cs.m[r][c] && cs.after[r][c] !== 17) { const [x, y] = cellXY(r, c, cs.rows, cs.cols); A.push([x, y, 1]); b.push(topOf(cs.after[r][c])); }
  const n = A.length, s = (f) => A.reduce((q, a, i) => q + f(a, b[i]), 0);
  const M = [[s((a) => a[0] * a[0]), s((a) => a[0] * a[1]), s((a) => a[0])], [s((a) => a[0] * a[1]), s((a) => a[1] * a[1]), s((a) => a[1])], [s((a) => a[0]), s((a) => a[1]), n]], R = [s((a, y) => a[0] * y), s((a, y) => a[1] * y), s((a, y) => y)];
  const det = (X) => X[0][0] * (X[1][1] * X[2][2] - X[1][2] * X[2][1]) - X[0][1] * (X[1][0] * X[2][2] - X[1][2] * X[2][0]) + X[0][2] * (X[1][0] * X[2][1] - X[1][1] * X[2][0]);
  const D = det(M), col = (j) => det(M.map((row, i) => row.map((v, q) => (q === j ? R[i] : v))));
  const [a, bb, c] = [col(0) / D, col(1) / D, col(2) / D];
  return (x, y) => a * x + bb * y + c;
}
function frame(i) {
  const ci = Math.min(2, Math.floor(i / LEN)), t = i - ci * LEN, cs = DATA[ci];
  const rise = ease(span(t, 0, 12)), needle = cs.통 * ease(span(t, 12, 24)), act = ease(span(t, 24, 40));
  const tops = [], cls = [];
  for (let r = 0; r < cs.rows; r++) { tops.push([]); cls.push([]); for (let c = 0; c < cs.cols; c++) {
    const p = cs.pred[r][c], a = cs.after[r][c], tr = cs.truth[r][c];
    if (p < 0) { tops[r].push(0); cls[r].push(""); continue; }
    const base = BED_Z + BED_H, zp = lerp(base, topOf(p), rise), za = topOf(a);
    let z = zp, cl = "";
    if (cs.act !== "lock" && a !== p) { z = lerp(zp, za, act); cl = cs.act === "cut" && t >= 24 ? "cut" : t >= 24 ? "fixed" : ""; }
    if (cs.act === "cut" && a !== p && tr === p && t < 24 && t >= 12) cl = "real";
    if (cs.act === "lock" && p !== 17 && tr === 17 && t >= 30) cl = "lump";
    tops[r].push(z); cls[r].push(cl);
  } }
  const plane = planeOf(cs); const zLift = cs.act === "lock" ? lerp(16, 10, ease(span(t, 24, 30))) - (t >= 30 ? Math.sin((t - 30) * 1.3) * 0.6 * Math.exp(-(t - 30) / 6) : 0) : lerp(46, 0, act);
  const lockP = cs.act === "lock" ? ease(span(t, 26, 32)) : 0;
  const out = [bench(), posts(), bed(cs), pins(cs, tops, cls), press(cs, cs.act === "lock" ? () => BED_Z + BED_H + 17 * HPL + 4 : plane, zLift, cs.act === "cut" && t >= 36 ? "gold hot" : "gold")];
  out.push(stem(cs.act === "lock" ? BED_Z + BED_H + 17 * HPL + 4 + zLift : plane(0, 0) + zLift), arm(), latch(lockP), dial(needle));
  return out.join("");
}

const frames = Array.from({ length: LEN * 3 }, (_, i) => frame(i)), SEG = { 판: [0, 60], 관: [60, 120], ㄱ: [120, 180] };
writeFileSync(join(DIR, "구간.json"), JSON.stringify({ fps: 30, 프레임: frames.length, 구간: SEG, 장면: CASES }, null, 1));

const CSS = `${k.ISO_CSS}
html,body{margin:0;background:transparent}.shot{width:1000px;height:700px;overflow:hidden}.shot svg{width:1000px;height:700px;display:block}
.lbl{font-family:"Malgun Gothic","맑은 고딕",sans-serif;text-anchor:middle;fill:#333;dominant-baseline:central;font-weight:700}
.lbl.zf{fill:rgb(40,160,80)}.lbl.zl{fill:#77776f}.lbl.za{fill:rgb(220,50,50)}
.gold{--anatomy-paper:#f3d68f;--anatomy-face:#f3d68f;--anatomy-top:#f6dc9c;--anatomy-lit-top:#f6dc9c;--anatomy-shade-0:#c48f1c;--anatomy-shade-1:#d39d26;--anatomy-shade-2:#dcab3a;--anatomy-shade-3:#e8bf5c;--anatomy-mid:#8a5c06;--anatomy-hi:#6b4704;--anatomy-lo:#b88420}
.red{--anatomy-paper:#f2b0b0;--anatomy-top:#f6c4c4;--anatomy-lit-top:#f6c4c4;--anatomy-shade-0:#c84848;--anatomy-shade-1:#d05454;--anatomy-shade-2:#d86060;--anatomy-shade-3:#e07a7a;--anatomy-hi:rgb(150,30,30);--anatomy-lo:rgb(190,40,40)}
.press .pt{fill:#f6dc9c;stroke:#6b4704;stroke-width:1.1}.press .pf{fill:#dcab3a;stroke:#6b4704;stroke-width:1.1}.press .ps{fill:#c48f1c;stroke:#6b4704;stroke-width:1.1}.press .pr{fill:none;stroke:#b88420;stroke-width:.7}
.press{opacity:.55}.press.hot .pt{fill:#f6c4c4;stroke:rgb(150,30,30)}.press.hot .pf{fill:#e07a7a;stroke:rgb(150,30,30)}.press.hot .ps{fill:#c84848;stroke:rgb(150,30,30)}
.pin{--anatomy-paper:#e9e9e6;--anatomy-shade-0:#bdbdb7;--anatomy-shade-1:#c8c8c2;--anatomy-shade-2:#d3d3cd;--anatomy-shade-3:#dcdcd7;--anatomy-top:#f3f3f0;--anatomy-lit-top:#f3f3f0;--anatomy-hi:#55554f;--anatomy-lo:#8e8e88}
.pin.real{--anatomy-paper:#d3ecd9;--anatomy-shade-0:#5fae76;--anatomy-shade-1:#72b987;--anatomy-shade-2:#8bc79c;--anatomy-shade-3:#a8d6b4;--anatomy-top:#e3f3e7;--anatomy-lit-top:#e3f3e7;--anatomy-hi:rgb(30,120,60);--anatomy-lo:rgb(40,160,80)}
.pin.cut{--anatomy-paper:#f7d4d4;--anatomy-shade-0:#d06060;--anatomy-shade-1:#d87272;--anatomy-shade-2:#e08a8a;--anatomy-shade-3:#e9a4a4;--anatomy-top:#fbe3e3;--anatomy-lit-top:#fbe3e3;--anatomy-hi:rgb(160,30,30);--anatomy-lo:rgb(220,50,50)}
.pin.lump{--anatomy-paper:#f7d4d4;--anatomy-shade-0:#d06060;--anatomy-shade-1:#d87272;--anatomy-shade-2:#e08a8a;--anatomy-shade-3:#e9a4a4;--anatomy-top:#fbe3e3;--anatomy-lit-top:#fbe3e3;--anatomy-hi:rgb(160,30,30);--anatomy-lo:rgb(220,50,50)}
.pin.fixed{--anatomy-paper:#d6e4f6;--anatomy-shade-0:#6f99d2;--anatomy-shade-1:#82a7da;--anatomy-shade-2:#98b7e2;--anatomy-shade-3:#b3cbeb;--anatomy-top:#e6eef9;--anatomy-lit-top:#e6eef9;--anatomy-hi:rgb(40,90,170);--anatomy-lo:rgb(60,120,200)}
.tile{fill:rgba(60,120,200,.16);stroke:rgba(60,120,200,.45);stroke-width:.5}.hole{fill:#55554f;stroke:#33332f;stroke-width:.4}.screw{fill:#8e8e88}
.bench{--anatomy-paper:#f4f4f2;--anatomy-top:#f7f7f5;--anatomy-lit-top:#f7f7f5;--anatomy-shade-0:#d9d9d6;--anatomy-shade-1:#e2e2df;--anatomy-shade-2:#ebebe8;--anatomy-shade-3:#f1f1ee}
.plate{--anatomy-paper:#c9c9c4;--anatomy-top:#d6d6d1;--anatomy-lit-top:#d6d6d1;--anatomy-shade-0:#a9a9a3;--anatomy-shade-1:#b3b3ad;--anatomy-shade-2:#bdbdb7;--anatomy-shade-3:#c6c6c0}
.paper{--anatomy-paper:#ffffff;--anatomy-top:#ffffff;--anatomy-lit-top:#ffffff;--anatomy-shade-0:#e4e4e2;--anatomy-shade-1:#ececea;--anatomy-shade-2:#f3f3f1;--anatomy-shade-3:#f9f9f8}
.stand{--anatomy-paper:#d9d9d4;--anatomy-top:#e3e3de;--anatomy-lit-top:#e3e3de;--anatomy-shade-0:#bdbdb7;--anatomy-shade-1:#c6c6c0;--anatomy-shade-2:#cfcfc9;--anatomy-shade-3:#d6d6d1}
.zone{fill:none;stroke-width:3.2;stroke-linecap:butt}.zfit{stroke:rgb(40,160,80)}.zlock{stroke:#b0b0a8}.zall{stroke:rgb(220,50,50)}
.needle{fill:none;stroke:#222;stroke-width:1.8;stroke-linecap:round}.hub{fill:#333}.shut{fill:none;stroke:rgb(220,50,50);stroke-width:3.4;stroke-linecap:round}`;
writeFileSync(join(DIR, "index.html"), `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body>${frames.map((body, i) => `<div class="shot iso" data-theme="light">${k.figureSvg({ width: W, height: HH, label: `면 맞춤 프레임 ${i}`, body })}</div>`).join("")}</body></html>`);
if (process.argv.includes("--html")) process.exit(0);

const binary = [process.env.LOCALAPPDATA && join(process.env.LOCALAPPDATA, "Google\\Chrome\\Application\\chrome.exe"), "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"].find((p) => p && existsSync(p));
const profile = mkdtempSync(join(tmpdir(), "face-"));
const proc = spawn(binary, ["--headless=new", "--do-not-de-elevate", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run", "--hide-scrollbars", "--allow-file-access-from-files", "about:blank"]);
const port = await chromePort(proc, profile);
const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
await new Promise((r) => (ws.onopen = r));
const send = (method, params = {}) => new Promise((r) => { const c = ++id; pending.set(c, r); ws.send(JSON.stringify({ id: c, method, params })); });
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1000, height: 700, deviceScaleFactor: 1, mobile: false });
await send("Emulation.setDefaultBackgroundColorOverride", { color: { r: 0, g: 0, b: 0, a: 0 } });
await send("Page.navigate", { url: pathToFileURL(join(DIR, "index.html")).href });
await new Promise((r) => setTimeout(r, 3000));
const only = process.argv.find((a) => a.startsWith("--only="));
const list = only ? only.slice(7).split(",").map(Number) : frames.map((_, i) => i);
for (const i of list) {
  const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: i * 700, width: 1000, height: 700, scale: 1 } });
  writeFileSync(join(OUT, `프레임_${String(i).padStart(3, "0")}.png`), Buffer.from(shot.result.data, "base64"));
}
console.log("frames", list.length);
proc.kill("SIGKILL");
try { rmSync(profile, { recursive: true, force: true }); } catch {}
