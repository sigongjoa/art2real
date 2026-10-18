import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 79 편 — 판정기준83 · 딱정벌레(252) · 기운 고리(104 · 정답 깊이 0.97 · 모델 0.30) · 반 칸 F 쉬운 20 모델 0.78 · 복잡 20 모델 0.69 · 복잡 20 정답 깊이 0.88
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 파 = "rgb(60,120,200)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string; 점?: string; 점색?: string };
const 돌림 = ({ 부품, 판들, 제목 }: { 부품: string; 판들: 판[]; 제목?: string }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0"); const 폭 = 판들.length === 2 ? 470 : 330, 왼 = (1000 - 폭 * 판들.length) / 2;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {제목 && <div style={{ position: "absolute", left: 0, width: 1000, top: 24, textAlign: "center", fontSize: 36, color: 먹 }}>{제목}</div>}
    {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 }), q = interpolate(f, [40 + j * 15, 55 + j * 15], [0, 1], C);
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 판들.length === 2 ? 60 : 110, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep79/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 40, color: c.색, marginTop: -30 }}>{c.글}</div>
        {c.점 && <div style={{ textAlign: "center", fontSize: 66, color: c.점색, opacity: q }}>{c.점}</div>}</div>; })}
  </AbsoluteFill>;
};
export const 벌레79 = () => <돌림 부품="bug" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "model", 글: "모델 결과", 색: 금 }]} />;
export const 벌레천장79 = () => <돌림 부품="bug" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "ceil", 글: "정답 깊이로 깎기", 색: 파 }]} />;
export const 고리79 = () => <돌림 부품="ring" 제목="겉이 실제 모양에 붙은 정도 (높을수록 좋음)" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "ceil", 글: "정답 깊이(최고)", 색: 파, 점: "0.97", 점색: 파 }, { 파일: "model", 글: "모델", 색: 금, 점: "0.30", 점색: 빨 }]} />;
const 판 = ({ 그림, 제목, 색 }: { 그림: string; 제목: string; 색: string }) => { const f = useCurrentFrame(); const a = interpolate(f, [0, 18], [0, 1], { ...C, easing: 이징 });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 30, textAlign: "center", fontSize: 44, color: 색 }}>{제목}</div>
    <Img src={staticFile(`ep79/${그림}.png`)} style={{ position: "absolute", left: 20, top: 110, width: 960, height: 480 }} />
  </AbsoluteFill>; };
export const 쉬움79 = () => <판 그림="easy" 제목="지금까지 시험한 부품 (20개 중 8개)" 색={회} />;
export const 어려움79 = () => <판 그림="hard" 제목="복잡한 것만 모은 부품 (20개 중 8개)" 색={빨} />;
// 막대: 반 칸 안에 맞는 겉 · 높을수록 좋음
export const 막대79 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const 줄 = (y: number, 글: string, 값: number, 색: string, t: number) => { const b = interpolate(f, [t, t + 30], [0, 값], { ...C, easing: 이징 }); return <>
    <div style={{ position: "absolute", left: 60, top: y, fontSize: 40, color: 색 }}>{글}</div>
    <div style={{ position: "absolute", left: 60, top: y + 56, height: 90, width: b * 700, background: 색, borderRadius: 12 }} />
    <div style={{ position: "absolute", left: 80 + b * 700, top: y + 64, fontSize: 64, color: 색 }}>{b.toFixed(2)}</div></>; };
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 30, fontSize: 38, color: 먹 }}>겉이 실제 모양에 붙은 정도 (높을수록 좋음)</div>
    {줄(100, "쉬운 20개 · 모델", .78, 회, 20)}{줄(290, "복잡한 20개 · 모델", .69, 빨, 60)}{줄(480, "복잡한 20개 · 정답 깊이(최고)", .88, 파, 100)}
  </AbsoluteFill>; };
