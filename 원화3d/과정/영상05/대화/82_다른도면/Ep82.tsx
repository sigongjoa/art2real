import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 82 편 — 부품 59 컵 · 판0 이 바닥을 뚫음 · 원 경계는 잡음(확률) · 바닥 16 층 확률 0.01 · 입력에 앞 도면 바닥선 없음 · 후보95 · 구조99 다시 투영 맞대기(포켓 15 0.25 · 16 0.23 · 관통 0.20 · 31 0.15)
const 회 = "rgb(130,130,140)", 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
type 표 = { 글: string; 색: string; x: number; y: number; t: number; 크?: number };
const 나타 = (f: number, t: number) => interpolate(f, [t, t + 14], [0, 1], { ...C, easing: 이징 });
const 표들 = (f: number, 표: 표[]) => 표.map((m) => { const p = 나타(f, m.t); return <div key={m.글} style={{ position: "absolute", left: m.x, top: m.y, fontSize: m.크 ?? 64, color: m.색, opacity: p, scale: `${0.7 + 0.3 * p}`, background: "rgba(255,255,255,0.85)", padding: "4px 16px", borderRadius: 14, border: `6px solid ${m.색}` }}>{m.글}</div>; });
const 그림 = ({ 파일, 제목, 위, 표 }: { 파일: string; 제목: string; 위: number; 표: 표[] }) => { const f = useCurrentFrame(); const a = 나타(f, 0);
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 26, textAlign: "center", fontSize: 44, color: 먹, opacity: a }}>{제목}</div>
    <Img src={staticFile(`ep82/${파일}`)} style={{ position: "absolute", left: 30, width: 940, top: 위, opacity: a, translate: `0px ${(1 - a) * 30}px` }} />
    {표들(f, 표)}</AbsoluteFill>; };
const 둘 = ({ 표 }: { 표: 표[] }) => { const f = useCurrentFrame();
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {[["truth_cut.png", "실제 부품", 초], ["model_cut.png", "모델 결과", 금]].map(([p, g, c], j) => { const a = 나타(f, j * 10); return <div key={p} style={{ position: "absolute", left: 20 + j * 490, top: 40, width: 470, opacity: a, translate: `0px ${(1 - a) * 40}px` }}>
      <Img src={staticFile(`ep82/${p}`)} style={{ width: 470, height: 470, objectFit: "contain" }} />
      <div style={{ textAlign: "center", fontSize: 48, color: c }}>{g}</div></div>; })}
    <div style={{ position: "absolute", left: 0, width: 1000, top: 610, textAlign: "center", fontSize: 32, color: 회 }}>반으로 잘라 속을 보여 줌</div>
    {표들(f, 표)}</AbsoluteFill>; };
export const 컵82 = () => <둘 표={[{ 글: "바닥이 없음", 색: 빨, x: 590, y: 330, t: 150 }]} />;
export const 확률82 = () => <그림 파일="prob.png" 제목="모델이 낸 확률 · 위에서 본 컵" 위={150} 표={[{ 글: "원 경계는 정확", 색: 초, x: 40, y: 450, t: 40, 크: 54 }, { 글: "바닥일 확률 1%", 색: 빨, x: 330, y: 560, t: 150, 크: 58 }]} />;
export const 입력82 = () => <그림 파일="input.png" 제목="모델이 받은 입력" 위={170} 표={[{ 글: "깊이 칸은 전부 0층", 색: 빨, x: 300, y: 450, t: 30, 크: 52 }, { 글: "앞 도면 바닥선은 안 들어감", 색: 빨, x: 150, y: 560, t: 150, 크: 52 }]} />;
export const 후보82 = () => <그림 파일="cand.png" 제목="앞 · 옆 도면의 선 높이 = 깊이 후보" 위={130} 표={[{ 글: "후보 0 · 15 · 16 · 31층", 색: 초, x: 240, y: 520, t: 150, 크: 58 }]} />;
const 셋 = () => { const f = useCurrentFrame();
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 0, width: 1000, top: 26, textAlign: "center", fontSize: 44, color: 먹, opacity: 나타(f, 0) }}>후보마다 깎고 앞에서 다시 그리기</div>
    {[["orig_front.png", "원래 앞 도면", 먹, 0], ["re_pocket.png", "포켓 16층", 초, 40], ["re_through.png", "관통", 빨, 70]].map(([p, g, c, t], j) => { const a = 나타(f, t as number); return <div key={p as string} style={{ position: "absolute", left: 25 + j * 325, top: 130, width: 300, opacity: a, translate: `0px ${(1 - a) * 40}px` }}>
      <Img src={staticFile(`ep82/${p}`)} style={{ width: 300, height: 300, imageRendering: "pixelated", border: `6px solid ${c}`, borderRadius: 10 }} />
      <div style={{ textAlign: "center", fontSize: 48, color: c as string, marginTop: 10 }}>{g}</div></div>; })}
    {표들(f, [{ 글: "바닥 점선이 있나?", 색: 금, x: 270, y: 540, t: 150, 크: 58 }])}</AbsoluteFill>; };
export const 투영82 = () => <셋 />;
const 막대 = ({ 제목, 아래, 줄들 }: { 제목: string; 아래: string; 줄들: [string, number, string][] }) => { const f = useCurrentFrame(); const a = 나타(f, 0); const 최 = Math.max(...줄들.map((z) => z[1]));
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700, opacity: a }}>
    <div style={{ position: "absolute", left: 60, top: 30, fontSize: 42, color: 먹 }}>{제목}</div>
    <div style={{ position: "absolute", left: 60, top: 92, fontSize: 32, color: 회 }}>{아래}</div>
    {줄들.map(([글, 값, 색], j) => { const t = 20 + j * 25, y = 160 + j * 128, b = interpolate(f, [t, t + 30], [0, 값], { ...C, easing: 이징 }); return <div key={글}>
      <div style={{ position: "absolute", left: 60, top: y + 18, fontSize: 44, color: 색, width: 260 }}>{글}</div>
      <div style={{ position: "absolute", left: 330, top: y, height: 96, width: b / 최 * 470, background: 색, borderRadius: 12 }} />
      <div style={{ position: "absolute", left: 350 + b / 최 * 470, top: y + 10, fontSize: 64, color: 색 }}>{b.toFixed(2)}</div></div>; })}
  </AbsoluteFill>; };
export const 막대82 = () => <막대 제목="다시 그린 도면이 원래 도면과 맞는 정도" 아래="높을수록 잘 맞음 · 정답 3D 없이 잼" 줄들={[["포켓 15층", 0.25, 초], ["포켓 16층", 0.23, 초], ["관통", 0.2, 빨], ["포켓 31층", 0.15, 회]]} />;
