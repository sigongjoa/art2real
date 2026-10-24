// 판 145 · 146 「코드 생성」 — 3 면도 → CadQuery 코드. 한 비교판의 두 참가자, 같은 언어 모델.
// 근거(이 그림이 쓰는 사실만 · 하네스/과제코드.py · conf/판_145선글코드.yaml · 판_146도면코드.yaml):
//   입력: 부품 하나의 3 면도(위 · 앞 · 옆, 각 128 px). 디코더는 둘 다 cadrille(2B 언어 모델 Qwen2 · CadQuery 를 이미 앎) + LoRA 미세조정.
//   146 「ViT 그대로」: 도면 그림(2×2 · 위 앞 / 옆 빈칸)을 칸(패치)으로 잘라 Qwen2-VL ViT 가 이미지 토큰 ~256 개로 → 언어 모델
//   145 「선 토큰」: 판 137 CNN 이 화소마다 선을 칠함 → 벡터화가 꼭짓점에서 끊음 → 선 하나 = 글 한 줄
//        「뷰 종류 x0 y0 x1 y1 [원호면 가운데 x y] [숨은선이면 h]」 (T=위 F=앞 S=옆 · L=직선 A=원호) → 언어 모델
//   언어 모델이 코드를 한 줄씩 쓴다 → 실행 → 3D 부품 → 정답 부품과 실루엣 IoU.
//   아직 돌지 않았다 — 결과 숫자는 그리지 않는다. 부품 · 코드 · 선 글은 설명용 예시(생성 코드의 보스 높이 12 대 정답 10 은 IoU 를 보이려 넣은 차이).
// 그림 요소: 입력 도면 받침 · 왼쪽 급지기(격자 도장 프레스 → 칸 토큰이 홈통으로) · 오른쪽 급지기(선 따라가는 펜 → 테이프 인쇄기)
//           · 가운데 한 대의 타자기(언어 모델 · LoRA 카트리지 · 146/145 선택 손잡이) · 출력 용지(코드) · 회전대(실행한 부품)
//           · 실루엣 판 · 정답 카드(정답 부품 + 코드) · 번호판 ①~⑥
// 사용: node build.mjs [--light] [--record]
//   → out/설명/anatomy/code145/code145[-light].html · --record 는 light 판을 8 fps × 2 배로 찍어 이 폴더에 .mp4 · .gif
import { mkdirSync, writeFileSync, readdirSync, unlinkSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "file:///C:/Users/zesky/.claude/skills/anatomy/kit/iso-kit.mjs";
import { kitScript } from "file:///C:/Users/zesky/.claude/skills/anatomy/scripts/inline-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, "../../../out/설명/anatomy/code145");
const RECORD = process.argv.includes("--record");
const theme = RECORD || process.argv.includes("--light") ? "light" : "dark";
const WIDTH = 640, HEIGHT = 400;

// ── 도면(128 px · 2 px/mm) — 정답 부품: 바닥 34.1×47.4×9 · Ø8 관통 구멍 · 보스 14×18×10 (뒤쪽 끝에 붙음) ──
const VIEWS = [   // [뷰 글자, 판 자리(2×2: 위 앞 / 옆 빈칸), 선들 [x0,y0,x1,y1, 숨음?] · 원호 {a,b,m}]
  ["T", [0, 0], [[30, 17, 98, 17], [30, 17, 30, 111], [98, 17, 98, 111], [30, 111, 98, 111], [50, 53, 78, 53], [50, 17, 50, 53], [78, 17, 78, 53],
    { a: [56, 64], b: [72, 64], m: [64, 56] }, { a: [72, 64], b: [56, 64], m: [64, 72] }]],
  ["F", [1, 0], [[30, 96, 98, 96], [30, 78, 30, 96], [98, 78, 98, 96], [30, 78, 50, 78], [78, 78, 98, 78], [50, 58, 50, 78], [78, 58, 78, 78], [50, 58, 78, 58], [56, 78, 56, 96, 1], [72, 78, 72, 96, 1]]],
  ["S", [0, 1], [[17, 96, 111, 96], [17, 58, 17, 96], [111, 78, 111, 96], [53, 78, 111, 78], [53, 58, 53, 78], [17, 58, 53, 58], [56, 78, 56, 96, 1], [72, 78, 72, 96, 1]]],
];
const LINES = [];   // 펼친 선 목록 = 선 글 순서
for (const [v, slot, ls] of VIEWS) for (const l of ls) {
  if (Array.isArray(l)) LINES.push({ v, slot, a: [l[0], l[1]], b: [l[2], l[3]], hid: !!l[4], tok: `${v} L ${l.slice(0, 4).join(" ")}${l[4] ? " h" : ""}` });
  else LINES.push({ v, slot, a: l.a, b: l.b, m: l.m, tok: `${v} A ${l.a.join(" ")} ${l.b.join(" ")} ${l.m.join(" ")}` });
}
if (LINES.length !== 27) throw new Error("선 수가 바뀌었다: " + LINES.length);
const CODE = ['b0 = cq.Workplane("XY")', '.box(34.1, 47.4, 9.0)', '.faces(">Z").workplane()', ".hole(8.0)", 'b1 = cq.Workplane("XY")', ".box(14.0, 18.0, 12.0)", ".translate((0, -14.7, 10.5))", "result = b0.union(b1)"];
const TRUE = CODE.map((c) => c.replace("12.0)", "10.0)").replace("10.5))", "9.5))"));
const INDENT = [0, 1, 1, 1, 0, 1, 1, 0];
if (TRUE.filter((c, i) => c !== CODE[i]).length !== 2) throw new Error("정답 코드와 생성 코드는 두 줄만 달라야 한다");

// ── 배치(세계 좌표: x 오른쪽 · y 앞쪽 · z 위) ───────────────────
const PLATE = { x: -180, y: -142, w: 392, d: 302, r: 10 }, PLATE_H = 10, FOOT_H = 5;
const SHEET = { x: -86, y: -122, w: 46, d: 46, r: 0.6 }, SZ = 3;   // 입력 도면(종이 위 z = SZ)
const SLIDE = 70;                                                  // 복사본이 급지기로 옮겨 가는 거리
const BED_L = { ...SHEET, x: SHEET.x - SLIDE }, BED_R = { ...SHEET, x: SHEET.x + SLIDE };
const PS = 21 / 128, PANEL = (slot) => [1.5 + slot[0] * 22, 1.5 + slot[1] * 22];
const MACH = { x: -162, y: 8, w: 218, d: 56, r: 3 }, MH = 14;
const CHUTE = { x: BED_L.x + BED_L.w / 2 - 11, y: BED_L.y + BED_L.d, w: 22, d: MACH.y - BED_L.y - BED_L.d - 6, r: 0.6 };
const PRN = { x: -37, y: -70, w: 88, d: 14, r: 2 }, PRN_H = 12;
const TAPE = { x: -33, w: 80 }, TAPE_Y0 = PRN.y + PRN.d, ROWT = 7.6;
const PAPER = { x: -156, y: 72, w: 136, d: 80, r: 0.6 }, ROWC = 9.2;
const TT = { c: [96, -38], r: 34 };                                // 회전대
const SIL = { x: 142, y: -82, w: 64, d: 66, r: 2 };                // 실루엣 판
const CARD = { x: -4, y: 76, w: 150, d: 72, r: 1 }, HOLD = { x: -8, y: 72, w: 158, d: 80, r: 2 };
const KEYS = { x: 160, y: 74, w: 38, d: 56, r: 2 }, NKEY = 6;
const PARK = [28, -79], PEN_DY = 6, BY = PARK[1] - PEN_DY, BEAM_Z = 14;

const P = k.fitProjection([...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [-160, -133, 54], [-106, -133, 54], [-27, -124, 24]], WIDTH, HEIGHT, { pad: 22, azimuth: 60, elevation: 38 });
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const T = (x, y, z, text, size, tone = "mid", anchor = "start") => k.faceTextSvg(k.topMatrix([x, y], z, P, "x"), text, { size, tone, anchor });
const depth = (x, y, z = 0) => k.depthOf([x, y, z], P);
const byDepth = (pts) => [...pts].sort((a, b) => depth(a[0], a[1]) - depth(b[0], b[1]));
const box = (x0, y0, w, d, z, h, tone = "hi", r = 0.4) => S(k.slabOf({ x: x0, y: y0, w, d, r }, z, h, P, 2, 0.3), { tone, crease: "lo" });
const circ = (cx, cy, r, z, n = 32) => k.onTop(Array.from({ length: n }, (_, i) => [cx + r * Math.cos(i / n * 2 * Math.PI), cy + r * Math.sin(i / n * 2 * Math.PI)]), z, P, true);

// 종이 위 한 장의 3 면도: 선마다 path (펜이 켜는 쪽은 data-ln)
const px = (sheet, slot, [u, v]) => { const [ox, oy] = PANEL(slot); return [sheet.x + ox + u * PS, sheet.y + oy + v * PS]; };
const arcPts = (sheet, l) => {   // 세 점 원호(여기선 반원) — 중심 = a · b 가운데
  const c = [(l.a[0] + l.b[0]) / 2, (l.a[1] + l.b[1]) / 2], r = Math.hypot(l.a[0] - c[0], l.a[1] - c[1]);
  const t0 = Math.atan2(l.a[1] - c[1], l.a[0] - c[0]), tm = Math.atan2(l.m[1] - c[1], l.m[0] - c[0]);
  const dir = Math.sign(Math.sin(tm - t0)) || 1;
  return Array.from({ length: 17 }, (_, i) => px(sheet, l.slot, [c[0] + r * Math.cos(t0 + dir * Math.PI * i / 16), c[1] + r * Math.sin(t0 + dir * Math.PI * i / 16)]));
};
const linePts = (sheet, l) => l.m ? arcPts(sheet, l) : [px(sheet, l.slot, l.a), px(sheet, l.slot, l.b)];
function drawing(sheet, z, tag) {
  const o = [];
  const frames = [[0, 0], [1, 0], [0, 1]].map((s) => { const [ox, oy] = PANEL(s); return k.planOutline({ x: sheet.x + ox, y: sheet.y + oy, w: 21, d: 21, r: 0 }, z, P); });
  o.push(L(frames.join(""), { tone: "faint" }));
  LINES.forEach((l, j) => {
    const cls = `iso-line dr${l.m ? " dr-arc" : ""}${l.hid ? " dr-hid" : ""}`;
    o.push(`<path class="${cls}"${tag ? ` data-ln="${j}"` : ""} d="${k.onTop(linePts(sheet, l), z, P)}"/>`);
  });
  return o.join("");
}
function sheetSlab(sheet, z) { return S(k.slabOf(sheet, z - 0.6, 0.6, P, 3), { tone: "hi", crease: "lo", flat: true }); }

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
  return o.join("");
}
function input() {   // 입력 받침 + 도면 · 빈 칸에 이름
  const tray = { x: SHEET.x - 4, y: SHEET.y - 4, w: SHEET.w + 8, d: SHEET.d + 8, r: 1.6 };
  const o = [S(k.slabOf(tray, 0, SZ - 0.6, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(tray, 1.8).map(([x, y]) => at([x, y, SZ - 0.6])), { size: 0.4 }));
  o.push(sheetSlab(SHEET, SZ));
  o.push(`<g data-part="in-lines">${drawing(SHEET, SZ + 0.02, false)}</g>`);
  o.push(T(SHEET.x + 25, SHEET.y + 31, SZ, "3 면도", 5, "hi"), T(SHEET.x + 25, SHEET.y + 38, SZ, "128 px ×3", 3.8, "mid"));
  return o.join("");
}
function beds() {   // 두 급지기 바닥 · 오른쪽 펜 레일
  const o = [];
  for (const b of [BED_L, BED_R]) {
    const bp = { x: b.x - 3, y: b.y - 3, w: b.w + 6, d: b.d + 6, r: 1.4 };
    o.push(S(k.slabOf(bp, 0, SZ - 0.6, P, 4, 0.4), { tone: "lo" }));
    o.push(L(k.planOutline(k.insetPlan(bp, 1.2), SZ - 0.6, P), { tone: "faint" }));
  }
  for (const x of [-27, 36]) {
    o.push(S(k.slabOf({ x, y: -126, w: 6, d: 52, r: 1.2 }, 0, 4, P, 4, 0.4), { tone: "mid" }));
    o.push(L(k.lineOnTop([x + 3, -122], [x + 3, -78], 4, P), { tone: "faint" }));
  }
  return o.join("");
}
function pressBack() {   // 도장 프레스: 기둥 둘 · 가로대 · 팔
  const o = [];
  for (const x of [BED_L.x - 4, BED_L.x + BED_L.w + 4]) o.push(S(k.cylinder(x, -131, 2.6, 0, 48, P, 20), { tone: "mid", crease: "none" }), S(k.cylinder(x, -131, 4.2, 0, 2, P, 24, 0.3), { tone: "lo" }));
  o.push(S(k.slabOf({ x: BED_L.x - 8, y: -134, w: 62, d: 6, r: 1 }, 46, 6, P, 3, 0.4), { tone: "mid" }));
  o.push(S(k.slabOf({ x: BED_L.x + 20, y: -130, w: 6, d: 30, r: 1 }, 46, 4, P, 3, 0.4), { tone: "mid" }));
  o.push(D([at([BED_L.x - 4, -131, 52]), at([BED_L.x + BED_L.w + 4, -131, 52])], { size: 0.45 }));
  return o.join("");
}
const HEAD_UP = 26, HEAD_DN = SZ + 0.7;
function pressHead() {   // 격자 도장: 위 자리에 짓고 z 로 옮긴다 · 칼날 격자 8×8
  const cx = BED_L.x + BED_L.w / 2, cy = BED_L.y + BED_L.d / 2, hp = { x: BED_L.x + 1, y: BED_L.y + 1, w: BED_L.w - 2, d: BED_L.d - 2, r: 1 };
  const o = [S(k.cylinder(cx, cy, 1.6, HEAD_UP + 5, 20, P, 16), { tone: "mid", crease: "none" })];
  o.push(S(k.slabOf(hp, HEAD_UP, 5, P, 3, 0.5), { tone: "hi", crease: "lo", inner: L(k.sideSeam(hp, HEAD_UP + 2, P, 3), { tone: "faint" }) }));
  const g = [];
  for (let i = 1; i < 8; i++) g.push(k.lineOnTop([hp.x + i * hp.w / 8, hp.y + 1], [hp.x + i * hp.w / 8, hp.y + hp.d - 1], HEAD_UP + 5, P), k.lineOnTop([hp.x + 1, hp.y + i * hp.d / 8], [hp.x + hp.w - 1, hp.y + i * hp.d / 8], HEAD_UP + 5, P));
  o.push(L(g.join(""), { tone: "lo" }));
  o.push(S(k.cylinder(cx, cy, 3.4, HEAD_UP + 5, 1.6, P, 24, 0.3), { tone: "mid" }));
  return `<g data-part="head">${o.join("")}</g>`;
}
function pressCollar() { return S(k.cylinder(BED_L.x + 23, -99, 3.6, 45, 6, P, 24, 0.4), { tone: "mid" }); }
function copies() {   // 입력 자리에 짓고 x 로 옮긴다
  const gl = [];
  for (let i = 1; i < 8; i++) gl.push(k.lineOnTop([SHEET.x + i * SHEET.w / 8, SHEET.y], [SHEET.x + i * SHEET.w / 8, SHEET.y + SHEET.d], SZ + 0.66, P), k.lineOnTop([SHEET.x, SHEET.y + i * SHEET.d / 8], [SHEET.x + SHEET.w, SHEET.y + i * SHEET.d / 8], SZ + 0.66, P));
  const L0 = `<g data-part="copyL" style="opacity:0">${sheetSlab(SHEET, SZ + 0.6)}${drawing(SHEET, SZ + 0.62, false)}<g data-part="cut" style="opacity:0">${L(gl.join(""), { className: "cut" })}</g></g>`;
  const ends = new Map();
  LINES.forEach((l) => { for (const p of [l.a, l.b]) ends.set(l.slot + ":" + p, px(SHEET, l.slot, p)); });
  const R0 = `<g data-part="copyR" style="opacity:0">${sheetSlab(SHEET, SZ + 0.6)}${drawing(SHEET, SZ + 0.62, true)}<g data-part="vtx" style="opacity:0">${D([...ends.values()].map(([x, y]) => at([x, y, SZ + 0.7])), { size: 0.85, tone: "red" })}</g></g>`;
  return L0 + R0;
}
function gantry() {   // 펜 들보(y 로) · 머리(x 로) — vec140 과 같은 짜임
  const beam = [];
  for (const x of [-24, 39]) {
    beam.push(S(k.slabOf({ x: x - 4, y: BY - 5, w: 8, d: 10, r: 1.4 }, 4, 3, P, 3, 0.4), { tone: "mid" }));
    beam.push(S(k.slabOf({ x: x - 2.5, y: BY - 2.5, w: 5, d: 5, r: 0.8 }, 7, BEAM_Z - 7, P, 3, 0.3), { tone: "mid" }));
  }
  const bp = { x: -29, y: BY - 3, w: 73, d: 6, r: 1 };
  beam.push(S(k.slabOf(bp, BEAM_Z, 3.6, P, 4, 0.4), { tone: "mid", inner: L(k.sideSeam(bp, BEAM_Z + 1.8, P, 4), { tone: "faint" }) }));
  const [hx, py] = PARK, head = [];
  head.push(`<g data-part="pen">${S(k.cylinder(hx, py, 1.4, SZ + 0.7, 1, P, 18, 0.3), { tone: "hi", lit: true })}${S(k.cylinder(hx, py, 0.6, SZ + 1.7, 7, P, 12), { tone: "mid", crease: "none" })}${S(k.cylinder(hx, py, 1.7, SZ + 8.7, 3, P, 18, 0.3), { tone: "mid" })}</g>`);
  const hb = { x: hx - 5, y: BY + 3, w: 10, d: PEN_DY - 0.5, r: 1.1 };
  head.push(S(k.slabOf(hb, 11, BEAM_Z + 6 - 11, P, 3, 0.5), { tone: "hi", crease: "lo" }));
  head.push(D(k.corners(hb, 1.6).map(([x, y]) => at([x, y, BEAM_Z + 6])), { size: 0.38 }));
  return `<g data-part="beam">${beam.join("")}</g><g data-part="phead">${head.join("")}</g>`;
}
const TILE_N = 14;
function chute() {   // 홈통 + 칸 토큰(홈통 입구에 짓고 y 로 민다)
  const o = [S(k.slabOf(CHUTE, 0, 2, P, 3), { tone: "lo", crease: "none" })];
  for (const x of [CHUTE.x, CHUTE.x + CHUTE.w - 2]) o.push(S(k.slabOf({ x, y: CHUTE.y, w: 2, d: CHUTE.d, r: 0.4 }, 2, 2.4, P, 2), { tone: "mid" }));
  const pat = [(x, y) => [[x + 1, y + 3.5], [x + 6, y + 3.5]], (x, y) => [[x + 3.5, y + 1], [x + 3.5, y + 6]], (x, y) => [[x + 1, y + 2], [x + 4.5, y + 2], [x + 4.5, y + 6]], null, (x, y) => [[x + 1, y + 5], [x + 6, y + 1.5]]];
  for (let i = 0; i < TILE_N; i++) {   // 칸(패치) → ViT 를 지나면 금색 토큰
    const x = CHUTE.x + 6.5, y = CHUTE.y, z = 2;
    const pp = pat[i % pat.length], arc = i % 5 === 3;
    const mark = pp ? L(k.onTop(pp(x + 1, y + 1), z + 1.4, P), { className: "tile-ln" }) : "";
    const am = arc ? `<path class="iso-line tile-arc" d="${k.onTop(Array.from({ length: 9 }, (_, j) => [x + 4.5 + 3 * Math.cos(j / 8 * Math.PI), y + 4.5 + 3 * Math.sin(j / 8 * Math.PI)]), z + 1.4, P)}"/>` : "";
    const patch = `<g class="t-patch">${S(k.slabOf({ x, y, w: 9, d: 9, r: 0.6 }, z, 1.4, P, 2), { tone: "hi", crease: "lo" })}${mark}${am}</g>`;
    const tok = `<g class="t-tok" style="opacity:0">${S(k.slabOf({ x: x + 1.5, y: y + 1.5, w: 6, d: 6, r: 1.2 }, z, 3, P, 3, 0.4), { tone: "hi", crease: "lo", className: "tok" })}</g>`;
    o.push(`<g data-tile="${i}" style="opacity:0">${patch}${tok}</g>`);
  }
  return o.join("");
}
function printer() {   // 선 → 글 인쇄기 · 테이프(줄 i 를 틈 뒤에 짓고 n 줄만큼 민다)
  const clip = k.onTop([[TAPE.x - 4, TAPE_Y0], [TAPE.x + TAPE.w + 4, TAPE_Y0], [TAPE.x + TAPE.w + 4, MACH.y], [TAPE.x - 4, MACH.y]], 0.6, P, true);
  const rows = [S(k.slabOf({ x: TAPE.x, y: TAPE_Y0 - LINES.length * ROWT - 4, w: TAPE.w, d: LINES.length * ROWT + 4 + (MACH.y - TAPE_Y0), r: 0.4 }, 0, 0.5, P, 2), { tone: "hi", crease: "none" })];
  LINES.forEach((l, i) => {
    const yb = TAPE_Y0 - i * ROWT - 2.2;
    rows.push(T(TAPE.x + 2.5, yb, 0.5, l.tok, 5.6, "hi"));
    rows.push(L(k.lineOnTop([TAPE.x, yb - ROWT + 2.2], [TAPE.x + TAPE.w, yb - ROWT + 2.2], 0.5, P), { tone: "faint" }));
  });
  const o = [`<clipPath id="tape-clip"><path d="${clip}"/></clipPath><g clip-path="url(#tape-clip)"><g data-part="tape">${rows.join("")}</g></g>`];
  o.push(S(k.slabOf(PRN, 0, PRN_H, P, 6, 0.8), { tone: "mid", inner: L(k.sideSeam(PRN, 4, P, 6), { tone: "faint" }) }));
  o.push(L(k.planOutline(k.insetPlan(PRN, 2.4), PRN_H, P, 4), { tone: "lo" }));
  o.push(D(k.corners(PRN, 1.8).map(([x, y]) => at([x, y, PRN_H])), { size: 0.42 }));
  o.push(T(PRN.x + 5, PRN.y + 9.6, PRN_H, "145 · 선 토큰", 6, "hi"));
  o.push(`<g data-part="led">${S(k.cylinder(PRN.x + PRN.w - 8, PRN.y + 7, 2.2, PRN_H, 1.1, P, 22, 0.3), { tone: "hi", className: "lens" })}</g>`);
  o.push(L(k.segment([TAPE.x - 1, PRN.y + PRN.d, 1.4], [TAPE.x + TAPE.w + 1, PRN.y + PRN.d, 1.4], P), { tone: "hi", className: "slot" }));
  return o.join("");
}
function vitBox() {   // 146 의 인코더: 칸이 지나가는 ViT 상자(홈통 위 굴)
  const vb = { x: CHUTE.x - 10, y: CHUTE.y + 3, w: CHUTE.w + 20, d: 16, r: 2 }, o = [];
  o.push(S(k.slabOf(vb, 0, 12, P, 6, 0.8), { tone: "mid", inner: L(k.sideSeam(vb, 4, P, 6), { tone: "faint" }) }));
  o.push(L(k.planOutline(k.insetPlan(vb, 2.4), 12, P, 4), { tone: "lo" }));
  o.push(D(k.corners(vb, 1.8).map(([x, y]) => at([x, y, 12])), { size: 0.42 }));
  o.push(T(vb.x + 4, vb.y + 10.4, 12, "146 · ViT", 6, "hi"));
  o.push(L(k.segment([CHUTE.x + 2, vb.y + vb.d, 5], [CHUTE.x + CHUTE.w - 2, vb.y + vb.d, 5], P), { tone: "hi", className: "slot" }));
  return o.join("");
}
function hoods() {   // 홈통 · 테이프가 언어 모델로 들어가는 덮개
  const o = [];
  for (const h of [{ x: CHUTE.x - 2, y: MACH.y - 7, w: CHUTE.w + 4, d: 7, r: 1 }, { x: TAPE.x - 4, y: MACH.y - 7, w: TAPE.w + 8, d: 7, r: 1 }]) {
    o.push(S(k.slabOf(h, 0, 10, P, 3, 0.5), { tone: "mid" }));
    o.push(L(k.segment([h.x + 1.5, h.y, 3], [h.x + h.w - 1.5, h.y, 3], P), { tone: "lo" }));
  }
  return o.join("");
}
const KEYXS = Array.from({ length: 19 }, (_, i) => MACH.x + 14 + i * 10.6);
function machine() {   // 언어 모델 = 타자기 한 대
  const o = [S(k.slabOf(MACH, 0, MH, P, 6, 1), { tone: "mid", inner: L(k.sideSeam(MACH, 5, P, 6), { tone: "faint" }) })];
  o.push(L(k.planOutline(k.insetPlan(MACH, 3), MH, P, 4), { tone: "lo" }));
  o.push(D(k.corners(MACH, 2).map(([x, y]) => at([x, y, MH])), { size: 0.45 }));
  // 롤러(가로 막대) + 양끝 손잡이
  const pl = { x: MACH.x + 22, y: MACH.y + 5, w: MACH.w - 44, d: 8, r: 3.8 };
  o.push(S(k.slabOf(pl, MH, 5, P, 8, 0.5), { tone: "hi", crease: "lo" }));
  for (const x of [MACH.x + 12, MACH.x + MACH.w - 12]) o.push(S(k.cylinder(x, MACH.y + 9, 5.4, MH, 10, P, 40, 0.5), { tone: "hi", crease: "lo", inner: L(k.knurl(x, MACH.y + 9, 5.4, MH + 0.6, MH + 9.4, 22, P), { tone: "faint" }) }));
  // 이름판
  const np = { x: MACH.x + 46, y: MACH.y + 16, w: 118, d: 13, r: 1.2 };
  o.push(S(k.slabOf(np, MH, 0.8, P, 4), { tone: "lo" }));
  o.push(T(np.x + 4, np.y + 9, MH + 0.8, "언어 모델 · cadrille 2B (Qwen2)", 6, "hi"));
  o.push(D([at([np.x + 2, np.y + np.d / 2, MH + 0.8]), at([np.x + np.w - 2, np.y + np.d / 2, MH + 0.8])], { size: 0.4 }));
  // LoRA 카트리지(금)
  const lo = { x: MACH.x + 172, y: MACH.y + 15, w: 34, d: 14, r: 1.4 };
  o.push(S(k.slabOf({ x: lo.x - 1.5, y: lo.y - 1.5, w: lo.w + 3, d: lo.d + 3, r: 1.8 }, MH, 0.8, P, 4), { tone: "lo" }));
  o.push(`<g class="lora">${S(k.slabOf(lo, MH + 0.8, 5, P, 4, 0.5), { tone: "hi", crease: "lo" })}</g>`);
  o.push(T(lo.x + lo.w / 2, lo.y + 9.2, MH + 5.8, "LoRA", 6.4, "hi", "middle"));
  // 선택 손잡이 146 / 145
  const tr = { x: MACH.x + 10, y: MACH.y + 18, w: 30, d: 6, r: 2.4 };
  o.push(S(k.slabOf(tr, MH, 0.6, P, 6), { tone: "lo", crease: "none" }));
  o.push(T(tr.x, tr.y - 1.4, MH, "146", 4.4, "mid"), T(tr.x + tr.w, tr.y - 1.4, MH, "145", 4.4, "mid", "end"));
  const kx = tr.x + tr.w / 2;
  o.push(`<g data-part="sel">${S(k.slabOf({ x: kx - 3.5, y: tr.y - 1, w: 7, d: 8, r: 1.4 }, MH + 0.6, 3.2, P, 3, 0.4), { tone: "hi", lit: true })}</g>`);
  // 자판 두 줄
  for (const [row, y] of [[0, MACH.y + 37], [1, MACH.y + 47]]) KEYXS.forEach((x, i) => {
    const xx = x + row * 5;
    o.push(`<g data-key="${row * 19 + i}">${S(k.cylinder(xx, y, 3.3, MH, 2.6, P, 22, 0.4), { tone: "hi", crease: "lo" })}</g>`);
  });
  o.push(L(k.segment([PAPER.x + 2, MACH.y + MACH.d, 4], [PAPER.x + PAPER.w - 2, MACH.y + MACH.d, 4], P), { tone: "hi", className: "slot" }));
  return o.join("");
}
function paper() {   // 출력 용지: 코드가 한 줄씩 · 줄 위 막대(인쇄 머리)
  const tray = { x: PAPER.x - 4, y: PAPER.y - 2, w: PAPER.w + 8, d: PAPER.d + 4, r: 1.4 };
  const o = [S(k.slabOf(tray, 0, 1.4, P, 4, 0.3), { tone: "lo" })];
  o.push(S(k.slabOf(PAPER, 1.4, 0.5, P, 2), { tone: "hi", crease: "none" }));
  CODE.forEach((c, i) => {
    const y = PAPER.y + 8 + i * ROWC;
    o.push(`<g data-code="${i}" style="opacity:0">${T(PAPER.x + 4 + INDENT[i] * 8, y, 1.9, c, 6.2, "hi")}</g>`);
  });
  for (const x of [tray.x + 0.5, tray.x + tray.w - 3.5]) o.push(S(k.slabOf({ x, y: tray.y + 1, w: 3, d: tray.d - 2, r: 0.6 }, 1.4, 2.2, P, 2), { tone: "mid" }));
  const bar = { x: tray.x, y: PAPER.y + 14.6, w: tray.w, d: 3, r: 1.2 };
  o.push(`<g data-part="pbar">${S(k.slabOf(bar, 3.6, 1.2, P, 3, 0.3), { tone: "mid" })}${D([at([bar.x + 1.8, bar.y + 1.5, 4.8]), at([bar.x + bar.w - 1.8, bar.y + 1.5, 4.8])], { size: 0.4 })}</g>`);
  return o.join("");
}
// 부품(정답 = 보스 10 · 생성 = 보스 12) — 가운데 (cx, cy) 바닥 z0 · 배율 s
function partSvg(cx, cy, z0, s, bossH, ids) {
  const b0 = { x: cx - 17.05 * s, y: cy - 23.7 * s, w: 34.1 * s, d: 47.4 * s, r: 0 };
  const b1 = { x: cx - 7 * s, y: cy - (14.7 + 9) * s, w: 14 * s, d: 18 * s, r: 0 };
  const a = S(k.slabOf(b0, z0, 9 * s, P, 1), { tone: "hi", crease: "lo" });
  const hole = `<path class="hole" d="${circ(cx, cy, 4 * s, z0 + 9 * s + 0.02)}"/>`;
  const b = S(k.slabOf(b1, z0 + 9 * s, bossH * s, P, 1), { tone: "hi", crease: "lo" });
  if (!ids) return a + hole + b;
  return `<g data-part="${ids[0]}" style="opacity:0">${a}</g><g data-part="${ids[1]}" style="opacity:0">${hole}</g><g data-part="${ids[2]}" style="opacity:0">${b}</g>`;
}
const TT_Z = 7;
function turntable() {
  const [cx, cy] = TT.c, o = [S(k.cylinder(cx, cy, TT.r, 0, 3, P, 48, 0.4), { tone: "lo" })];
  o.push(S(k.cylinder(cx, cy, TT.r - 3, 3, TT_Z - 3, P, 48, 0.4), { tone: "mid" }));
  o.push(L(k.radialTicks(cx, cy, TT.r - 4, 48, 6, TT_Z, [-1.2, -2.4], P).minor || "", { tone: "lo" }));
  o.push(L(k.ring(cx, cy, TT.r - 9, TT_Z, P, 40), { tone: "faint" }));
  o.push(T(cx - TT.r + 2, cy + TT.r + 5, 0, "실행한 부품", 5.2, "mid"));
  o.push(partSvg(cx, cy, TT_Z, 1, 12, ["b0", "bh", "b1"]));
  return o.join("");
}
// 실루엣 판: 옆에서 본 실루엣(y, z) · 생성 = 파랑 칠 · 정답 = 금 테 · 남는 곳 = 빨강
function silhouette() {
  const o = [S(k.slabOf(SIL, 0, 2.4, P, 4, 0.4), { tone: "lo" })];
  const pl = k.insetPlan(SIL, 3);
  o.push(S(k.slabOf(pl, 2.4, 0.6, P, 2), { tone: "hi", crease: "none" }));
  o.push(D(k.corners(SIL, 1.6).map(([x, y]) => at([x, y, 2.4])), { size: 0.4 }));
  const z = 3.02, cx = SIL.x + SIL.w / 2, by = SIL.y + 52, K = 1.15;
  const m = ([yy, zz]) => [cx + yy * K, by - zz * K];
  const poly = (H) => [[-23.7, 0], [23.7, 0], [23.7, 9], [-5.7, 9], [-5.7, 9 + H], [-23.7, 9 + H]].map(m);
  o.push(L(k.lineOnTop([SIL.x + 6, by], [SIL.x + SIL.w - 6, by], z, P), { tone: "faint" }));
  o.push(`<g data-part="silG" style="opacity:0"><path class="sil-gen" d="${k.onTop(poly(12), z, P, true)}"/></g>`);
  o.push(`<g data-part="silX" style="opacity:0"><path class="sil-x" d="${k.onTop([[-23.7, 19], [-5.7, 19], [-5.7, 21], [-23.7, 21]].map(m), z + 0.01, P, true)}"/></g>`);
  o.push(`<g data-part="silT" style="opacity:0"><path class="iso-line sil-true" d="${k.onTop(poly(10), z + 0.02, P, true)}"/></g>`);
  o.push(T(SIL.x + 5, SIL.y + 10, z, "실루엣 비교", 5.2, "hi"));
  o.push(`<g data-part="iou" style="opacity:0">${T(SIL.x + 5, SIL.y + SIL.d - 6, z, "IoU = 겹침 ÷ 합침", 4.8, "hi")}</g>`);
  return o.join("");
}
function answer() {   // 정답 카드: 정답 부품 + 그 코드
  const o = [S(k.slabOf(HOLD, 0, 2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(HOLD, 2).map(([x, y]) => at([x, y, 2])), { size: 0.42 }));
  o.push(S(k.slabOf(CARD, 2, 0.8, P, 4), { tone: "hi", crease: "lo" }));
  const z = 2.82;
  o.push(T(CARD.x + 4, CARD.y + 8, z, "정답 카드 · 정답 부품과 그 코드", 5.2, "mid"));
  o.push(L(k.lineOnTop([CARD.x + 2, CARD.y + 11], [CARD.x + CARD.w - 2, CARD.y + 11], z, P), { tone: "faint" }));
  TRUE.forEach((c, i) => {
    const diff = c !== CODE[i];
    o.push(`<g data-true="${i}"${diff ? ' data-diff=""' : ""}>${T(CARD.x + 44 + INDENT[i] * 6, CARD.y + 18 + i * 7, z, c, 4.6, "hi")}</g>`);
  });
  o.push(`<g data-part="tpart">${partSvg(CARD.x + 21, CARD.y + 42, z, 0.68, 10)}</g>`);
  return o.join("");
}
function steps() {
  const o = [S(k.slabOf(KEYS, 0, 1.2, P, 4, 0.4), { tone: "lo" })];
  o.push(D(k.corners(KEYS, 1.8).map(([x, y]) => at([x, y, 1.2])), { size: 0.42 }));
  for (let i = 0; i < NKEY; i++) {   // 2 열 × 3 줄
    const kp = { x: KEYS.x + 3.5 + (i % 2) * 16.5, y: KEYS.y + 3.5 + Math.floor(i / 2) * 16.5, w: 14.5, d: 14.5, r: 1.4 };
    o.push(`<g data-step="${i}">${S(k.slabOf(kp, 1.2, 2.6, P, 3, 0.5), { tone: "mid" })}${k.faceTextSvg(k.topMatrix([kp.x + kp.w / 2, kp.y + kp.d / 2 + 2.6], 3.8, P, "x"), String(i + 1), { size: 7, tone: "mid", anchor: "middle" })}</g>`);
  }
  return o.join("");
}

// ── 시간표 ─────────────────────────────────────────────────────
const LOOP = 44;
const T2 = 3.6, T3 = 12.6, T4 = 22, T5 = 30, T6 = 35.4, TF = 40.2;
const TILE0 = 7.0, TILE_DT = 0.32, TILE_RUN = 1.5;
const TR0 = 14.8, TRB = 0.19;   // 펜: 선마다 0.19 초
const PEN = [[0, ...PARK, 3, 0], [TR0, ...PARK, 3, 0]];
const LN_T = [];
LINES.forEach((l, j) => {
  const pts = linePts(BED_R, l), t0 = TR0 + j * TRB;
  PEN.push([t0 + 0.05, ...pts[0], 3, 1], [t0 + 0.07, ...pts[0], 0, 1]);
  pts.forEach((p, i) => PEN.push([t0 + 0.08 + 0.1 * i / (pts.length - 1), ...p, 0, 0]));
  PEN.push([t0 + TRB, ...pts[pts.length - 1], 3, 1]);
  LN_T.push(t0 + 0.18);
});
const TR1 = TR0 + LINES.length * TRB;
PEN.push([TR1 + 1, ...PARK, 3, 1]);
const CODE0 = T4 + 0.6, CODEDT = 0.9;

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "판 145 와 146 코드 생성을 한 대의 타자기와 두 급지기로 그린 그림. 입력은 부품 하나의 3 면도(위 · 앞 · 옆 각 128 화소). 왼쪽 급지기(146)는 도면을 격자 도장으로 칸(패치)으로 잘라 칸 토큰을 홈통으로 흘려보낸다(Qwen2-VL ViT, 이미지 토큰 약 256 개). 오른쪽 급지기(145)는 펜이 도면의 선을 하나씩 따라가고 인쇄기가 선마다 글 한 줄을 테이프에 찍는다. 두 입력은 같은 타자기, 즉 같은 언어 모델 cadrille 2B(Qwen2, LoRA 카트리지)로 들어가고, 타자기는 출력 용지에 CadQuery 코드를 한 줄씩 쓴다. 코드를 실행하면 회전대 위에 부품이 생기고, 실루엣 판에서 정답 부품의 실루엣과 겹쳐 IoU 를 잰다. 정답 카드에 정답 부품과 그 코드가 놓여 있다.",
  body: [base(), input(), pressBack(), beds(), copies(), pressHead(), pressCollar(), `${gantry()}`, chute(), vitBox(), printer(), hoods(), machine(), turntable(), silhouette(), paper(), answer(), steps()],
});

const live = `
const P = ${JSON.stringify(P)};
const PARK = ${JSON.stringify(PARK)}, PEN = ${JSON.stringify(PEN)}, LN_T = ${JSON.stringify(LN_T)};
const LOOP = ${LOOP}, T2 = ${T2}, T3 = ${T3}, T4 = ${T4}, T5 = ${T5}, T6 = ${T6}, TF = ${TF};
const TILE0 = ${TILE0}, TILE_DT = ${TILE_DT}, TILE_RUN = ${TILE_RUN}, TILE_LEN = ${CHUTE.d + 2}, TR0 = ${TR0}, TR1 = ${TR1};
const NL = ${LINES.length}, ROWT = ${ROWT}, ROWC = ${ROWC}, CODE0 = ${CODE0}, CODEDT = ${CODEDT}, NC = ${CODE.length};
const VIT_AT = 12, SLIDE = ${SLIDE}, HEAD_UP = ${HEAD_UP}, HEAD_DN = ${HEAD_DN}, NKEYS = ${KEYXS.length * 2};
const svg = document.querySelector(".iso-stage svg"), stage = document.querySelector(".iso-stage");
const $ = (s) => svg.querySelector(s), $$ = (s) => [...svg.querySelectorAll(s)];
const part = (n) => $('[data-part="' + n + '"]');
const tiles = $$("[data-tile]").sort((a, b) => a.dataset.tile - b.dataset.tile);
const lns = $$("[data-ln]"), codes = $$("[data-code]").sort((a, b) => a.dataset.code - b.dataset.code), trues = $$("[data-true]");
const keysM = $$("[data-key]"), steps = $$("[data-step]").sort((a, b) => a.dataset.step - b.dataset.step);
const readout = document.querySelector("[data-readout]"), still = matchMedia("(prefers-reduced-motion: reduce)");
const ease = (u) => u <= 0 ? 0 : u >= 1 ? 1 : u * u * (3 - 2 * u);
const ramp = (t, t0, d = 0.5) => ease((t - t0) / d);
const win = (t, t0, t1, d = 0.5) => ramp(t, t0, d) * (1 - ramp(t, t1, d));
const END = LOOP - 1.4;
const mv = (el, v) => el.setAttribute("transform", translateAlong(P, v));
function penAt(t) {
  if (t <= PEN[0][0]) return PEN[0].slice(1, 4);
  for (let i = 1; i < PEN.length; i++) if (t <= PEN[i][0]) {
    const a = PEN[i - 1], b = PEN[i], u0 = (t - a[0]) / Math.max(1e-6, b[0] - a[0]), u = b[4] ? ease(u0) : u0;
    return [a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u];
  }
  return PEN[PEN.length - 1].slice(1, 4);
}
function text(t) {
  if (t < T2) return "① 입력: 부품 하나의 3 면도 (위 · 앞 · 옆, 128 px 씩)";
  if (t < 6.6) return "② 146 ViT 그대로: 도면을 격자 도장으로 칸(패치)으로 자른다";
  if (t < T3) return "② Qwen2-VL 의 ViT 가 칸을 이미지 토큰으로 → 약 256 개가 언어 모델로";
  if (t < TR0) return "③ 145 선 토큰: 우리 CNN 이 화소마다 선을 칠하고, 꼭짓점에서 끊는다";
  if (t < TR1 + 0.3) return "③ 선 하나 = 글 한 줄 「뷰 종류 시작 끝 (원호 가운데) (h=숨음)」 · " + Math.min(NL, Math.max(1, Math.ceil((t - TR0) / ${TRB}))) + "/" + NL;
  if (t < T4) return "③ 선 글 27 줄이 테이프로 언어 모델에 들어간다";
  if (t < CODE0 + 2.4) return "④ 같은 언어 모델: cadrille 2B (Qwen2 · CadQuery 를 앎) + LoRA";
  if (t < T5) return "④ 언어 모델이 CadQuery 코드를 한 줄씩 쓴다";
  if (t < T6) return "⑤ 실행: 코드를 돌리면 3D 부품이 나온다";
  if (t < 38.2) return "⑥ 정답 부품과 실루엣을 겹친다 · IoU = 겹침 ÷ 합침";
  if (t < TF) return "⑥ 어긋난 곳(빨강)만큼 IoU 가 준다 · 실행 안 되면 0";
  return "인코더만 바꾸고 같은 언어 모델이 코드를 쓴다 · 실행해서 모양을 맞춘다";
}
function draw(t) {
  const out = 1 - ramp(t, END, 0.8);
  // ① 입력 선 켜기
  for (const e of part("in-lines").querySelectorAll(".dr")) e.classList.toggle("on", t > 0.6 && t < T2 - 0.2);
  // ② 146: 복사본 → 왼쪽 급지기 · 도장 · 칸 토큰
  const cl = part("copyL");
  cl.style.opacity = (t >= T2 ? 1 : 0) * out;
  mv(cl, [-SLIDE * ramp(t, T2 + 0.2, 1.2), 0, 0]);
  const hz = HEAD_UP - (HEAD_UP - HEAD_DN) * (ramp(t, T2 + 1.6, 0.7) - ramp(t, T2 + 2.6, 0.7));
  mv(part("head"), [0, 0, hz - HEAD_UP]);
  part("cut").style.opacity = ramp(t, T2 + 2.2, 0.2);
  tiles.forEach((g, i) => {
    const u = (t - TILE0 - i * TILE_DT) / TILE_RUN;
    g.style.opacity = u > 0 && u < 1 ? Math.min(1, u * 8, (1 - u) * 6) : 0;
    mv(g, [0, TILE_LEN * Math.max(0, Math.min(1, u)), 0]);
    const past = u * TILE_LEN > VIT_AT ? 1 : 0;
    g.firstChild.style.opacity = 1 - past; g.lastChild.style.opacity = past;
  });
  // ③ 145: 복사본 → 오른쪽 급지기 · 꼭짓점 · 펜 · 테이프
  const cr = part("copyR");
  cr.style.opacity = (t >= T3 ? 1 : 0) * out;
  mv(cr, [SLIDE * ramp(t, T3 + 0.2, 1.2), 0, 0]);
  part("vtx").style.opacity = win(t, T3 + 1.6, T4, 0.4);
  lns.forEach((e) => e.classList.toggle("on", t >= LN_T[+e.dataset.ln] && t < T4 + 0.5));
  const [px, py, lift] = penAt(t);
  mv(part("beam"), [0, py - PARK[1], 0]);
  mv(part("phead"), [px - PARK[0], py - PARK[1], 0]);
  mv(part("pen"), [0, 0, lift]);
  const done = LN_T.filter((x) => t >= x).length;
  const n = t < LN_T[0] ? 0 : done + (t - LN_T[Math.max(0, done - 1)] < 0.15 ? -1 + ramp(t, LN_T[Math.max(0, done - 1)], 0.15) : 0);
  mv(part("tape"), [0, ROWT * (t < T4 + 1.4 ? n : NL + 5 * ramp(t, T4, 1.4)) , 0]);
  part("tape").style.opacity = ramp(t, T3 + 0.8, 0.4) * (1 - ramp(t, T4 + 1.4, 0.3));
  part("led").toggleAttribute("data-on", t >= TR0 && t < TR1 && ((t - TR0) % ${TRB}) < 0.09);
  // 선택 손잡이: 146 쪽 · 145 쪽 · 가운데
  const sel = -10 * win(t, T2 + 0.1, T3, 0.6) + 10 * win(t, T3 + 0.1, T4, 0.6);
  mv(part("sel"), [sel, 0, 0]);
  // ④ 코드
  const cn = t < CODE0 ? 0 : Math.min(NC, Math.floor((t - CODE0) / CODEDT) + 1);
  codes.forEach((g, i) => { g.style.opacity = ramp(t, CODE0 + i * CODEDT, 0.25) * out; });
  const cur = (t5) => t5 < T5 + 0.4 ? -1 : t5 < T5 + 1.4 ? 0 : t5 < T5 + 2.4 ? 2 : t5 < T5 + 3.6 ? 4 : t5 < T6 ? 7 : -1;
  const hi = cur(t);
  codes.forEach((g, i) => g.toggleAttribute("data-now", (hi === 0 && i < 2) || (hi === 2 && (i === 2 || i === 3)) || (hi === 4 && i >= 4 && i <= 6) || (hi === 7 && i === 7)));
  const by = cn ? (cn - 2 + ramp(t, CODE0 + (cn - 1) * CODEDT, 0.25)) * ROWC : -ROWC;
  mv(part("pbar"), [0, t < END ? by : by * out, 0]);
  keysM.forEach((g, i) => { const on = t >= CODE0 && t < CODE0 + NC * CODEDT && ((i * 7 + Math.floor(t * 9) * 13) % 23) < 2; mv(g, [0, 0, on ? -1.2 : 0]); });
  // ⑤ 실행
  const b0 = part("b0"), bh = part("bh"), b1 = part("b1");
  b0.style.opacity = ramp(t, T5 + 0.4, 0.4) * out; mv(b0, [0, 0, 10 * (1 - ramp(t, T5 + 0.4, 0.8))]);
  bh.style.opacity = ramp(t, T5 + 1.5, 0.4) * out;
  b1.style.opacity = ramp(t, T5 + 2.5, 0.4) * out; mv(b1, [0, 0, 12 * (1 - ramp(t, T5 + 2.5, 0.8))]);
  // ⑥ 비교
  part("silG").style.opacity = ramp(t, T6 + 0.3, 0.5) * out;
  part("silT").style.opacity = ramp(t, T6 + 1.1, 0.5) * out;
  part("silX").style.opacity = ramp(t, T6 + 2.9, 0.4) * out;
  part("iou").style.opacity = ramp(t, T6 + 1.8, 0.5) * out;
  part("tpart").classList.toggle("on", t >= T6 + 1.1 && t < END);
  trues.forEach((g) => g.toggleAttribute("data-now", g.hasAttribute("data-diff") && t >= T6 + 2.9 && t < END));
  const step = t < T2 ? 0 : t < T3 ? 1 : t < T4 ? 2 : t < T5 ? 3 : t < T6 ? 4 : t < END ? 5 : -1;
  steps.forEach((g, i) => g.toggleAttribute("data-active", i === step));
  readout.textContent = text(t);
}
let frame = 0, last = 0, clock = 0, visible = false, held = false;
function tick(now) { const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60; last = now; clock = (clock + dt) % LOOP; draw(clock); frame = visible && !held ? requestAnimationFrame(tick) : 0; }
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible && !frame && !still.matches && !held) { last = 0; frame = requestAnimationFrame(tick); } }, { rootMargin: "120px 0px" }).observe(stage);
window.__seek = (t) => { held = true; cancelAnimationFrame(frame); frame = 0; draw(((t % LOOP) + LOOP) % LOOP); };   // 녹화용
if (still.matches) draw(39); else draw(0);
`;
const css = `<style>
.iso{--k-st:var(--anatomy-blue);--k-cu:var(--anatomy-green);--k-v:var(--anatomy-red);--k-au:#c98a00}
.iso[data-theme="dark"],[data-theme="dark"] .iso{--k-au:#f0b429}
.iso-line.dr{stroke:var(--k-st);stroke-width:.7;stroke-opacity:.75}
.iso-line.dr-arc{stroke:var(--k-cu)}
.iso-line.dr-hid{stroke-dasharray:1.4 1.1}
.iso-line.dr.on{stroke-width:1.7;stroke-opacity:1}
.iso-line.cut{stroke:var(--k-au);stroke-width:.9}
.tok .iso-top{fill:var(--k-au)}
.iso-line.tile-ln{stroke:var(--k-st);stroke-width:1}.iso-line.tile-arc{stroke:var(--k-cu);stroke-width:1;fill:none}
.hole{fill:var(--anatomy-muted);stroke:var(--anatomy-strong);stroke-width:.5}
.sil-gen{fill:var(--k-st);fill-opacity:.28;stroke:var(--k-st);stroke-width:1}
.sil-x{fill:var(--k-v);fill-opacity:.55;stroke:none}
.iso-line.sil-true{stroke:var(--k-au);stroke-width:1.8;fill:none}
.slot{stroke-width:1.6}
.iso-dots[data-tone="red"] circle{fill:var(--k-v);opacity:1}
.lora .iso-top{fill:color-mix(in srgb,var(--k-au) 35%,var(--anatomy-top))}
[data-part="led"][data-on] .lens>.iso-top{fill:var(--k-v)}
[data-code][data-now] .iso-face-text{fill:var(--k-au);font-weight:700}
[data-true][data-now] .iso-face-text{fill:var(--k-v);font-weight:700}
[data-part="tpart"].on .iso-edge{stroke:var(--k-au)}
[data-step][data-active] .iso-edge{stroke:var(--anatomy-lit)}[data-step][data-active] .iso-top{fill:var(--anatomy-lit-top)}
[data-step][data-active] .iso-face-text{fill:var(--anatomy-lit);font-weight:700}
</style>`;
const body = k.plateHtml({
  fig: "그림 7", title: "코드 생성 · 판 145 · 146",
  hint: `저절로 돈다 · 한 바퀴 ${LOOP} 초`,
  readout: "① 입력: 부품 하나의 3 면도 (위 · 앞 · 옆, 128 px 씩)",
  keys: [
    { mark: "flat", label: "번호판 ① 입력 3 면도 ② 146 칸 토큰 ③ 145 선 토큰 ④ 언어 모델이 코드 ⑤ 실행 ⑥ 실루엣 비교" },
    { mark: "raised", label: "두 급지기 = 두 인코더 · 왼쪽 격자 도장(ViT 패치) · 오른쪽 펜 + 인쇄기(우리 선 글) · 가운데 타자기 한 대 = 같은 언어 모델" },
    { mark: "blue", label: "파랑 = 직선 · 초록 = 원호 · 금 = 지금 실행 중인 코드 줄 · 정답 실루엣 · 빨강 = 꼭짓점 · 정답과 어긋난 곳" },
    { mark: "flat", label: "정답 카드 = 정답 부품과 그 CadQuery 코드 · 생성 코드와 다른 두 줄이 빨강으로 켜진다" },
  ],
  caption: "판 145 와 146 은 한 비교판의 두 참가자다. 입력은 부품 하나의 3 면도(위 · 앞 · 옆, 각 128 px)이고, 디코더는 둘 다 cadrille — CadQuery 를 이미 아는 2B 언어 모델(Qwen2) — 에 LoRA 를 붙여 미세조정한 것이다. 다른 것은 인코더, 곧 도면이 언어 모델에 닿는 길 하나다. 146 은 도면 그림을 칸(패치)으로 잘라 Qwen2-VL 의 ViT 가 이미지 토큰 약 256 개로 바꾼다. 145 는 우리 CNN 이 화소마다 선을 칠하고 벡터화가 꼭짓점에서 끊어, 선 하나를 「뷰 종류 x0 y0 x1 y1 (원호면 가운데 점) (숨은선이면 h)」 글 한 줄로 준다. 언어 모델이 쓴 CadQuery 코드를 실행해 나온 부품의 실루엣을 정답 부품의 실루엣과 겹쳐 IoU 를 잰다(실행 실패 = 0). 두 판은 아직 돌지 않았다 — 부품 · 코드 · 선 글은 설명용 예시이고, 생성 코드의 보스 높이(12 대 정답 10)는 IoU 를 보이려 넣은 차이다. 숫자 결과는 그리지 않았다.",
  body: `${css}<div class="iso-stage" tabindex="0" role="img" aria-label="판 145 · 146 코드 생성 동작 그림">${svg}</div>`,
});
mkdirSync(OUT, { recursive: true });
const html = join(OUT, theme === "light" ? "code145-light.html" : "code145.html");
writeFileSync(html, k.pageHtml({ title: "판 145 · 146 코드 생성", theme, body, script: kitScript() + live }));
console.log("wrote", html, "· 선 글", LINES.length, "줄");

if (RECORD) {   // 8 fps · 2 배 · light → mp4(libx264 yuv420p crf20) + gif(800 폭, 같은 프레임)
  const FPS = 8, DRIVE = "C:/Users/zesky/.claude/skills/anatomy/scripts/drive.mjs", FR = join(OUT, "frames");
  mkdirSync(FR, { recursive: true }); for (const f of readdirSync(FR)) unlinkSync(join(FR, f));   // rmSync 재귀는 한글 경로에서 node 가 죽었다
  const acts = [];
  for (let i = 0; i < LOOP * FPS; i++) acts.push(["eval", `__seek(${(i / FPS).toFixed(3)})`], ["shot", `frames/f${String(i).padStart(3, "0")}.png`, null, 2]);
  writeFileSync(join(OUT, "frames.json"), JSON.stringify(acts));
  execFileSync(process.execPath, [DRIVE, html, "--actions", "frames.json"], { cwd: OUT, stdio: ["ignore", "ignore", "inherit"] });
  const mp4 = join(HERE, "code145.mp4"), gif = join(HERE, "code145.gif");
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], { stdio: "inherit" });
  execFileSync("ffmpeg", ["-y", "-v", "error", "-framerate", String(FPS), "-i", join(FR, "f%03d.png"), "-vf", "scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse", gif], { stdio: "inherit" });
  console.log("wrote", mp4, gif);
}
