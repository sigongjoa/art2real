import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";

// 83 편 — 부품 59 컵 · 정답 / 모델 턴테이블(재료83) · 옛 구조: 위 도면만 모델로 · 앞 도면 바닥 점선은 안 들어감 · 바닥이라 본 확률 1 %(확률98)
const 빨 = "rgb(220,50,50)", 초 = "rgb(40,160,80)", 금 = "rgb(200,140,20)", 먹 = "rgb(40,40,50)";
const 글꼴 = "'Malgun Gothic', sans-serif";
const C = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const 이징 = Easing.bezier(0.2, 0, 0, 1);
const 나타 = (f: number, t: number, d = 14) => interpolate(f, [t, t + d], [0, 1], { ...C, easing: 이징 });
// 손그림 동그라미: 둘레를 따라 그려짐
const 동그라미 = ({ x, y, rx, ry, 색, t }: { x: number; y: number; rx: number; ry: number; 색: string; t: number }) => { const f = useCurrentFrame(); const p = 나타(f, t, 18); const L = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2) * 1.1;
  return <svg style={{ position: "absolute", left: 0, top: 0 }} width={1000} height={700}><path d={`M ${x + rx} ${y} A ${rx} ${ry} 0 1 1 ${x + rx - 1} ${y - 8} A ${rx * 1.04} ${ry * 1.06} -8 0 1 ${x + rx + 6} ${y + 10}`} fill="none" stroke={색} strokeWidth={9} strokeLinecap="round" strokeDasharray={L} strokeDashoffset={L * (1 - p)} /></svg>; };
export const 컵83 = () => { const f = useCurrentFrame(); const i = String(Math.floor((f % 96) / 2)).padStart(2, "0");
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {[["cup_truth", "실제 부품", 초], ["cup_model", "모델 결과", 금]].map(([p, g, c], j) => { const a = 나타(f, j * 10); return <div key={p} style={{ position: "absolute", left: 20 + j * 490, top: 30, width: 470, opacity: a, translate: `0px ${(1 - a) * 40}px` }}>
      <Img src={staticFile(`ep83/${p}/${i}.png`)} style={{ width: 470, height: 470 }} />
      <div style={{ textAlign: "center", fontSize: 56, color: c, marginTop: 6 }}>{g}</div></div>; })}
    <동그라미 x={745} y={215} rx={120} ry={85} 색={빨} t={160} />
  </AbsoluteFill>; };
export const 옛길83 = () => { const f = useCurrentFrame(); const 들어감 = interpolate(f, [20, 60], [0, 1], { ...C, easing: 이징 }); const x표 = 나타(f, 150, 12); const 큰 = 나타(f, 200, 16);
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    <div style={{ position: "absolute", left: 40, top: 40, width: 260, opacity: 나타(f, 0) }}><Img src={staticFile("ep83/top.png")} style={{ width: 260, height: 260, border: `6px solid ${먹}`, borderRadius: 12, translate: `${들어감 * 340}px ${들어감 * 300}px`, scale: `${1 - 들어감 * 0.6}`, opacity: 1 - 나타(f, 52, 10) }} /><div style={{ textAlign: "center", fontSize: 44, color: 먹, opacity: 1 - 들어감 }}>위 도면</div></div>
    <div style={{ position: "absolute", left: 330, top: 300, width: 300, height: 260, borderRadius: 28, background: "rgb(243,214,143)", border: `8px solid ${금}`, opacity: 나타(f, 4), display: "flex", alignItems: "center", justifyContent: "center", fontSize: 72, color: "rgb(107,71,4)", gap: 18 }}><Img src={staticFile("ep83/top.png")} style={{ width: 92, height: 92, border: `4px solid ${먹}`, borderRadius: 8, opacity: 나타(f, 56, 8) }} />모델</div>
    <div style={{ position: "absolute", left: 690, top: 40, width: 270, opacity: 나타(f, 70) }}><Img src={staticFile("ep83/orig_front.png")} style={{ width: 270, height: 270, border: `6px solid ${먹}`, borderRadius: 12, imageRendering: "pixelated" }} /><div style={{ textAlign: "center", fontSize: 44, color: 먹 }}>앞 도면</div>
      <div style={{ position: "absolute", left: 14, top: 128, width: 240, height: 44, border: `7px solid ${금}`, borderRadius: 12, opacity: 나타(f, 100) }} /></div>
    <svg style={{ position: "absolute", left: 0, top: 0 }} width={1000} height={700}>
      <path d="M 790 380 C 760 440 710 450 650 445" stroke={먹} strokeWidth={12} fill="none" strokeDasharray="24 16" opacity={나타(f, 110)} />
      <path d={`M ${675} ${395} L ${675 + 95 * x표} ${395 + 95 * x표}`} stroke={빨} strokeWidth={20} strokeLinecap="round" opacity={x표 > 0 ? 1 : 0} />
      <path d={`M ${770} ${395} L ${770 - 95 * x표} ${395 + 95 * x표}`} stroke={빨} strokeWidth={16} strokeLinecap="round" opacity={x표 > 0.5 ? 1 : 0} />
    </svg>
    <div style={{ position: "absolute", left: 760, top: 480, fontSize: 130, color: 빨, opacity: 큰, scale: `${0.6 + 0.4 * 큰}` }}>1%</div>
  </AbsoluteFill>; };
export const 결과83 = () => { const f = useCurrentFrame(); const i = String(Math.floor((f % 96) / 2)).padStart(2, "0");
  return <AbsoluteFill style={{ fontFamily: 글꼴, fontWeight: 700 }}>
    {[["cup_pocket", "고른 결과", 초], ["cup_truth", "실제 부품", 초]].map(([p, g, c], j) => { const a = 나타(f, j * 10); return <div key={p} style={{ position: "absolute", left: 20 + j * 490, top: 30, width: 470, opacity: a, translate: `0px ${(1 - a) * 40}px` }}>
      <Img src={staticFile(`ep83/${p}/${i}.png`)} style={{ width: 470, height: 470 }} />
      <div style={{ textAlign: "center", fontSize: 50, color: c, marginTop: 6 }}>{g}</div></div>; })}
    <div style={{ position: "absolute", left: 0, width: 1000, top: 600, textAlign: "center", fontSize: 54, color: 금, opacity: 나타(f, 160) }}>바닥 한 칸 차이</div>
  </AbsoluteFill>; };
