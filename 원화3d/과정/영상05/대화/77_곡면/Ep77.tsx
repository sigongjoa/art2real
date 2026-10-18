import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Circle } from "@remotion/rough-notation";

// 77 편 — 곡선77 · 둥근 고리(시험 18) 턴테이블 · 값: 학습 1000 곡면 · 기운 면 넓이 중앙값 52 % · 곡면 많음 314 개 울퉁 천장 4.3 % · 모델 7.0 %
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 파 = "rgb(60,120,200)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 판 = { 파일: string; 글: string; 색: string };
const 돌림 = ({ 판들, 동 }: { 판들: 판[]; 동?: boolean }) => {
  const f = useCurrentFrame(); const i = String(Math.floor((f % 150) / 150 * 48)).padStart(2, "0");
  const 폭 = 판들.length === 1 ? 620 : 330, 왼 = (1000 - 폭 * 판들.length) / 2;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {판들.map((c, j) => { const p = interpolate(f, [j * 10, j * 10 + 20], [0, 1], { ...C, easing: 이징 });
      return <div key={c.파일} style={{ position: "absolute", left: 왼 + j * 폭, top: 판들.length === 1 ? 10 : 120, width: 폭, opacity: p, translate: `0px ${(1 - p) * 40}px` }}>
        <Img src={staticFile(`ep77/ring_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        {판들.length > 1 && <div style={{ textAlign: "center", fontSize: 42, color: c.색, marginTop: -10 }}>{c.글}</div>}</div>; })}
    {동 && <div style={{ position: "absolute", left: 250, top: 120, width: 500, height: 420 }}>
      <Circle progress={interpolate(f, [50, 72], [0, 1], { ...C, easing: Easing.inOut(Easing.quad) })} color={빨} strokeWidth={7} padding={6} seed={5 + Math.floor(f / 3)} roughness={1.8}><div style={{ width: 500, height: 420 }} /></Circle></div>}
  </AbsoluteFill>;
};
export const 고리77 = () => <돌림 동 판들={[{ 파일: "model", 글: "모델 결과", 색: 금 }]} />;
export const 비교77 = () => <돌림 판들={[{ 파일: "truth", 글: "정답", 색: 초 }, { 파일: "ceil", 글: "정답 깊이로 깎기", 색: 파 }, { 파일: "model", 글: "모델", 색: 금 }]} />;
// 넓이: 모델이 배운 부품 겉넓이 중 곡면 · 기운 면 52 %
export const 넓이77 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 }), p = interpolate(f, [20, 60], [0, 52], { ...C, easing: 이징 });
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 70, top: 90, fontSize: 46, color: 먹 }}>모델이 배운 부품 1,000개의 겉넓이</div>
    <div style={{ position: "absolute", left: 70, top: 220, width: 860, height: 170, background: "rgb(225,225,230)", borderRadius: 20, overflow: "hidden" }}>
      <div style={{ width: `${p / 100 * 860}px`, height: 170, background: 금 }} /></div>
    <div style={{ position: "absolute", left: 90, top: 250, fontSize: 90, color: "white" }}>{Math.round(p)}%</div>
    <div style={{ position: "absolute", left: 70, top: 420, fontSize: 44, color: 금 }}>■ 곡면 · 비스듬한 면</div>
    <div style={{ position: "absolute", left: 560, top: 420, fontSize: 44, color: 회 }}>■ 반듯한 평면</div>
  </AbsoluteFill>; };
// 막대: 곡면 많은 부품 314 개 · 평평해야 할 곳이 꺾인 비율 · 정답 깊이 4.3 % · 모델 7.0 % (= 4.3 + 2.7)
export const 막대77 = () => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const b1 = interpolate(f, [20, 50], [0, 4.3], { ...C, easing: 이징 }), b2 = interpolate(f, [60, 90], [0, 4.3], { ...C, easing: 이징 }), b3 = interpolate(f, [100, 130], [0, 2.7], { ...C, easing: 이징 }), 자 = 100;
  const 줄 = (y: number, 글: string, 색: string, 값: React.ReactNode, 막: React.ReactNode) => <>
    <div style={{ position: "absolute", left: 60, top: y, fontSize: 40, color: 색 }}>{글}</div>
    <div style={{ position: "absolute", left: 60, top: y + 60, height: 110, display: "flex" }}>{막}</div>
    <div style={{ position: "absolute", left: 800, top: y + 70, fontSize: 70, color: 색 }}>{값}</div></>;
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 40, fontSize: 36, color: 먹 }}>곡면이 많은 부품 314개 · 평평해야 할 곳이 꺾인 비율</div>
    {줄(140, "정답 깊이로 깎기", 파, `${b1.toFixed(1)}%`, <div style={{ width: b1 * 자, background: 파, borderRadius: 12 }} />)}
    {줄(390, "모델", 금, `${(b2 + b3).toFixed(1)}%`, <><div style={{ width: b2 * 자, background: 파, borderRadius: "12px 0 0 12px" }} /><div style={{ width: b3 * 자, background: 빨, borderRadius: "0 12px 12px 0" }} /></>)}
    <div style={{ position: "absolute", left: 60 + 4.3 * 자, top: 580, fontSize: 40, color: 빨, opacity: interpolate(f, [120, 135], [0, 1], C) }}>모델 몫 2.7%p</div>
  </AbsoluteFill>; };
