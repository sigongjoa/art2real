import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 76 편 — 실제76 · 정답 없는 GPT · Gemini 3면도 → 판0 32 단계 · 위 = 입력 그림 · 아래 = 턴테이블 · 숫자 없음
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string };
type 표 = { x: number; y: number; w: number; h: number; 색: string; 시작: number };
const 동그라미 = ({ 표들 }: { 표들: 표[] }) => { const f = useCurrentFrame();
  return <>{표들.map((t, k) => <div key={k} style={{ position: "absolute", left: t.x, top: t.y, width: t.w, height: t.h }}>
    <Circle progress={interpolate(f, [t.시작, t.시작 + 22], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={t.색} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: t.w, height: t.h }} /></Circle></div>)}</>; };
const 그림돌림 = ({ 부품, 판들, 표들 = [], 그림 = true }: { 부품: string; 판들: 판[]; 표들?: 표[]; 그림?: boolean }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0");
  const g = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 }); const 폭 = 판들.length === 1 ? 420 : 430, 왼 = (1000 - 폭 * 판들.length) / 2, 위 = 그림 ? 215 : 80;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {그림 && <Img src={staticFile(`ep76/${부품}_그림.png`)} style={{ position: "absolute", left: 40, top: 20, width: 920, height: 190, objectFit: "contain", opacity: g }} />}
    {판들.map((c, j) => { const p = interpolate(f, [8 + j * 10, 28 + j * 10], [0, 1], { ...C, easing: 이징 });
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 위, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep76/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 44, color: c.색, marginTop: -18 }}>{c.글}</div></div>; })}
    <동그라미 표들={표들} />
  </AbsoluteFill>;
};
export const 투구76 = () => <그림돌림 부품="helmet" 판들={[{ 파일: "ai", 글: "모델 결과", 색: 금 }]} />;
export const 투구비교76 = () => <그림돌림 부품="helmet" 그림={false} 판들={[{ 파일: "frame", 글: "세 윤곽 겹침", 색: 회 }, { 파일: "ai", 글: "모델 결과", 색: 금 }]} />;
export const 브래킷76 = () => <그림돌림 부품="bracket" 판들={[{ 파일: "ai", 글: "모델 결과", 색: 초 }]} />;
export const 어깨76 = () => <그림돌림 부품="shoulder" 판들={[{ 파일: "ai", 글: "모델 결과", 색: 금 }]} />;
// 그림비교: 배운 도면(학습 데이터 한 장) 과 투구 도면 · 옆 그림에 빨간 동그라미
export const 그림비교76 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 }), b = interpolate(f, [24, 40], [0, 1], { ...C, easing: 이징 });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 50, top: 30, fontSize: 44, color: 초, opacity: a }}>모델이 배운 도면</div>
    <Img src={staticFile("ep76/learned_그림.png")} style={{ position: "absolute", left: 50, top: 90, width: 900, height: 230, objectFit: "contain", opacity: a }} />
    <div style={{ position: "absolute", left: 50, top: 360, fontSize: 44, color: 빨, opacity: b }}>GPT가 그린 투구 도면</div>
    <Img src={staticFile("ep76/helmet_그림.png")} style={{ position: "absolute", left: 50, top: 420, width: 900, height: 260, objectFit: "contain", opacity: b }} />
    <동그라미 표들={[{ x: 590, y: 425, w: 230, h: 250, 색: 빨, 시작: 160 }]} />
  </AbsoluteFill>; };
