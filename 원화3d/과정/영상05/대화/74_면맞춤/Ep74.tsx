import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 74 편 — 판정기준65 · 66(면 맞춤) · 그림이 주인 · 턴테이블 · 값: 기운 판 66 0.99 · ㄱ자 65 0.37 → 66 0.94 · 712 평균 0.853 → 0.854
const 먹 = "rgb(40,40,50)", 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(220,160,30)", 파 = "rgb(60,120,200)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string; 빈?: boolean };
type 표 = { x: number; y: number; w: number; h: number; 색: string; 시작: number };
const 돌림 = ({ 부품, 판들, 표들 = [] }: { 부품: string; 판들: 판[]; 표들?: 표[] }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0");
  const 폭 = 판들.length === 1 ? 620 : 판들.length === 2 ? 480 : 330, 왼 = (1000 - 폭 * 판들.length) / 2;
  return (
    <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
      {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 });
        return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 판들.length === 1 ? 10 : 90, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
          <Img src={staticFile(`ep74/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
          {c.빈 && <div style={{ position: "absolute", left: 0, top: 폭 / 2 - 40, width: 폭, textAlign: "center", fontSize: 60, color: 빨 }}>사라짐</div>}
          {판들.length > 1 && <div style={{ textAlign: "center", fontSize: 46, color: c.색, marginTop: -16 }}>{c.글}</div>}
        </div>; })}
      {표들.map((t, k) => <div key={k} style={{ position: "absolute", left: t.x, top: t.y, width: t.w, height: t.h }}>
        <Circle progress={interpolate(f, [t.시작, t.시작 + 22], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={t.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: t.w, height: t.h }} /></Circle></div>)}
    </AbsoluteFill>
  );
};
export const 판74 = () => <돌림 부품="slant" 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "f66", 글: "면으로 맞춤", 색: 파 }]} />;
export const 막대74 = () => <돌림 부품="bar" 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "f65", 글: "고치기 전", 색: "rgb(160,100,200)" }, { 파일: "f66", 글: "고친 뒤", 색: 파 }]} />;
export const 평균74 = () => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig(); const p = interpolate(f, [8, 40], [0, 1], { ...C, easing: 이징 });
  const 막 = (y: number, 이름: string, v: number, 색: string) => <><div style={{ position: "absolute", left: 40, top: y, height: 110, display: "flex", alignItems: "center", fontSize: 44, color: 먹 }}>{이름}</div>
    <div style={{ position: "absolute", left: 300, top: y, width: 620 * ((v - 0.5) / 0.45) * p, height: 110, borderRadius: 14, background: 색 }} />
    <div style={{ position: "absolute", left: 300 + 620 * ((v - 0.5) / 0.45) * p - 170, top: y, width: 160, height: 110, display: "flex", alignItems: "center", justifyContent: "flex-end", fontSize: 52, color: "white" }}>{(0.5 + (v - 0.5) * p).toFixed(3)}</div></>;
  const 같 = spring({ frame: f - 55, fps, config: { stiffness: 260, damping: 15 } });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 0, top: 70, width: 1000, textAlign: "center", fontSize: 40, color: 회 }}>시험 부품 712 개 평균</div>
    {막(190, "원래", 0.853, 회)}{막(360, "면으로 맞춤", 0.854, 파)}
    <div style={{ position: "absolute", left: 0, top: 545, width: 1000, textAlign: "center", fontSize: 58, color: 빨, opacity: Math.min(Math.max(같, 0) * 2, 1), scale: `${interpolate(같, [0, 1], [1.4, 1])}` }}>거의 그대로</div></AbsoluteFill>;
};
