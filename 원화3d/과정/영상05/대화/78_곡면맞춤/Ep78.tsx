import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 78 편 — 판정기준79 · 80 · 비누 모양 부품(시험 82) · 옛 점수(다시 그린 선) 칸 0.86 · 맞춤 0.67 · 정답에 가까운 연속 0.75 · 새 자(10° 넘게 기운 겉) 20 부품 35 % → 24 %
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 파 = "rgb(60,120,200)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string; 점?: string; 점색?: string };
const 돌림 = ({ 판들 }: { 판들: 판[] }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0"); const 폭 = 480, 왼 = (1000 - 폭 * 판들.length) / 2;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 }), q = interpolate(f, [40 + j * 15, 55 + j * 15], [0, 1], C);
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 40, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep78/soap_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 44, color: c.색, marginTop: -30 }}>{c.글}</div>
        {c.점 && <div style={{ textAlign: "center", fontSize: 72, color: c.점색, opacity: q, marginTop: 6 }}>{c.점}</div>}</div>; })}
  </AbsoluteFill>;
};
export const 비누78 = () => <돌림 판들={[{ 파일: "cell", 글: "칸으로 깎기", 색: 금, 점: "0.86", 점색: 회 }, { 파일: "fit", 글: "곡면 맞춰 깎기", 색: 금, 점: "0.67", 점색: 빨 }]} />;
export const 자고장78 = () => <돌림 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "smooth", 글: "거의 같은 3D", 색: 파, 점: "0.75", 점색: 빨 }]} />;
// 막대: 부품 20 개 · 정답보다 10° 넘게 비뚤어진 겉 · 칸 35 % · 곡면 맞춤 24 %
export const 막대78 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const b1 = interpolate(f, [30, 60], [0, 35], { ...C, easing: 이징 }), b2 = interpolate(f, [70, 100], [0, 24], { ...C, easing: 이징 }), 자 = 19, z = interpolate(f, [10, 24], [0, 1], C);
  const 줄 = (y: number, 글: string, 값: number, 색: string) => <>
    <div style={{ position: "absolute", left: 60, top: y, fontSize: 44, color: 색 }}>{글}</div>
    <div style={{ position: "absolute", left: 60, top: y + 64, height: 120, width: 값 * 자, background: 색, borderRadius: 14 }} />
    <div style={{ position: "absolute", left: 90 + 값 * 자, top: y + 82, fontSize: 76, color: 색 }}>{Math.round(값)}%</div></>;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 40, fontSize: 40, color: 먹 }}>부품 20개 · 실제 부품보다 10° 넘게 비뚤어진 겉</div>
    <div style={{ position: "absolute", left: 60, top: 110, fontSize: 44, color: 초, opacity: z }}>실제 부품 = 0% (낮을수록 좋음)</div>
    {줄(210, "칸으로 깎기", b1, 금)}{줄(450, "곡면 맞춰 깎기", b2, 초)}
  </AbsoluteFill>; };
