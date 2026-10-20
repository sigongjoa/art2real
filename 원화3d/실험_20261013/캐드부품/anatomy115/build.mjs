// Fig — 새 구조에서 모델이 어떻게 배우나: 후보 카드 넷(기하가 뽑은 코드) · 확률 슬라이더 넷(모델) · 깊이 게이지(CAD 가 깎은 컵) · 광학 비교기(다시 그린 단면 ↔ 원화 차트) · 10-20
// 사용: node build.mjs [--light] → learn115.html (모델 = model.mjs · 부품 59 실제 후보)
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const KIT = "C:/Users/zesky/.claude/skills/anatomy/";
const k = await import(pathToFileURL(KIT + "kit/iso-kit.mjs").href);
const { kitScript } = await import(pathToFileURL(KIT + "scripts/inline-kit.mjs").href);
import * as M from "./model.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 420;
const PLATE = { x: -172, y: -52, w: 344, d: 92, r: 8 }, PLATE_H = 12, FOOT_H = 5;
const RACK = { x: -162, y: -46, w: 150, d: 50, r: 3 }, RACK_H = 8;
const CX = [-146, -112, -78, -44];          // 카드 · 슬라이더 가운데 x
const CARD_Y = -26, CARD_Z0 = RACK_H, CARD_H = 46, CUP_Z0 = RACK_H + 7;   // 카드 앞면 y · 컵 단면 바닥 z
const ROD_DX = 15, ROD_Y = -24, ROD_Z0 = RACK_H, ROD_H = 40, COLLAR_H = 3, SPAN = 32;  // 슬라이더 막대 · 칼라 이동 폭 = 확률 1
const RAIL_Y = -6;   // 카드 앞(+y 가 보는 쪽)
const CUP = [8, -6], CUP_R = 13, STAGE_Z = 4, CUP_Z = STAGE_Z + 3, CUP_TOP = CUP_Z + M.CUP.h * 0.75;
const DIAL = [8, -6], DIAL_R = 15, DIAL_Z = 74, DIAL_H = 8, DIAL_TOP = DIAL_Z + DIAL_H;
const POST = [8, -40], ARM_Z = 86;   // 컵 뒤
const SCR = { x: 52, y: -10, w: 96, d: 5, r: 1 }, SCR_Z0 = 10, SCR_H = 78;   // 비교기 스크린 판(앞면 y = SCR.y)
const SC = [100, 44], SCALE = 1.25;          // 스크린 위 단면 가운데(x, z 바닥) · 확대
const MDIAL = [80, 14], MDIAL_R = 13, MDIAL_Z = 6, MDIAL_TOP = MDIAL_Z + 6;

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [SCR.x, SCR.y, SCR_Z0 + SCR_H + 4], [SCR.x + SCR.w, SCR.y + SCR.d, SCR_Z0 + SCR_H + 4], [DIAL[0], DIAL[1], DIAL_TOP + 4], [POST[0], POST[1], ARM_Z + 6]], WIDTH, HEIGHT, { pad: 22, azimuth: 140 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const seg = (a, b) => { const A = at(a), B = at(b); return `M${A[0].toFixed(2)} ${A[1].toFixed(2)}L${B[0].toFixed(2)} ${B[1].toFixed(2)}`; };
const poly = (pts, closed) => pts.map((p, i) => { const q = at(p); return (i ? "L" : "M") + q[0].toFixed(2) + " " + q[1].toFixed(2); }).join("") + (closed ? "Z" : "");

// 컵 단면(가운데 cx · 바닥 z0 · 배율 s · 바닥 층 Lc) 을 y = face 평면에 — 바깥 · 안 벽 · 바닥선
function section(cx, z0, s, Lc, face) {
  const h = M.CUP.h * s, o = M.CUP.outer * s, n = M.CUP.inner * s, d = M.depthOf(Lc) * s, top = z0 + h;
  const pt = (x, z) => [x, face, z];
  if (Lc >= M.LAYERS) return [[pt(cx - o, z0), pt(cx - o, top), pt(cx - n, top), pt(cx - n, z0)], [pt(cx + n, z0), pt(cx + n, top), pt(cx + o, top), pt(cx + o, z0)]];
  return [[pt(cx - o, z0), pt(cx - o, top), pt(cx - n, top), pt(cx - n, top - d), pt(cx + n, top - d), pt(cx + n, top), pt(cx + o, top), pt(cx + o, z0), pt(cx - o, z0)]];
}
const sectionPath = (cx, z0, s, Lc, face) => section(cx, z0, s, Lc, face).map((r) => poly(r, false)).join("");

function plate() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  const byDepth = (pts) => [...pts].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
  for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }), D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  const strip = { x: -150, y: PLATE.y + 6, w: 120, d: 7, r: 1 };   // 앞쪽 눈금 띠
  out.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + 0.8, 0.6, [2, 3.6], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }), D([at([strip.x + 2, strip.y + 3.5, 0.6]), at([strip.x + strip.w - 2, strip.y + 3.5, 0.6])], { size: 0.45 }));
  const lp = { x: -10, y: PLATE.y + 5, w: 34, d: 12, r: 1.5 };   // 이름판
  out.push(S(k.slabOf(lp, 0, 0.8, P, 3, 0.3), { tone: "lo", crease: "none" }));
  for (const yy of [lp.y + 3.5, lp.y + 6, lp.y + 8.5]) out.push(L(k.lineOnTop([lp.x + 4, yy], [lp.x + lp.w - 4, yy], 0.8, P), { tone: "faint", free: true }));
  out.push(D(k.corners(lp, 1.8).map(([x, y]) => at([x, y, 0.8])), { size: 0.4 }));
  return out.join("");
}

function rack() {   // 후보 판대 · 카드 넷 · 레일
  const out = [S(k.slabOf(RACK, 0, RACK_H, P, 6, 0.8), { tone: "mid" })];
  out.push(L(k.planOutline(k.insetPlan(RACK, 3), RACK_H, P), { tone: "faint" }), D(k.corners(RACK, 4).map(([x, y]) => at([x, y, RACK_H])), { size: 0.45 }));
  CX.forEach((cx, i) => {   // 카드 홈 · 카드 · 새긴 단면 · 번호
    out.push(S(k.slabOf({ x: cx - 13, y: CARD_Y - 1.5, w: 26, d: 6, r: 0.8 }, RACK_H, 2, P, 3, 0.3), { tone: "lo" }));
    const card = { x: cx - 11, y: CARD_Y, w: 22, d: 2.4, r: 0.5 };
    out.push(S(k.slabOf(card, CARD_Z0 + 2, CARD_H, P, 2, 0.3), { tone: "hi", crease: "lo", inner: `<path class="iso-line" data-tone="mid" d="${sectionPath(cx, CUP_Z0, 1, M.CANDS[i].L, CARD_Y + 2.42)}"/>` }));
    out.push(k.faceTextSvg(k.sideMatrix([cx - 9, CARD_Y + 2.42], CARD_Z0 + CARD_H - 1, P, "left"), M.CANDS[i].L >= 32 ? "관통" : "층 " + M.CANDS[i].L, { size: 3, tone: "lo" }));
  });
  out.push(S(k.slabOf({ x: RACK.x + 4, y: RAIL_Y, w: RACK.w - 8, d: 4, r: 1 }, RACK_H, 2, P, 3, 0.4), { tone: "mid" }));
  out.push(D([RACK.x + 8, RACK.x + RACK.w - 8].map((x) => at([x, RAIL_Y + 2, RACK_H + 2])), { size: 0.4 }));
  return out.join("");
}
const rodOf = (c0) => { const cx = c0 + ROD_DX; return S(k.cylinder(cx, ROD_Y, 1.1, ROD_Z0 + 2, ROD_H, P, 16), { tone: "mid", crease: "none" }) + S(k.cylinder(cx, ROD_Y, 3, ROD_Z0, 2, P, 24), { tone: "mid" }) + S(k.cylinder(cx, ROD_Y, 2, ROD_Z0 + 2 + ROD_H, 1.4, P, 16), { tone: "mid" }); };
const collarOf = (c0, lit) => { const cx = c0 + ROD_DX; return S(k.cylinder(cx, ROD_Y, 3.4, 0, COLLAR_H, P, 28, 0.4), { tone: "hi", lit }) + L(k.knurl(cx, ROD_Y, 3.4, 0.4, COLLAR_H - 0.4, 18, P), { tone: "lo" }); };
const carriageOf = () => S(k.slabOf({ x: -7, y: RAIL_Y - 2, w: 14, d: 8, r: 1.5 }, RACK_H + 2, 4, P, 4, 0.5), { tone: "mid" }) + S(k.cylinder(0, RAIL_Y + 2, 2.2, RACK_H + 6, 2, P, 20), { tone: "hi", lit: true }) + D([at([-4.5, RAIL_Y + 4, RACK_H + 6]), at([4.5, RAIL_Y + 4, RACK_H + 6])], { size: 0.4 });

function stage() {   // 깎은 컵 · 깊이 게이지
  const out = [S(k.cylinder(CUP[0], CUP[1], 20, 0, STAGE_Z, P, 48, 0.6), { tone: "mid" })];
  out.push(L(k.radialTicks(CUP[0], CUP[1], 18.5, 36, 6, STAGE_Z, [1, 2], P).minor, { tone: "lo" }));
  out.push(S(k.cylinder(CUP[0], CUP[1], 15, STAGE_Z, CUP_Z - STAGE_Z, P, 40), { tone: "mid" }));
  out.push(S(k.cylinder(CUP[0], CUP[1], CUP_R, CUP_Z, CUP_TOP - CUP_Z, P, 48, 0.5), { tone: "hi", crease: "lo", inner: `<path class="iso-line" data-tone="faint" d="${k.sideArc(CUP[0], CUP[1], CUP_R, CUP_Z + 6, P, 30)}"/>` }));
  out.push(`<path class="iso-solid" data-tone="lo" d="${k.pathOf(k.circleRing(CUP[0], CUP[1], CUP_R * M.CUP.inner / M.CUP.outer, 40).map((p) => at([p[0], p[1], CUP_TOP])), true)}" style="fill:var(--iso-lo, #333)"/>`);
  out.push(L(k.ring(CUP[0], CUP[1], CUP_R * M.CUP.inner / M.CUP.outer, CUP_TOP, P, 40), { tone: "mid" }));
  return out.join("");
}
function gauge() {   // 기둥 · 팔 · 다이얼(깊이)
  const out = [S(k.cylinder(POST[0], POST[1], 6, 0, 3, P, 28), { tone: "mid" }), S(k.cylinder(POST[0], POST[1], 2.8, 3, ARM_Z - 3, P, 24), { tone: "mid", crease: "none" })];
  out.push(L([30, 55].map((z) => k.sideArc(POST[0], POST[1], 2.8, z, P, 14)).join(""), { tone: "faint" }));
  const arm = { x: POST[0] - 3, y: POST[1] - 3, w: 6, d: DIAL[1] - DIAL_R - POST[1] + 5, r: 2 };
  out.push(S(k.slabOf(arm, ARM_Z - 4, 4, P, 4, 0.5), { tone: "mid" }), D([at([POST[0], POST[1], ARM_Z]), at([POST[0], arm.y + arm.d - 3, ARM_Z])], { size: 0.45 }));
  out.push(S(k.slabOf({ x: DIAL[0] - 4, y: DIAL[1] - DIAL_R - 2, w: 8, d: 5, r: 1.5 }, DIAL_Z + 1, ARM_Z - DIAL_Z - 1, P, 3, 0.4), { tone: "mid" }));
  return out.join("");
}
function gaugeTop() {
  const out = [S(k.cylinder(DIAL[0], DIAL[1], 2.6, DIAL_Z - 10, 10, P, 20), { tone: "mid" })];
  out.push(S(k.cylinder(DIAL[0], DIAL[1], DIAL_R, DIAL_Z, DIAL_H, P, 64, 0.8), { tone: "hi", crease: "lo" }));
  out.push(L(k.knurl(DIAL[0], DIAL[1], DIAL_R, DIAL_TOP - 3, DIAL_TOP, 70, P, 0.3), { tone: "lo" }), L(k.ring(DIAL[0], DIAL[1], DIAL_R - 2, DIAL_TOP, P, 64), { tone: "lo" }));
  const t = k.radialTicks(DIAL[0], DIAL[1], DIAL_R - 2.6, 32, 4, DIAL_TOP, [1.1, 2.4], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }), L(k.ring(DIAL[0], DIAL[1], 1.4, DIAL_TOP, P, 16), { tone: "mid" }));
  return out.join("");
}
const plungerOf = () => S(k.cylinder(DIAL[0], DIAL[1], 1.2, 0, DIAL_Z - 10 - CUP_Z, P, 16), { tone: "hi", crease: "none" }) + S(k.cylinder(DIAL[0], DIAL[1], 2, 0, 1.6, P, 16), { tone: "hi" });

function comparator() {   // 스크린 판 · 다리 · 원화 차트 · 어긋남 다이얼 · 회차 계수기
  const out = [];
  const base = { x: SCR.x - 4, y: -30, w: SCR.w + 8, d: 58, r: 3 };
  out.push(S(k.slabOf(base, 0, 6, P, 6, 0.6), { tone: "mid" }), L(k.planOutline(k.insetPlan(base, 3), 6, P), { tone: "faint" }), D(k.corners(base, 4).map(([x, y]) => at([x, y, 6])), { size: 0.45 }));
  for (const x of [SCR.x + 8, SCR.x + SCR.w - 8]) out.push(S(k.slabOf({ x: x - 3, y: SCR.y - 1, w: 6, d: SCR.d + 6, r: 1 }, 6, SCR_Z0 - 6 + 6, P, 3, 0.4), { tone: "mid" }));
  const glassLines = [];   // 스크린 안 테 · 눈금 십자 · 원화 차트(정답 층 16)
  const f = SCR.y + SCR.d + 0.02, gx0 = SCR.x + 6, gx1 = SCR.x + SCR.w - 6, gz0 = SCR_Z0 + 6, gz1 = SCR_Z0 + SCR_H - 6;
  glassLines.push(poly([[gx0, f, gz0], [gx1, f, gz0], [gx1, f, gz1], [gx0, f, gz1]], true));
  out.push(S(k.slabOf(SCR, SCR_Z0, SCR_H, P, 2, 0.6), { tone: "hi", crease: "lo", inner: `<path class="iso-line" data-tone="lo" d="${glassLines.join("")}"/><path class="iso-line" data-tone="faint" d="${seg([SC[0], f, gz0], [SC[0], f, gz1]) + seg([gx0, f, SC[1] + M.CUP.h * SCALE * 0.5], [gx1, f, SC[1] + M.CUP.h * SCALE * 0.5])}"/><path class="iso-line" data-tone="mid" d="${sectionPath(SC[0], SC[1] - 10, SCALE, M.TRUTH, f)}"/>` }));
  out.push(D([[SCR.x + 3, SCR_Z0 + 3], [SCR.x + SCR.w - 3, SCR_Z0 + 3], [SCR.x + 3, SCR_Z0 + SCR_H - 3], [SCR.x + SCR.w - 3, SCR_Z0 + SCR_H - 3]].map(([x, z]) => at([x, f, z])), { size: 0.45 }));
  out.push(S(k.cylinder(MDIAL[0], MDIAL[1], MDIAL_R, MDIAL_Z, 6, P, 56, 0.6), { tone: "hi", crease: "lo" }), L(k.ring(MDIAL[0], MDIAL[1], MDIAL_R - 2, MDIAL_TOP, P, 56), { tone: "lo" }));
  const t = k.radialTicks(MDIAL[0], MDIAL[1], MDIAL_R - 2.4, 20, 5, MDIAL_TOP, [1, 2.2], P, -Math.PI * 0.75, Math.PI * 1.5);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }), L(k.ring(MDIAL[0], MDIAL[1], 1.2, MDIAL_TOP, P, 14), { tone: "mid" }));
  const ctr = { x: 104, y: 10, w: 30, d: 14, r: 2 };   // 회차 계수기
  out.push(S(k.slabOf(ctr, 6, 6, P, 4, 0.5), { tone: "mid" }), S(k.slabOf(k.insetPlan(ctr, 3), 12, 0.6, P, 3), { tone: "lo", crease: "none" }));
  out.push(`<g data-part="epoch">${k.faceTextSvg(k.topMatrix([ctr.x + 6, ctr.y + 9], 12.6, P, "x"), "1", { size: 6, tone: "hi" })}</g>`);
  out.push(k.wireSvg(at([DIAL[0] + DIAL_R, DIAL[1], DIAL_Z + 4]), at([SCR.x, SCR.y + 2, SCR_Z0 + SCR_H - 12]), { via: [at([40, -12, DIAL_Z + 6])], tone: "lo" }));
  return out.join("");
}
const cardLit = M.CANDS.map((c, i) => `<path data-part="cardlit" data-i="${i}" class="iso-line" data-tone="lit" d="${sectionPath(CX[i], CUP_Z0, 1, c.L, CARD_Y + 2.44)}" style="stroke-width:1.1;opacity:${i ? 0 : 1}"/>`).join("");
const shadows = M.CANDS.map((c, i) => `<path data-part="shadow" data-i="${i}" class="iso-line" data-tone="lit" d="${sectionPath(SC[0], SC[1] - 10, SCALE, c.L, SCR.y + SCR.d + 0.04)}" style="stroke-width:1.2;opacity:${i ? 0 : 1}"/>`).join("");
const bands = M.CANDS.map((c, i) => {   // 어긋난 띠: 원화 바닥과 후보 바닥 사이 빗금
  const f = SCR.y + SCR.d + 0.03, n = M.CUP.inner * SCALE, top = SC[1] - 10 + M.CUP.h * SCALE, a = top - M.depthOf(M.TRUTH) * SCALE, b = top - M.depthOf(c.L) * SCALE;
  const lines = []; for (let x = SC[0] - n + 1.5; x < SC[0] + n; x += 2.5) lines.push(seg([x, f, Math.min(a, b)], [x, f, Math.max(a, b)]));
  return `<path data-part="band" data-i="${i}" class="iso-line" data-tone="lo" d="${lines.join("")}" style="opacity:${i ? 0 : 1}"/>`;
}).join("");
const needleAt = (cx, cy, r, z, frac, from = 0, span = Math.PI * 2) => { const a = from + frac * span; return k.lineOnTop([cx - Math.sin(a) * 2.4, cy + Math.cos(a) * 2.4], [cx + Math.sin(a) * r, cy - Math.cos(a) * r], z, P); };

const RUN = M.train(6);
const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "학습 장치: 기하가 뽑은 코드 후보 카드 넷, 그 앞의 확률 슬라이더 넷, 고른 후보로 깎은 컵과 깊이 게이지, 다시 그린 단면을 원화 차트와 겹치는 광학 비교기. 매 회 비교기가 후보 넷을 다 재고 가장 덜 어긋난 후보 쪽으로 슬라이더가 올라간다.",
  body: [plate(), ...[   // 큰 덩어리는 깊이 순(뒤 → 앞)으로
    [[POST[0], POST[1], 0], gauge() + `<g data-part="plunger" transform="${k.translateAlong(P, [0, 0, CUP_Z + (M.CUP.h - M.depthOf(0)) * 0.75])}">${plungerOf()}</g>`],
    [[CUP[0], CUP[1], 0], stage()],
    [[DIAL[0], DIAL[1] - 20, 0], gaugeTop() + `<path data-part="dneedle" class="iso-line" data-tone="hi" data-free="start" d="${needleAt(DIAL[0], DIAL[1], DIAL_R - 3.5, DIAL_TOP + 0.2, 0)}" style="stroke-width:1.1"/>`],
    [[SCR.x + SCR.w / 2, SCR.y, 0], comparator() + bands + shadows + `<path data-part="mneedle" class="iso-line" data-tone="hi" data-free="start" d="${needleAt(MDIAL[0], MDIAL[1], MDIAL_R - 3, MDIAL_TOP + 0.2, 0, -Math.PI * 0.75, Math.PI * 1.5)}" style="stroke-width:1.1"/>`],
    [[RACK.x + RACK.w / 2, RACK.y + RACK.d / 2, 0], rack() + CX.map((cx) => rodOf(cx)).join("") + CX.map((cx, i) => `<g data-part="collar" data-i="${i}" transform="${k.translateAlong(P, [0, 0, ROD_Z0 + 2 + SPAN * 0.25])}">${collarOf(cx, false)}</g>`).join("") + `<g data-part="carriage" transform="${k.translateAlong(P, [CX[0], 0, 0])}">${carriageOf()}</g>` + cardLit],
  ].sort((a, b) => k.depthOf(a[0], P) - k.depthOf(b[0], P)).map((g) => g[1])],
});

const live = `
const P = ${JSON.stringify(P)}, RUN = ${JSON.stringify(RUN)}, CANDS = ${JSON.stringify(M.CANDS)}, CX = ${JSON.stringify(CX)};
const LAYERS = ${M.LAYERS}, CUPH = ${M.CUP.h}, CUP_Z = ${CUP_Z}, ROD0 = ${ROD_Z0 + 2}, SPAN = ${SPAN};
const DIAL = ${JSON.stringify(DIAL)}, DIAL_R = ${DIAL_R}, DIAL_TOP = ${DIAL_TOP}, MDIAL = ${JSON.stringify(MDIAL)}, MDIAL_R = ${MDIAL_R}, MDIAL_TOP = ${MDIAL_TOP};
const 층깊이 = (L) => CUPH * Math.min(L, LAYERS) / LAYERS;
const needleAt = (cx, cy, r, z, frac, from = 0, span = Math.PI * 2) => { const a = from + frac * span; return lineOnTop([cx - Math.sin(a) * 2.4, cy + Math.cos(a) * 2.4], [cx + Math.sin(a) * r, cy - Math.cos(a) * r], z, P); };
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg"), readout = document.querySelector("[data-readout]");
const q = (s) => [...svg.querySelectorAll(s)];
const collars = q('[data-part="collar"]'), carriage = svg.querySelector('[data-part="carriage"]'), plunger = svg.querySelector('[data-part="plunger"]');
const dneedle = svg.querySelector('[data-part="dneedle"]'), mneedle = svg.querySelector('[data-part="mneedle"]'), shadows = q('[data-part="shadow"]'), cardLit = q('[data-part="cardlit"]'), bands = q('[data-part="band"]'), epochText = svg.querySelector('[data-part="epoch"] text');
const still = matchMedia("(prefers-reduced-motion: reduce)");
// 대본: 회차마다 후보 넷을 차례로 재고(0.95 초씩) → 슬라이더 갱신(1.4 초) · 6 회 뒤 「쓸 때」: 가장 높은 후보 하나만 재기(2.4 초) · 그리고 처음부터
const STEPS = []; RUN.forEach((r, e) => { r.reads.forEach((m, i) => STEPS.push({ kind: "read", e, i, m, p: r.p, dur: 0.95 })); STEPS.push({ kind: "learn", e, p: r.after, best: r.best, dur: 1.4 }); });
const final = RUN[RUN.length - 1].after, pick = final.indexOf(Math.max(...final));
STEPS.push({ kind: "use", e: RUN.length, i: pick, m: RUN[0].reads[pick], p: final, dur: 2.6 });
const TOTAL = STEPS.reduce((a, s) => a + s.dur, 0);
let clock = 0, last = 0, frame = 0, visible = false;
const cur = { x: CX[0], depth: 층깊이(CANDS[0].L), mis: RUN[0].reads[0], p: [...RUN[0].p] };
function stepAt(t) { let s = 0; for (const st of STEPS) { if (t < s + st.dur) return [st, (t - s) / st.dur]; s += st.dur; } return [STEPS[STEPS.length - 1], 1]; }
function draw(st) {
  carriage.setAttribute("transform", translateAlong(P, [cur.x, 0, 0]));
  plunger.setAttribute("transform", translateAlong(P, [0, 0, CUP_Z + (CUPH - cur.depth) * 0.75]));
  dneedle.setAttribute("d", needleAt(DIAL[0], DIAL[1], DIAL_R - 3.5, DIAL_TOP + 0.2, cur.depth / CUPH));
  mneedle.setAttribute("d", needleAt(MDIAL[0], MDIAL[1], MDIAL_R - 3, MDIAL_TOP + 0.2, Math.min(cur.mis / 0.5, 1), -Math.PI * 0.75, Math.PI * 1.5));
  collars.forEach((c, i) => c.setAttribute("transform", translateAlong(P, [0, 0, ROD0 + SPAN * cur.p[i]])));
  const show = st.kind === "learn" ? st.best : st.i;
  shadows.forEach((s, i) => { s.style.opacity = i === show ? 1 : 0; }); bands.forEach((b, i) => { b.style.opacity = i === show ? 1 : 0; }); cardLit.forEach((b, i) => { b.style.opacity = i === show ? 1 : 0; });
  collars.forEach((c, i) => c.querySelectorAll(".iso-solid, [data-lit]").forEach(() => {}));
  if (epochText && epochText.textContent !== String(Math.min(st.e + 1, RUN.length))) epochText.textContent = st.kind === "use" ? "✓" : String(st.e + 1);
  const L = CANDS[show].L, name = L >= LAYERS ? "관통" : "층 " + L;
  const text = st.kind === "use" ? "학습 뒤 · 모델이 고른 " + name + " · 어긋남 " + (100 * st.m).toFixed(1) + " % · 확률 " + st.p[show].toFixed(2)
    : st.kind === "learn" ? (st.e + 1) + " 회 학습 · 가장 덜 어긋난 " + name + " 쪽으로 · 확률 " + st.p[st.best].toFixed(2)
    : (st.e + 1) + " 회 · 후보 " + name + " 다시 그림 · 어긋남 " + (100 * st.m).toFixed(1) + " %";
  if (readout.textContent !== text) readout.textContent = text;
}
function tick(now) {
  if (window.__rec) { frame = 0; return; }
  const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60; last = now; update(dt); frame = visible ? requestAnimationFrame(tick) : 0;
}
window.__step = (dt) => { window.__rec = true; update(dt); return clock; };   // 영상 녹화: 고정 dt 로 한 칸씩
window.__total = TOTAL;
function update(dt) {
  clock = (clock + dt) % TOTAL;
  const [st] = stepAt(clock), ease = (a, b, tau) => a + (b - a) * (1 - Math.exp(-dt / tau));
  const i = st.kind === "learn" ? st.best : st.i;
  cur.x = ease(cur.x, CX[i], 0.16); cur.depth = ease(cur.depth, 층깊이(CANDS[i].L), 0.14); cur.mis = ease(cur.mis, st.kind === "learn" ? RUN[st.e].reads[st.best] : st.m, 0.12);
  cur.p = cur.p.map((v, j) => ease(v, (st.kind === "read" ? st.p : st.p)[j], 0.35));
  draw(st);
}
const run = () => { if (!frame && visible && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } };
new IntersectionObserver((es) => { visible = es[es.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
const restart = () => { clock = 0; cur.p = [...RUN[0].p]; run(); };
stage.addEventListener("click", restart); stage.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); restart(); } });
if (still.matches) { const st = STEPS[STEPS.length - 1]; cur.x = CX[st.i]; cur.depth = 층깊이(CANDS[st.i].L); cur.mis = st.m; cur.p = [...st.p]; draw(st); } else draw(STEPS[0]);
`;
const body = k.plateHtml({
  fig: "Fig 115", title: "코드 후보 고르기 학습",
  hint: "가만히 두면 학습이 돈다 · 누르면 처음부터",
  readout: "1 회 · 후보 층 0 다시 그림 · 어긋남 45.5 %",
  keys: [
    { mark: "lit", label: "모델: 슬라이더 칼라 높이 = 그 후보를 고를 확률 (넷의 합 1)" },
    { mark: "raised", label: "후보 카드: 기하가 다른 도면 선에서 뽑은 코드(부품 59 실제 후보 층 0 · 15 · 31 · 관통)" },
    { mark: "lit", label: "비교기: 고른 후보로 깎아 다시 그린 단면(밝은 선)을 원화 차트(정답 층 16)에 겹쳐 어긋난 넓이를 잰다" },
  ],
  caption: "학습 때는 비교기가 후보 넷을 다 다시 그려 원화와 맞대고, 가장 덜 어긋난 후보(층 15 · 2.8 %)를 정답으로 삼아 확률을 교차 엔트로피 기울기만큼 그쪽으로 당긴다(학습률 1.1 · 0.25 → 0.88). 학습 뒤에는 모델이 고른 후보 하나만 재서 검산한다. 숫자(층 · 깊이)는 기하가 내고 모델은 고르기만 한다 — 실제로는 부품 수천 개에 걸쳐, 그림을 보는 인코더(예: Gemma 비전 인코더) 위에서 배운다.",
  body: `<div class="iso-stage" tabindex="0" role="img" aria-label="학습 장치 · Enter 로 처음부터">${svg}</div>`,
});
const name = theme === "light" ? "learn115-light.html" : "learn115.html";
writeFileSync(join(HERE, name), k.pageHtml({ title: "코드 후보 고르기 학습", theme, body, script: kitScript() + live }));
console.log("wrote", name);
