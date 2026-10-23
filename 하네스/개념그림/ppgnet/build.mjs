// PPGNet (Zhang · Li · Lu · Gao, CVPR 2019) 핵심 동작 — 꼭짓점 핀보드 + 6×6 토글 스위치 행렬(인접 행렬) + 정답 카드 + 단계 번호판
// 움직이는 것: 핀(꼭짓점)이 솟고, 핀 두 개마다 수레가 실을 따라 64 점을 읽은 뒤, 행렬의 (i,j)·(j,i) 스위치가 함께 젖혀진다 = 모델이 「이 쌍은 선으로 이어졌다(1)」고 답함.
//   그때마다 정답 카드의 같은 쌍이 깜빡이고 판정 램프가 맞음(초록) / 틀림(빨강)을 보인다. 마지막(④)에 모델 연결표를 정답에 겹쳐 맞힌 수 / 틀린 수.
// 논문에서 확인한 사실 (https://ar5iv.labs.arxiv.org/html/1905.03415 · 2026-10-23 읽음):
//   §3.1   선 = 꼭짓점 그래프(노드 + 인접 행렬). 같은 끝점을 나누는 선분은 인접 행렬에 1 만 더할 뿐 → 긴 선과 그 안의 짧은 선을 함께 표현
//   §3.2.1 백본: dilated ResNet-50 + 피라미드 풀링 디코더 → 256 채널 · H/4 × W/4 특징
//   §3.2.2 꼭짓점 검출(JDM): 꼭짓점 열지도 → 국소 최대 + 군집 NMS(ε = 3 px) · 문턱 τ = 0.25(§4.3 · 그림 4 설정)
//   §3.2.3 선분 정렬(LSAM): 꼭짓점 쌍마다 등간격 64 점(L = 64) 쌍선형 보간 → C × 64
//   §3.2.4 인접 행렬 추론(AMIM): 쌍마다 연결 확률 → K × K 행렬 · 꼭짓점은 최대 512 개 · 64×64 블록씩 · O(n²) · 512 개에 약 0.9 s(Tesla P40)
//   §3.2.5 손실: 열지도와 인접 행렬 모두 이진 교차 엔트로피(λ = 1) — 정답 = 사람이 그린 선의 꼭짓점 · 연결표
// 함께 읽은 것: claudedocs/research_선검출모델_20261023.md (그래프 출력 계열: L-CNN · PPGNet · GAT-CADNet)
// 지어낸 것(설명용): 도면 꼭짓점 6 · 쌍 15 · 정답 연결 8. 모델 답에 일부러 틀림 2 (없는 선 2–6 을 이음 · 있는 선 5–6 을 놓침)
// 사용: node build.mjs [--light] → ppgnet.html / ppgnet-light.html
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

const PLATE = { x: -116, y: -86, w: 236, d: 202, r: 8 };
const PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -106, y: -70, w: 92, d: 140, r: 2 };
const SHEET_T = 0.8;
const PIN_H = 13, PIN_R = 2.6;
// 도면: 뒤쪽 한 직선 위 꼭짓점 1 · 2 · 3 (2 = T 자 교차) + 앞쪽 4 · 5 · 6   (코드 안 번호는 0 부터)
const J = [[-92, 50], [-92, 0], [-92, -50], [-48, 50], [-48, 0], [-28, -42]];
const TRUE = [[0, 1], [1, 2], [0, 2], [0, 3], [3, 4], [1, 4], [4, 5], [2, 5]];
const PAIRS = []; for (let a = 0; a < J.length; a++) for (let b = a + 1; b < J.length; b++) PAIRS.push([a, b]);
const has = (list, a, b) => list.some(([p, q]) => (p === a && q === b) || (p === b && q === a));
const PRED = [...TRUE.filter(([a, b]) => !(a === 4 && b === 5)), [1, 5]];   // 모델 답(설명용): 4–5 놓침 · 1–5 헛연결
const SAMPLES = 64;   // §3.2.3 L = 64
// 스위치 행렬: 칸 (i, j) = [MX + i·PITCH, MY − j·PITCH]
const N = J.length, PITCH = 13, MX = 14, MY = 32;
const PANEL = { x: MX - 21, y: MY - (N - 1) * PITCH - 10, w: (N - 1) * PITCH + 33, d: (N - 1) * PITCH + 31, r: 4 };
const PANEL_H = 7, PT = PANEL_H;
const cell = (i, j) => [MX + i * PITCH, MY - j * PITCH];
const ROW_LED = (i) => [MX + i * PITCH, MY + 13];
const COL_LED = (j) => [MX - 13, MY - j * PITCH];
const DIAL = [100, 78];
const CARD = { x: -6, y: 60, w: 42, d: 54, r: 2 }, CARD_T = 1.4;
const mini = ([x, y]) => [16 + (x + 60) * 0.4, 90 + y * 0.4];   // 도면 → 정답 카드 축소
const VERDICT = [31, 64];
const STEPS = { x: 40, y: 100, w: 62, d: 11, r: 2 }, STEP_LAMP = (s) => [47 + s * 14.5, 105.5];

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...J.map(([x, y]) => [x, y, PIN_H + 4]), ...k.boxCorners(PANEL, 0, PT + 8)], WIDTH, HEIGHT, { pad: 30, azimuth: 40 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const T = ([x, y], z, text, style) => k.faceTextSvg(k.topMatrix([x, y], z, P), text, style);
const depth = ([x, y]) => k.depthOf([x, y, 0], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth(a) - depth(b));
const disc = (x, y, r, z, cls) => `<path class="${cls}" d="${k.ring(x, y, r, z, P, 28)}"/>`;

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
  // 앞쪽 자(종이 가장자리 따라) — 눈금은 자 가장자리에서
  const strip = { x: SHEET.x + 4, y: SHEET.y + SHEET.d + 3, w: SHEET.w - 8, d: 7, r: 1 };
  o.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + 0.8, 0.6, [2, 3.6], P, "x");
  if (t && t.minor) o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  return o.join("");
}
function sheet() {   // 종이 + 도면(입력 그림) + 꼭짓점 번호 + 열지도 고리
  const o = [S(k.slabOf(SHEET, 0, SHEET_T, P, 4), { tone: "hi", crease: "lo" })];
  o.push(L(k.planOutline(k.insetPlan(SHEET, 3), SHEET_T, P), { tone: "faint" }));
  o.push(D(k.corners(SHEET, 4).map(([x, y]) => at([x, y, SHEET_T])), { size: 0.45 }));
  o.push(`<g style="stroke-width:1.3">${L(TRUE.map(([a, b]) => k.lineOnTop(J[a], J[b], SHEET_T, P)).join(""), { tone: "hi" })}</g>`);
  o.push(`<g data-part="heat" style="opacity:0">${J.map(([x, y]) => L([9, 6, 3.6].map((r) => k.ring(x, y, r, SHEET_T, P, 32)).join(""), { tone: "lo" })).join("")}</g>`);
  J.forEach(([x, y], i) => o.push(T([x + 7, y + 7], SHEET_T, String(i + 1), { size: 7, tone: "hi" })));
  return o.join("");
}
function answerCard() {   // 정답 카드: 사람이 그린 정답 연결 8 개 · 쌍마다 깜빡일 덧선 · 판정 램프
  const o = [S(k.slabOf(CARD, 0, CARD_T, P, 4, 0.3), { tone: "hi", crease: "lo" })];
  const z = CARD_T;
  o.push(L(k.planOutline(k.insetPlan(CARD, 2.4), z, P), { tone: "faint" }));
  o.push(D(k.corners(CARD, 1.8).map(([x, y]) => at([x, y, z])), { size: 0.45 }));
  o.push(T([6, 66.5], z, "정답", { size: 5, tone: "hi" }));
  o.push(`<g style="stroke-width:1.1">${L(TRUE.map(([a, b]) => k.lineOnTop(mini(J[a]), mini(J[b]), z, P)).join(""), { tone: "mid" })}</g>`);
  o.push(`<g data-part="cardpairs">${PAIRS.map(([a, b], i) => `<path data-cp="${i}" class="iso-line cp" d="${k.lineOnTop(mini(J[a]), mini(J[b]), z, P)}"/>`).join("")}</g>`);
  o.push(D(J.map((p) => at([...mini(p), z])), { size: 1.1, tone: "hi" }));
  const [vx, vy] = VERDICT;
  o.push(S(k.cylinder(vx, vy, 3, z, 0.8, P, 24, 0.2), { tone: "lo" }));
  o.push(`<g data-verdict="off">${disc(vx, vy, 2, z + 0.8, "vd")}</g>`);
  return o.join("");
}
function steps() {   // 단계 번호판 ①②③④ — 지금 단계 램프가 켜짐
  const o = [S(k.slabOf(STEPS, 0, 2, P, 4, 0.4), { tone: "mid" })];
  o.push(D([at([STEPS.x + 2.4, STEPS.y + STEPS.d / 2, 2]), at([STEPS.x + STEPS.w - 2.4, STEPS.y + STEPS.d / 2, 2])], { size: 0.45 }));
  for (let s = 0; s < 4; s++) {
    const [x, y] = STEP_LAMP(s);
    o.push(S(k.cylinder(x, y, 2.6, 2, 0.8, P, 24), { tone: "lo" }));
    const lamp = (lit) => S(k.cylinder(x, y, 1.8, 2.8, 1.2, P, 20, 0.2), { tone: lit ? "hi" : "mid", lit });
    o.push(`<g data-step="${s}" data-state="off">${lamp(false)}<g class="on">${lamp(true)}</g></g>`);
    o.push(T([x + 4, y + 3.4], 2, String(s + 1), { size: 6, tone: "hi" }));
  }
  return o.join("");
}
function dial() {   // 꼭짓점 문턱 τ 다이얼 — 바늘은 0.25
  const [cx, cy] = DIAL, from = -Math.PI * 0.75, span = Math.PI * 1.5, a = from + 0.25 * span;
  const o = [S(k.cylinder(cx, cy, 10, 0, 1.2, P, 48, 0.3), { tone: "lo" })];
  const t = k.radialTicks(cx, cy, 9.4, 20, 5, 1.2, [1.2, 2.4], P, from, span);
  o.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  o.push(S(k.cylinder(cx, cy, 5, 1.2, 4, P, 36, 0.4), { tone: "mid" }));
  o.push(L(k.knurl(cx, cy, 5, 1.2, 5.2, 40, P), { tone: "lo" }));
  o.push(L(k.lineOnTop([cx, cy], [cx + Math.sin(a) * 5, cy - Math.cos(a) * 5], 5.2, P), { tone: "hi" }));
  o.push(D([at([cx, cy, 5.2])], { size: 0.55, tone: "hi" }));
  return o.join("");
}
function panel() {   // 스위치 행렬 상자: 행 램프 · 열 램프 · 6×6 토글
  const o = [S(k.slabOf(PANEL, 0, PANEL_H, P, 6, 0.8), { tone: "mid" })];
  o.push(L(k.planOutline(k.insetPlan(PANEL, 3), PT, P), { tone: "faint" }));
  o.push(D(k.corners(PANEL, 2.2).map(([x, y]) => at([x, y, PT])), { size: 0.5 }));
  const grid = { x: MX - 6, y: MY - (N - 1) * PITCH - 6, w: (N - 1) * PITCH + 12, d: (N - 1) * PITCH + 12, r: 1.5 };
  o.push(L(k.planOutline(grid, PT, P), { tone: "lo" }));
  const items = [];
  for (let i = 0; i < N; i++) for (const [kind, [x, y]] of [["r", ROW_LED(i)], ["c", COL_LED(i)]]) items.push([x, y, () => {
    const lamp = (lit) => S(k.cylinder(x, y, 1.7, PT + 0.9, 1.1, P, 20), { tone: lit ? "hi" : "mid", lit });
    return S(k.cylinder(x, y, 2.5, PT, 0.9, P, 24), { tone: "lo" }) + `<g data-led="${kind}${i}" data-state="off">${lamp(false)}<g class="on">${lamp(true)}</g></g>`;
  }]);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    const [x, y] = cell(i, j);
    items.push([x, y, () => {
      if (i === j) return S(k.cylinder(x, y, 2.6, PT, 0.6, P, 24), { tone: "lo" }) + L(k.lineOnTop([x - 1.4, y], [x + 1.4, y], PT + 0.6, P), { tone: "faint" });
      const g = [L(k.ring(x, y, 4.2, PT, P, 28), { tone: "faint" }), S(k.cylinder(x, y, 3, PT, 1.1, P, 24, 0.3), { tone: "lo" }), S(k.cylinder(x, y, 1.9, PT + 1.1, 0.9, P, 6), { tone: "mid" })];
      const lever = (dx, lit) => {
        const top = [x + dx, y, PT + 6.4];
        return `<g style="stroke-width:1.3">${L(k.segment([x, y, PT + 2], top, P), { tone: lit ? "hi" : "mid" })}</g>` +
          S(k.cylinder(top[0], top[1], 1.5, top[2] - 0.7, 1.8, P, 18, 0.3), { tone: lit ? "hi" : "mid", lit });
      };
      g.push(`<g data-sw="${i}-${j}" data-state="off"><g class="off">${lever(-2.8, false)}</g><g class="on">${lever(2.8, true)}</g></g>`);
      return g.join("");
    }]);
  }
  for (const [, , f] of byDepth(items)) o.push(f());
  return o.join("");
}
function threads() {   // 꼭짓점 쌍마다 실(핀 머리에서 머리로)
  return PAIRS.map(([a, b], i) => `<path data-thread="${i}" class="iso-line" data-tone="lo" style="opacity:0;stroke-width:.7" d="${k.segment([...J[a], PIN_H - 0.6], [...J[b], PIN_H - 0.6], P)}"/>`).join("");
}
function pins() {   // 꼭짓점 핀: 깃 · 기둥 · 머리 (깊이 순)
  return byDepth(J.map((p, i) => [...p, i])).map(([x, y, i]) => {
    const head = (lit) => S(k.cylinder(x, y, PIN_R, PIN_H - 2, 2.4, P, 24, 0.4), { tone: "hi", lit });
    const g = [S(k.cylinder(x, y, 3.8, SHEET_T, 1.2, P, 24, 0.3), { tone: "lo" }),
      S(k.cylinder(x, y, 1.3, SHEET_T + 1.2, PIN_H - 3.2, P, 16), { tone: "mid", crease: "none" }),
      `<g data-head="${i}" data-state="off">${head(false)}<g class="on">${head(true)}</g></g>`];
    return `<g data-pin="${i}" style="opacity:0">${g.join("")}</g>`;
  }).join("");
}
function shuttle() {   // 64 점 수레 (원점에 짓고 옮김)
  const g = [S(k.cylinder(0, 0, 3.2, PIN_H - 2.6, 1.4, P, 24), { tone: "mid" }), S(k.cylinder(0, 0, 2, PIN_H - 1.2, 2.6, P, 20, 0.3), { tone: "hi", lit: true })];
  return `<g data-part="shuttle" style="opacity:0">${g.join("")}</g>`;
}

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "PPGNet 핵심 동작을 핀보드와 스위치 행렬로 그린 그림. 도면 위 꼭짓점 자리에 핀이 솟고, 핀 두 개마다 수레가 실을 따라 64 점을 읽는다. 모델이 이어졌다고 답하면 옆 6×6 스위치 행렬에서 스위치 두 개가 젖혀지고, 정답 카드의 같은 쌍이 깜빡이며 맞음/틀림을 보인다.",
  body: [base(), sheet(), answerCard(), steps(), dial(), panel(), `<g data-part="threads">${threads()}</g>`, `<g data-part="samples"></g>`, pins(), shuttle()],
});

const live = `
const P = ${JSON.stringify(P)};
const J = ${JSON.stringify(J)}, PAIRS = ${JSON.stringify(PAIRS)};
const TRUE = ${JSON.stringify(PAIRS.map(([a, b]) => has(TRUE, a, b)))}, PRED = ${JSON.stringify(PAIRS.map(([a, b]) => has(PRED, a, b)))};
const PIN_H = ${PIN_H}, NS = ${SAMPLES}, NJ = J.length;
const stage = document.querySelector(".iso-stage"), svg = stage.querySelector("svg");
const q = (s) => svg.querySelector(s), qa = (s) => [...svg.querySelectorAll(s)];
const pins = qa("[data-pin]").sort((a, b) => a.dataset.pin - b.dataset.pin), heads = qa("[data-head]").sort((a, b) => a.dataset.head - b.dataset.head);
const threads = qa("[data-thread]"), cps = qa("[data-cp]"), stepEls = qa("[data-step]");
const sw = (i, j) => q('[data-sw="' + i + '-' + j + '"]'), led = (n) => q('[data-led="' + n + '"]');
const heat = q('[data-part="heat"]'), shuttle = q('[data-part="shuttle"]'), samples = q('[data-part="samples"]'), verdict = q("[data-verdict]");
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const T_HEAT = 1.8, T_PIN = 2.4, T_THREAD = 1.4, T_EACH = 0.9, T_END = 4.2;
const t0 = T_HEAT + T_PIN + T_THREAD, t1 = t0 + PAIRS.length * T_EACH, LOOP = t1 + T_END;
const DECIDE = 0.6;   // 쌍 검사 중 이 몫에서 모델이 답함
const set = (el, s) => { if (el && el.dataset.state !== s) el.dataset.state = s; };
const OK = "var(--anatomy-green)", BAD = "var(--anatomy-red)";
const say = (s) => { if (readout.textContent !== s) readout.textContent = s; };
function draw(t) {
  let found = 0, cur = -1, sCur = 0;
  const stageNo = t < T_HEAT ? 0 : t < T_HEAT + T_PIN ? 1 : t < t1 ? 2 : 3;
  stepEls.forEach((el, s) => set(el, s === stageNo ? "on" : "off"));
  heat.style.opacity = t < T_HEAT + T_PIN ? ease(t / T_HEAT) : Math.max(0.25, 1 - ease((t - T_HEAT - T_PIN) / 1));
  pins.forEach((g, i) => { const u = ease((t - T_HEAT - i * 0.32) / 0.5); g.style.opacity = u; g.setAttribute("transform", translateAlong(P, [0, 0, -6 * (1 - u)])); if (u > 0.5) found++; });
  const tu = ease((t - T_HEAT - T_PIN) / T_THREAD), end = t >= t1;
  let dots = "", hit = 0, fp = 0, fn = 0;
  threads.forEach((el, i) => {
    const s = (t - t0 - i * T_EACH) / T_EACH, [a, b] = PAIRS[i], decided = s >= DECIDE, right = PRED[i] === TRUE[i];
    if (s >= 1 || end) { if (right) hit++; else if (PRED[i]) fp++; else fn++; }
    // 실: 검사 전 흐림 · 검사 중 진함 · 답 1 이면 굵게 · ④ 에서 맞음 초록 / 틀림 빨강
    let op = tu * 0.45, tone = "lo", w = ".7", stroke = "", dash = "";
    if (s >= 0 && s < 1) { op = 1; tone = "hi"; }
    if (decided) { op = PRED[i] ? 1 : 0.1; tone = PRED[i] ? "lit" : "lo"; w = PRED[i] ? "1.2" : ".7"; }
    if (end) {
      const e = ease((t - t1) / 0.8);
      if (PRED[i] || TRUE[i]) { op = 1; w = "1.4"; stroke = right ? OK : BAD; dash = !PRED[i] ? "3 2" : ""; } else op = 0.1 * (1 - e);
    }
    el.style.opacity = op; el.dataset.tone = tone; el.style.strokeWidth = w; el.style.stroke = stroke; el.style.strokeDasharray = dash;
    const on = decided && PRED[i] ? "on" : "off";
    set(sw(a, b), on); set(sw(b, a), on);
    // 정답 카드: 답하는 순간 같은 쌍이 깜빡임 · ④ 에서 겹친 결과
    const cp = cps[i]; let cpOp = 0, cpStroke = "", cpDash = "";
    if (decided && s < 1) { const blink = 0.5 + 0.5 * Math.cos((s - DECIDE) * Math.PI * 10); cpOp = blink; cpStroke = right ? OK : BAD; cpDash = TRUE[i] ? "" : "2 1.5"; }
    if (end && (PRED[i] || TRUE[i])) { cpOp = 1; cpStroke = right ? OK : BAD; cpDash = PRED[i] && !TRUE[i] ? "2 1.5" : !PRED[i] ? "1 1.5" : ""; }
    cp.style.opacity = cpOp; cp.style.stroke = cpStroke; cp.style.strokeDasharray = cpDash;
    if (s >= 0 && s < 1) {
      cur = i; sCur = s;
      const A = [...J[a], PIN_H - 0.6], B = [...J[b], PIN_H - 0.6];
      const u = ease(Math.min(1, s / (DECIDE - 0.05))), p = [A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u, 0];
      shuttle.style.opacity = 1; shuttle.setAttribute("transform", translateAlong(P, p));
      const n = Math.floor(u * (NS - 1));
      for (let m = 0; m <= n; m++) { const w2 = m / (NS - 1); const sp = iso([A[0] + (B[0] - A[0]) * w2, A[1] + (B[1] - A[1]) * w2, A[2] + 0.3], P); dots += '<circle cx="' + sp[0].toFixed(2) + '" cy="' + sp[1].toFixed(2) + '" r=".5" class="iso-dot" data-tone="lit"/>'; }
    }
  });
  const [ca, cb] = cur >= 0 ? PAIRS[cur] : [-1, -1];
  for (let i = 0; i < NJ; i++) { set(heads[i], i === ca || i === cb ? "on" : "off"); set(led("r" + i), i === ca ? "on" : "off"); set(led("c" + i), i === cb ? "on" : "off"); }
  if (cur < 0) shuttle.style.opacity = 0;
  samples.innerHTML = dots;
  // 판정 램프
  let vd = "off";
  if (cur >= 0 && sCur >= DECIDE) vd = PRED[cur] === TRUE[cur] ? "ok" : "bad";
  if (end) vd = fp + fn ? "bad" : "ok";
  if (verdict.dataset.verdict !== vd) verdict.dataset.verdict = vd;
  // 판독 줄: 지금 무엇을 하는지 한 문장
  if (stageNo === 0) say("① 입력 그림에서 꼭짓점이 있을 만한 곳을 열지도로 찾는 중");
  else if (stageNo === 1) say("② 열지도가 0.25 를 넘는 곳에 꼭짓점 핀을 꽂는 중 · " + found + " / " + NJ);
  else if (cur < 0) say("③ 꼭짓점 6 개로 만들 수 있는 쌍 15 개를 하나씩 검사할 차례");
  else if (stageNo === 2) {
    const head = "③ 꼭짓점 " + (ca + 1) + ["과", "와", "과", "와", "와", "과"][ca] + " " + (cb + 1);
    if (sCur < DECIDE) say(head + " 사이 64 점을 읽어 이어졌는지 보는 중");
    else {
      const p = PRED[cur], g = TRUE[cur];
      say(head + " → 모델: " + (p ? "이어짐" : "안 이어짐") + " · 정답: " + (g ? "이어짐" : "안 이어짐") + " · " + (p === g ? "맞음" : "틀림"));
    }
  }
  if (end) say("④ 모델 답을 정답에 겹침 → 15 쌍 중 " + hit + " 맞음 · 틀림 " + (fp + fn) + " (없는 선 " + fp + " · 놓친 선 " + fn + ")");
}
let frame = 0, last = 0, clock = 0, visible = false, held = null;   // held: 녹화용 고정 시각(__ppg.hold)
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(held ?? clock); frame = visible ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__ppg = { LOOP, hold: (t) => { held = t; draw(t); } };
draw(still.matches ? LOOP - 0.5 : 0);
`;
const css = `<style>
[data-state] > .on{opacity:0;transition:opacity .25s}[data-state="on"] > .on{opacity:1}[data-sw] > .off{transition:opacity .25s}[data-sw][data-state="on"] > .off{opacity:0}
.cp{fill:none;stroke-width:1.6;opacity:0}
.vd{fill:var(--anatomy-paper);stroke:var(--anatomy-lo);stroke-width:.6;transition:fill .2s}
[data-verdict="ok"] .vd{fill:var(--anatomy-green)}[data-verdict="bad"] .vd{fill:var(--anatomy-red)}
.iso-plate-corner[data-corner="readout"]{max-width:78%;text-align:right}
</style>`;
const body = k.plateHtml({
  fig: "그림 2", title: "PPGNet · 꼭짓점 쌍 그래프",
  hint: "",
  readout: "① 꼭짓점 찾는 중",
  keys: [
    { mark: "lit", label: "핀 = 모델이 찾은 꼭짓점 (열지도 문턱 0.25 · 논문은 최대 512 개)" },
    { mark: "dotted", label: "수레 = 쌍마다 선 위 64 점을 읽음 (LSAM)" },
    { mark: "raised", label: "스위치 행렬 = 모델 답 K×K 인접 행렬 · (i,j) 와 (j,i) 가 함께 젖혀짐" },
    { mark: "flat", label: "정답 카드 = 사람이 그린 선 8 개 · 램프 초록 맞음 / 빨강 틀림" },
  ],
  caption: "이 모델은 선 그림(사진) 한 장을 받아, 꼭짓점이 어디 있고 어느 두 꼭짓점이 선으로 이어졌는지(꼭짓점 그래프)를 맞힌다. 정답은 사람이 그려 둔 선의 꼭짓점과 연결표다(§3.2.5, 열지도와 인접 행렬 모두 이진 교차 엔트로피). ① 백본(dilated ResNet-50)이 꼭짓점 열지도를 그리고 ② 문턱 0.25 를 넘는 곳을 꼭짓점으로 잡는다(§3.2.2). ③ 꼭짓점 쌍마다 선 위 64 점의 특징을 모아(§3.2.3) 이어졌는지를 K×K 인접 행렬로 답한다(§3.2.4). ④ 그 행렬을 정답과 겹쳐 맞힌 쌍을 센다. 같은 끝점을 나누는 선은 행렬에 1 을 더할 뿐이라, 한 직선 위 1–2–3 처럼 긴 선 1–3 과 안쪽 짧은 선 1–2 · 2–3 이 함께 1 이다(§3.1). 그림의 도면과 모델의 틀림 2 개(없는 선 2–6 · 놓친 선 5–6)는 설명을 위해 지어낸 예다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="PPGNet 동작 그림">${svg}</div>`,
});
const out = join(HERE, theme === "light" ? "ppgnet-light.html" : "ppgnet.html");
writeFileSync(out, k.pageHtml({ title: "PPGNet", theme, body, script: kitScript() + live }));
console.log("wrote", out);
