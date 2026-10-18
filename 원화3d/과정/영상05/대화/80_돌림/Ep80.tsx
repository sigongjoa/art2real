import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 80 편 — 판정기준84 · 85(고친 판) · 톱니 축 635 모델 0.58 · 도면만 회전 0.81 · 돌기 원판 206 모델 0.74 · 도면만 0.59 · 어려운 회전 부품 10 개 10° 넘게 비뚤어진 겉 35 % → 24 % · 붙은 정도 0.71 → 0.73
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 보 = "rgb(140,90,190)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string; 점?: string; 점색?: string };
const 돌림 = ({ 부품, 판들, 제목 }: { 부품: string; 판들: 판[]; 제목?: string }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0"); const 폭 = 판들.length === 2 ? 470 : 330, 왼 = (1000 - 폭 * 판들.length) / 2;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {제목 && <div style={{ position: "absolute", left: 0, width: 1000, top: 24, textAlign: "center", fontSize: 34, color: 먹 }}>{제목}</div>}
    {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 }), q = interpolate(f, [40 + j * 15, 55 + j * 15], [0, 1], C);
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 판들.length === 2 ? 60 : 100, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep80/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 40, color: c.색, marginTop: -30 }}>{c.글}</div>
        {c.점 && <div style={{ textAlign: "center", fontSize: 66, color: c.점색, opacity: q }}>{c.점}</div>}</div>; })}
  </AbsoluteFill>;
};
const 제 = "겉이 실제 모양에 붙은 정도 (높을수록 좋음)";
export const 톱니80 = () => <돌림 부품="gear" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "model", 글: "모델 결과", 색: 금 }]} />;
export const 비교80 = () => <돌림 부품="gear" 제목={제} 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "model", 글: "모델", 색: 금, 점: "0.58", 점색: 빨 }, { 파일: "rev", 글: "도면만 돌림", 색: 보, 점: "0.81", 점색: 초 }]} />;
export const 돌기80 = () => <돌림 부품="boss" 제목={제} 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "model", 글: "모델", 색: 금, 점: "0.74", 점색: 회 }, { 파일: "rev", 글: "도면만 돌림", 색: 보, 점: "0.59", 점색: 빨 }]} />;
export const 강좌80 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 18], [0, 1], { ...C, easing: 이징 });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 26, textAlign: "center", fontSize: 40, color: 먹 }}>유튜브 CAD 강좌 13편</div>
    <Img src={staticFile("ep80/tutorial.png")} style={{ position: "absolute", left: 120, top: 90, width: 760, height: 428, borderRadius: 12 }} />
    <div style={{ position: "absolute", left: 0, width: 1000, top: 560, textAlign: "center", fontSize: 44, color: 초, opacity: interpolate(f, [30, 50], [0, 1], C) }}>원으로 보이는 면에서 몸통부터 돌린다</div>
  </AbsoluteFill>; };
// 막대: 어려운 회전 부품 10 개 · 10° 넘게 비뚤어진 겉(낮을수록 좋음)
export const 막대80 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const 줄 = (y: number, 글: string, 값: number, 색: string, t: number) => { const b = interpolate(f, [t, t + 30], [0, 값], { ...C, easing: 이징 }); return <>
    <div style={{ position: "absolute", left: 60, top: y, fontSize: 42, color: 색 }}>{글}</div>
    <div style={{ position: "absolute", left: 60, top: y + 60, height: 110, width: b * 19, background: 색, borderRadius: 12 }} />
    <div style={{ position: "absolute", left: 90 + b * 19, top: y + 74, fontSize: 72, color: 색 }}>{Math.round(b)}%</div></>; };
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 30, fontSize: 38, color: 먹 }}>어려운 회전 부품 10개 · 10° 넘게 비뚤어진 겉</div>
    <div style={{ position: "absolute", left: 60, top: 90, fontSize: 36, color: 초 }}>낮을수록 좋음</div>
    {줄(170, "모델", 35, 금, 20)}{줄(420, "도면만 돌림", 24, 보, 60)}
  </AbsoluteFill>; };
