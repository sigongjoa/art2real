import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 78 편(다시) — 판정기준79 · 80 · 비누 모양 부품(시험 82) · 고치기 전 20 부품 겉 어긋남 칸 0.82 · 곡면 0.86 칸 · 공 반지름 0.3 → 0.2973 · 고친 뒤 0.64 칸 · 10° 넘게 비뚤어진 겉 35 % → 23 %
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 점: string; 점색: string };
const 돌림 = ({ 판들, 제목 }: { 판들: 판[]; 제목: string }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0"); const 폭 = 440, 왼 = (1000 - 폭 * 판들.length) / 2;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 22, textAlign: "center", fontSize: 36, color: 먹 }}>{제목}</div>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 66, textAlign: "center", fontSize: 30, color: 회 }}>1칸 = 깎는 격자 한 칸</div>
    {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 }), q = interpolate(f, [40 + j * 15, 55 + j * 15], [0, 1], C);
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 95, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep78/soap_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 42, color: 금, marginTop: -40 }}>{c.글}</div>
        <div style={{ textAlign: "center", fontSize: 70, color: c.점색, opacity: q, marginTop: 0 }}>{c.점}</div></div>; })}
  </AbsoluteFill>;
};
const 제 = "부품 20개 · 실제 부품과 겉이 어긋난 거리 (낮을수록 좋음)";
export const 전78 = () => <돌림 제목={제} 판들={[{ 파일: "cell", 글: "칸으로 깎기", 점: "0.82칸", 점색: 회 }, { 파일: "fitold", 글: "곡면 맞춰 깎기", 점: "0.86칸", 점색: 빨 }]} />;
export const 후78 = () => <돌림 제목={제} 판들={[{ 파일: "cell", 글: "칸으로 깎기", 점: "0.82칸", 점색: 회 }, { 파일: "fit", 글: "고친 곡면 깎기", 점: "0.64칸", 점색: 초 }]} />;
// 테두리: 깊이 지도 한 줄 — 부품이 있는 화소(초록 막대)와 빈 화소 · 빈 곳을 바닥값으로 두고 이어 붙이면 테두리가 안으로 기운다(빨강) · 고친 뒤 벽은 화소 사이에 선다(초록)
export const 테두리78 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 }), b = interpolate(f, [30, 60], [0, 1], { ...C, easing: 이징 }), c = interpolate(f, [170, 200], [0, 1], { ...C, easing: 이징 });
  const 칸 = 90, x0 = 95, 위 = 250, 바닥 = 560, 있 = 6;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 40, top: 30, fontSize: 34, color: 먹, whiteSpace: "nowrap" }}>반지름 0.3인 공을 깎으면 → <span style={{ color: 빨 }}>0.2973</span> (0.12칸 줄어듦)</div>
    <svg width={1000} height={700} style={{ position: "absolute", left: 0, top: 0 }}>
      {Array.from({ length: 9 }).map((_, i) => <rect key={i} x={x0 + i * 칸 + 4} y={i < 있 ? 위 : 바닥 - 6} width={칸 - 8} height={i < 있 ? 바닥 - 위 : 6} fill={i < 있 ? "rgb(200,230,205)" : "rgb(225,225,230)"} />)}
      <polyline points={`${x0},${위} ${x0 + (있 - .5) * 칸},${위} ${x0 + (있 - .5) * 칸 + (칸) * b},${위 + (바닥 - 위) * b}`} fill="none" stroke={빨} strokeWidth={9} />
      <polyline points={`${x0},${위 - 14} ${x0 + 있 * 칸},${위 - 14} ${x0 + 있 * 칸},${위 - 14 + (바닥 - 위 + 14) * c}`} fill="none" stroke={초} strokeWidth={9} opacity={c} />
    </svg>
    <div style={{ position: "absolute", left: 60, top: 590, fontSize: 38, color: 빨, opacity: b }}>━ 빈 곳과 섞여 테두리가 안으로 기욺</div>
    <div style={{ position: "absolute", left: 60, top: 640, fontSize: 38, color: 초, opacity: c }}>━ 고친 뒤: 벽이 화소 경계에 섬</div>
  </AbsoluteFill>; };
// 막대: 부품 20 개 · 실제 부품보다 10° 넘게 비뚤어진 겉 · 칸 35 % · 곡면(고친 뒤) 23 %
export const 막대78 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const b1 = interpolate(f, [30, 60], [0, 35], { ...C, easing: 이징 }), b2 = interpolate(f, [70, 100], [0, 23], { ...C, easing: 이징 }), 자 = 19, z = interpolate(f, [10, 24], [0, 1], C);
  const 줄 = (y: number, 글: string, 값: number, 색: string) => <>
    <div style={{ position: "absolute", left: 60, top: y, fontSize: 44, color: 색 }}>{글}</div>
    <div style={{ position: "absolute", left: 60, top: y + 64, height: 120, width: 값 * 자, background: 색, borderRadius: 14 }} />
    <div style={{ position: "absolute", left: 90 + 값 * 자, top: y + 82, fontSize: 76, color: 색 }}>{Math.round(값)}%</div></>;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 40, fontSize: 40, color: 먹 }}>부품 20개 · 실제 부품보다 10° 넘게 비뚤어진 겉</div>
    <div style={{ position: "absolute", left: 60, top: 110, fontSize: 44, color: 초, opacity: z }}>실제 부품 = 0% (낮을수록 좋음)</div>
    {줄(210, "칸으로 깎기", b1, 금)}{줄(450, "고친 곡면 깎기", b2, 초)}
  </AbsoluteFill>; };
