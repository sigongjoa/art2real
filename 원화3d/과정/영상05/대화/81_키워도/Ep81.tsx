import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 81 편 — 판정기준90 · 91 · 어려움 467 정답 · 판0(이전) · 넓은숨은(지금) · 어려움 20 반 칸 F 0.69 → 0.68 · 학습 부품 층 맞음 70 % · 시험 69 % · 외우기 64 개 300 에폭 81 %
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
        <Img src={staticFile(`ep81/${부품}_${c.파일}/${i}.png`)} style={{ width: 폭, height: 폭 }} />
        <div style={{ textAlign: "center", fontSize: 40, color: c.색, marginTop: -30 }}>{c.글}</div>
        {c.점 && <div style={{ textAlign: "center", fontSize: 66, color: c.점색, opacity: q }}>{c.점}</div>}</div>; })}
  </AbsoluteFill>;
};
export const 부품81 = () => <돌림 부품="part" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "old", 글: "모델 결과", 색: 금 }]} />;
export const 비교81 = () => <돌림 부품="part" 판들={[{ 파일: "truth", 글: "실제 부품", 색: 초 }, { 파일: "old", 글: "이전 모델", 색: 금 }, { 파일: "new", 글: "키우고 점선", 색: 보 }]} />;
const 막대 = ({ 제목, 아래, 줄들, 단위 }: { 제목: string; 아래: string; 줄들: [string, number, string][]; 단위: string }) => { const f = useCurrentFrame(); const a = interpolate(f, [0, 16], [0, 1], { ...C, easing: 이징 });
  const 최 = Math.max(...줄들.map((z) => z[1]));
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 30, fontSize: 40, color: 먹 }}>{제목}</div>
    <div style={{ position: "absolute", left: 60, top: 90, fontSize: 34, color: 회 }}>{아래}</div>
    {줄들.map(([글, 값, 색], j) => { const t = 20 + j * 40, y = 170 + j * 250, b = interpolate(f, [t, t + 30], [0, 값], { ...C, easing: 이징 }); return <div key={글}>
      <div style={{ position: "absolute", left: 60, top: y, fontSize: 44, color: 색 }}>{글}</div>
      <div style={{ position: "absolute", left: 60, top: y + 62, height: 110, width: b / 최 * 620, background: 색, borderRadius: 12 }} />
      <div style={{ position: "absolute", left: 90 + b / 최 * 620, top: y + 76, fontSize: 72, color: 색 }}>{단위 === "%" ? Math.round(b) + "%" : b.toFixed(2)}</div></div>; })}
  </AbsoluteFill>; };
export const 막대81 = () => <막대 제목="어려운 부품 20개 · 실제 모양에 붙은 정도" 아래="높을수록 좋음" 단위="" 줄들={[["이전 모델", 0.69, 금], ["키우고 점선", 0.68, 빨]]} />;
export const 외움81 = () => <막대 제목="깊이 층을 맞힌 비율" 아래="배운 부품과 처음 보는 부품" 단위="%" 줄들={[["이미 배운 부품", 70, 금], ["처음 보는 부품", 69, 회]]} />;
export const 외우기81 = () => <막대 제목="부품 64개만 300번 반복" 아래="같은 64개로 채점 · 100%면 다 외움" 단위="%" 줄들={[["다 외우면", 100, 회], ["모델", 81, 빨]]} />;
