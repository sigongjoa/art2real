// L-CNN (Zhou · Qi · Ma, ICCV 2019) 핵심 동작 — 핀보드: 꼭짓점 제안(핀) → 꼭짓점 쌍 = 선 후보(실) → 선마다 32 점 훑어 맞다/틀리다(LoI 풀링) → 램프
// 근거: claudedocs/research_선검출모델_20261023.md (K=300 꼭짓점 · 32 점 샘플 · 1D max pool 8 · FC 1024) · 그림의 도면은 꼭짓점 6 · 선 후보 15 · 참 7
// 사용: node build.mjs [--light] → lcnn.html
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

const PLATE = { x: -120, y: -82, w: 240, d: 164, r: 8 };
const PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -54, y: -58, w: 150, d: 120, r: 2 };   // 도면이 깔린 종이(얇은 판)
const SHEET_T = 0.8;
const PIN_H = 12, PIN_R = 2.4;
// 도면: 집 모양(벽 · 지붕) + 꼬리 선 하나 — 꼭짓점 6 · 참 모서리 7
const J = [[-36, -35], [30, -35], [30, 15], [-36, 15], [-3, 45], [80, -35]];
const CARD = { x: -114, y: -50, w: 52, d: 56, r: 2 };   // 정답 카드(왼쪽): 이 도면의 진짜 선 7 개
const CARD_C = [CARD.x + CARD.w / 2, CARD.y + CARD.d / 2 + 2], CARD_S = 0.4;
const 카드점 = (p) => [CARD_C[0] + (p[0] - 22) * CARD_S, CARD_C[1] + (p[1] - 5) * CARD_S];
const STEPS = [[-106, 22], [-89, 22], [-72, 22]];   // 단계 번호판 ① ② ③
const TRUE = [[0, 1], [1, 2], [2, 3], [3, 0], [3, 4], [2, 4], [1, 5]];
const PAIRS = []; for (let a = 0; a < J.length; a++) for (let b = a + 1; b < J.length; b++) PAIRS.push([a, b]);
const isTrue = (a, b) => TRUE.some(([p, q]) => (p === a && q === b) || (p === b && q === a));
const SAMPLES = 32;
const LAMP_Y = PLATE.y + PLATE.d - 11;   // 앞줄(뷰어 쪽 = y 큰 쪽) 램프 레일
const LAMPS = PAIRS.map((_, i) => [-84 + i * 11.4, LAMP_Y]);

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...J.map(([x, y]) => [x, y, PIN_H + 4])], WIDTH, HEIGHT, { pad: 34, azimuth: 40 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const byDepth = (pts) => [...pts].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));

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
  // 오른쪽 자(가로) — 눈금은 자 가장자리에서
  const strip = { x: PLATE.x + PLATE.w - 18, y: -60, w: 8, d: 122, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.y + 4, strip.y + strip.d - 4, 4, 5, strip.x + 0.8, 0.6, [2, 3.6], P, "y");
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  // 이름판(뒤 왼쪽) — 세 줄은 인쇄 글자
  const plate = { x: PLATE.x + 12, y: PLATE.y + 8, w: 40, d: 11, r: 1.2 };
  o.push(S(k.slabOf(plate, 0, 0.8, P, 4), { tone: "lo" }));
  o.push(L(k.planOutline(k.insetPlan(plate, 1.6), 0.8, P), { tone: "faint" }));
  [[5, 30], [5, 22], [5, 26]].forEach(([dx, len], i) => o.push(L(k.lineOnTop([plate.x + dx, plate.y + 3 + i * 2.6], [plate.x + dx + len, plate.y + 3 + i * 2.6], 0.8, P), { tone: "lo", free: true })));
  o.push(D([at([plate.x + 2.4, plate.y + plate.d / 2, 0.8]), at([plate.x + plate.w - 2.4, plate.y + plate.d / 2, 0.8])], { size: 0.45 }));
  return o.join("");
}
function sheet() {   // 종이 + 도면(입력 그림) + 꼭짓점 열지도 고리
  const o = [S(k.slabOf(SHEET, 0, SHEET_T, P, 4), { tone: "hi", crease: "lo" })];
  o.push(L(k.planOutline(k.insetPlan(SHEET, 3), SHEET_T, P), { tone: "faint" }));
  o.push(D(k.corners(SHEET, 4).map(([x, y]) => at([x, y, SHEET_T])), { size: 0.45 }));
  o.push(`<g style="stroke-width:1.6">${L(TRUE.map(([a, b]) => k.lineOnTop(J[a], J[b], SHEET_T, P)).join(""), { tone: "hi" })}</g>`);   // 입력 도면 선(굵게)
  J.forEach(([x, y]) => o.push(L([7, 4.6].map((r) => k.ring(x, y, r, SHEET_T, P, 28)).join(""), { tone: "faint" })));
  return o.join("");
}
function answerCard() {   // 정답 카드: 받침 + 카드 + 진짜 선 7 개(채택될 때마다 그 선이 켜짐) + 꼭짓점 점
  const o = [S(k.slabOf(k.insetPlan(CARD, -2), 0, 1.2, P, 4, 0.4), { tone: "lo" }), S(k.slabOf(CARD, 1.2, 1, P, 4, 0.3), { tone: "hi", crease: "lo" })];
  o.push(L(k.planOutline(k.insetPlan(CARD, 3), 2.2, P), { tone: "faint" }));
  o.push(D(k.corners(CARD, 3.5).map(([x, y]) => at([x, y, 2.2])), { size: 0.45 }));
  o.push(`<g style="stroke-width:1.2">${L(TRUE.map(([a, b]) => k.lineOnTop(카드점(J[a]), 카드점(J[b]), 2.2, P)).join(""), { tone: "mid" })}</g>`);
  TRUE.forEach(([a, b], i) => o.push(`<path data-ans="${a}-${b}" class="iso-line" data-tone="lit" style="opacity:0;stroke-width:1.6" d="${k.lineOnTop(카드점(J[a]), 카드점(J[b]), 2.25, P)}"/>`));
  o.push(D(J.map((p) => at([...카드점(p), 2.2])), { size: 0.7, tone: "mid" }));
  o.push(k.faceTextSvg(k.topMatrix([CARD.x + CARD.w / 2, CARD.y + 6], 2.2, P, "x"), "정답", { size: 4, tone: "mid", anchor: "middle" }));
  return o.join("");
}
function stepPlates() {   // 단계 번호판: 지금 단계만 켜짐
  return STEPS.map(([x, y], i) => {
    const pl = { x: x - 7, y: y - 6, w: 14, d: 12, r: 1.5 };
    return S(k.slabOf(pl, 0, 1.6, P, 4, 0.4), { tone: "lo" }) + `<g data-step="${i}" data-state="off">${S(k.slabOf(k.insetPlan(pl, 1.4), 1.6, 1, P, 4, 0.3), { tone: "mid" })}<g class="lamp-on">${S(k.slabOf(k.insetPlan(pl, 1.4), 1.6, 1, P, 4, 0.3), { tone: "hi", lit: true })}</g>${k.faceTextSvg(k.topMatrix([x, y + 2.4], 2.6, P, "x"), String(i + 1), { size: 6, tone: "lo", anchor: "middle" })}</g>`;
  }).join("");
}
function lampRail() {   // 앞줄: 선 후보마다 램프 하나(채택 = 켜짐)
  const rail = { x: -92, y: LAMP_Y - 4, w: 172, d: 8, r: 2 };
  const o = [S(k.slabOf(rail, 0, 3, P, 4, 0.5), { tone: "mid" })];
  o.push(D([at([rail.x + 3, LAMP_Y, 3]), at([rail.x + rail.w - 3, LAMP_Y, 3])], { size: 0.45 }));
  LAMPS.forEach(([x, y], i) => {
    o.push(S(k.cylinder(x, y, 3.4, 3, 1.4, P, 20), { tone: "lo" }));
    o.push(`<g data-lamp="${i}" data-state="off">${S(k.cylinder(x, y, 2.4, 4.4, 1.6, P, 20), { tone: "mid" })}<g class="lamp-on">${S(k.cylinder(x, y, 2.4, 4.4, 1.6, P, 20), { tone: "hi", lit: true })}</g><g class="lamp-no">${L(k.lineOnTop([x - 1.4, y], [x + 1.4, y], 6, P), { tone: "lo" })}</g></g>`);
  });
  return o.join("");
}
function pins() {   // 꼭짓점 핀: 깃 · 기둥 · 머리 (깊이 순)
  return byDepth(J.map((p, i) => [...p, i])).map(([x, y, i]) => {
    const g = [S(k.cylinder(x, y, 3.6, SHEET_T, 1.2, P, 24), { tone: "lo" }),
      S(k.cylinder(x, y, 1.3, SHEET_T + 1.2, PIN_H - 3.2, P, 16), { tone: "mid", crease: "none" }),
      S(k.cylinder(x, y, PIN_R, PIN_H - 2, 2.2, P, 24, 0.4), { tone: "hi", lit: true })];
    return `<g data-pin="${i}" style="opacity:0">${g.join("")}</g>`;
  }).join("");
}
function threads() {   // 선 후보 = 꼭짓점 쌍마다 실 하나(핀 머리에서 머리로)
  return PAIRS.map(([a, b], i) => `<path data-thread="${i}" class="iso-line" data-tone="lo" style="opacity:0;stroke-width:.7" d="${k.segment([...J[a], PIN_H - 0.6], [...J[b], PIN_H - 0.6], P)}"/>`).join("");
}
function shuttle() {   // 검사 수레: 실을 따라 미끄러지며 32 점을 읽음 (원점에 짓고 옮김)
  const g = [S(k.cylinder(0, 0, 3.2, PIN_H - 2.6, 1.4, P, 24), { tone: "mid" }), S(k.cylinder(0, 0, 2, PIN_H - 1.2, 2.6, P, 20, 0.3), { tone: "hi", lit: true })];
  return `<g data-part="shuttle" style="opacity:0">${g.join("")}</g>`;
}

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "L-CNN 핵심 동작을 핀보드로 그린 그림. 도면 위 꼭짓점 자리에 핀이 솟고, 핀 두 개마다 실(선 후보)이 걸린다. 검사 수레가 실을 따라 32 점을 읽고 맞는 선이면 앞줄 램프를 켠다.",
  body: [base(), answerCard(), stepPlates(), sheet(), lampRail(), `<g data-part="threads">${threads()}</g>`, `<g data-part="samples"></g>`, pins(), shuttle()],
});

const live = `
const P = ${JSON.stringify(P)};
const J = ${JSON.stringify(J)}, PAIRS = ${JSON.stringify(PAIRS)}, TRUE = ${JSON.stringify(PAIRS.map(([a, b]) => isTrue(a, b)))};
const PIN_H = ${PIN_H}, N = ${SAMPLES};
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const pins = [...svg.querySelectorAll("[data-pin]")].sort((a, b) => a.dataset.pin - b.dataset.pin);
const threads = [...svg.querySelectorAll("[data-thread]")], lamps = [...svg.querySelectorAll("[data-lamp]")];
const shuttle = svg.querySelector('[data-part="shuttle"]'), samples = svg.querySelector('[data-part="samples"]');
const steps = [...svg.querySelectorAll("[data-step]")], answers = [...svg.querySelectorAll("[data-ans]")];
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const T_PIN = 2.4, T_THREAD = 1.6, T_EACH = 0.9, T_END = 2.2, LOOP = T_PIN + T_THREAD + PAIRS.length * T_EACH + T_END;
const scr = (p) => iso(p, P);
function draw(t) {
  let found = 0, done = 0, kept = 0;
  pins.forEach((g, i) => { const u = ease((t - i * 0.32) / 0.5); g.style.opacity = u; g.setAttribute("transform", translateAlong(P, [0, 0, -6 * (1 - u)])); if (u > 0.5) found++; });
  const tu = ease((t - T_PIN) / T_THREAD), t0 = T_PIN + T_THREAD;
  let dots = "";
  threads.forEach((el, i) => {
    const s = (t - t0 - i * T_EACH) / T_EACH;
    if (s >= 1) { done++; if (TRUE[i]) kept++; }
    el.style.opacity = s >= 1 ? (TRUE[i] ? 1 : 0.1) : tu * 0.85;
    el.dataset.tone = s >= 1 && TRUE[i] ? "lit" : s >= 0 && s < 1 ? "hi" : "mid";
    el.style.strokeWidth = s >= 1 && TRUE[i] ? "1.5" : s >= 0 && s < 1 ? "1.1" : ".8";
    const lamp = lamps[i]; lamp.dataset.state = s >= 1 ? (TRUE[i] ? "on" : "no") : "off";
    if (s >= 0 && s < 1) {
      const [a, b] = PAIRS[i], A = [...J[a], PIN_H - 0.6], B = [...J[b], PIN_H - 0.6];
      const u = ease(Math.min(1, s / 0.8)); const p = [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, 0];
      shuttle.style.opacity = 1; shuttle.setAttribute("transform", translateAlong(P, p));
      const n = Math.floor(u * N);
      for (let q = 0; q <= n && q < N; q++) { const w = q / (N - 1); const sp = scr([A[0] + (B[0] - A[0]) * w, A[1] + (B[1] - A[1]) * w, A[2] + 0.3]); dots += '<circle cx="' + sp[0].toFixed(2) + '" cy="' + sp[1].toFixed(2) + '" r="1.05" class="iso-dot" data-tone="lit"/>'; }
    }
  });
  if (t < t0 || t > t0 + PAIRS.length * T_EACH) shuttle.style.opacity = 0;
  samples.innerHTML = dots;
  const 단계 = t < T_PIN ? 0 : t < t0 ? 1 : 2;
  steps.forEach((g, i) => g.dataset.state = i === 단계 ? "on" : "off");
  // 정답 카드: 채택된 선은 카드의 같은 선이 켜진 채 남음 · 지금 읽는 후보가 정답에 있으면 깜빡임
  answers.forEach((el) => { const [a, b] = el.dataset.ans.split("-").map(Number); const i = PAIRS.findIndex(([p, q]) => p === a && q === b); const s = (t - t0 - i * T_EACH) / T_EACH; el.style.opacity = s >= 1 ? 1 : s >= 0 ? 0.35 + 0.35 * Math.sin(s * 18) ** 2 : 0; });
  if (t < T_PIN) readout.textContent = "① 도면에서 꼭짓점을 찾는다 · " + found + " / " + J.length;
  else if (t < t0) readout.textContent = "② 꼭짓점 두 개씩 이어 선 후보 " + PAIRS.length + " 개를 만든다";
  else if (t > t0 + PAIRS.length * T_EACH) readout.textContent = "끝 · 정답 선 " + TRUE.filter(Boolean).length + " 개 중 " + kept + " 개 찾음 · 헛선 0";
  else { const i = Math.min(PAIRS.length - 1, Math.floor((t - t0) / T_EACH)); readout.textContent = "③ 후보 " + (i + 1) + " / " + PAIRS.length + " 을 32 점 읽는 중 → " + (TRUE[i] ? "정답에 있는 선 · 채택" : "정답에 없는 선 · 기각"); }
}
let frame = 0, last = 0, clock = 0, visible = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
draw(still.matches ? LOOP - 0.5 : 0);
`;
const css = `<style>[data-lamp] .lamp-on,[data-lamp] .lamp-no,[data-step] .lamp-on{opacity:0;transition:opacity .25s}[data-lamp][data-state="on"] .lamp-on,[data-step][data-state="on"] .lamp-on{opacity:1}[data-lamp][data-state="no"] .lamp-no{opacity:1}</style>`;
const body = k.plateHtml({
  fig: "그림 1", title: "L-CNN · 선 단위 검증",
  hint: "저절로 돈다 · 한 바퀴 약 20 초",
  readout: "① 도면에서 꼭짓점을 찾는다",
  keys: [{ mark: "raised", label: "왼쪽 정답 카드 = 이 도면의 진짜 선 7 개 · 모델이 맞히면 그 선이 켜짐" }, { mark: "lit", label: "핀 = 꼭짓점 후보 (논문은 열지도에서 상위 300 개)" }, { mark: "flat", label: "실 = 꼭짓점 두 개를 잇는 선 후보 · 수레가 32 점을 읽고 채택 / 기각 · 단계판 ① ② ③" }],
  caption: "이 모델은 선 그림(사진)을 받아 「선분 목록」을 맞힌다. 정답은 왼쪽 카드의 선 7 개다. L-CNN(ICCV 2019)은 화소마다 라벨을 붙이지 않는다. 꼭짓점을 먼저 찾고, 꼭짓점 쌍마다 선 후보를 세운 뒤, 선 하나하나를 따로 맞다/틀리다로 판정한다(LoI 풀링: 선 위 32 점 → 1D 최대 풀링 8 → 완전연결 1024). 그래서 두 선이 같은 화소를 지나도 서로 다른 후보로 따로 판정된다. 단, 직선 선분만 다룬다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="L-CNN 동작 그림">${svg}</div>`,
});
const out = join(HERE, theme === "light" ? "lcnn-light.html" : "lcnn.html");
writeFileSync(out, k.pageHtml({ title: "L-CNN", theme, body, script: kitScript() + live }));
console.log("wrote", out);
