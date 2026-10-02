from PIL import Image, ImageDraw, ImageFont
B=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',30); R=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24); S=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
def sheet(title, items, out):
    W,IH,CH=900,520,190; rows=(len(items)+1)//2
    s=Image.new('RGB',(W*2+30,90+rows*(IH+CH+20)),(250,249,246)); d=ImageDraw.Draw(s)
    d.text((20,25),title,fill=(20,20,30),font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',40))
    for i,(f,t,lines,src) in enumerate(items):
        x=10+(i%2)*(W+10); y=90+(i//2)*(IH+CH+20)
        d.rectangle([x,y,x+W,y+IH+CH],fill='white',outline=(210,210,210))
        im=Image.open(f).convert('RGB'); im.thumbnail((W-20,IH-20)); s.paste(im,(x+(W-im.width)//2,y+10+(IH-20-im.height)//2))
        d.text((x+15,y+IH+8),'%d. %s'%(i+1,t),fill=(150,40,30),font=B)
        for k,l in enumerate(lines): d.text((x+15,y+IH+52+k*34),l,fill=(30,30,40),font=R)
        d.text((x+15,y+IH+CH-30),src,fill=(120,120,130),font=S)
    s.save(out,quality=88)
sheet('교재 예시 ① 지온 — 덩어리로 읽는다 (화가 · 원형사까지)',[
 ('crop_지온01c.png','지온 만들기',['단면 모서리 · 대칭 · 크기 변화 · 축만 바꾸면','원통이 쐐기 · 뿔 · 휜 관으로 — 36 가지 덩어리'],'Biederman 1987, Fig 7 부근 p8'),
 ('crop_지온06.png','숫자 둘로 고르는 덩어리',['초이차곡면: 지수 두 개만 바꿔','상자 ↔ 공 ↔ 별 모양을 연속으로 오간다'],'Barr 1981, Fig 7 p5'),
 ('crop_지온03.png','같은 윤곽, 다른 부품',['술잔으로 보면 받침 · 줄기 · 그릇,','얼굴로 보면 이마 · 코 · 입술 · 턱 — 무엇이 앞이냐에 따라'],'Hoffman & Richards 1984, Fig 12 p18'),
 ('crop_지온05.png','어디서 자르나',['오목한 점에서 자르고(a),','같은 점이면 짧은 자르기(c)를 고른다'],'Hoffman, Parts and Wholes, Fig 3 p5'),
 ('crop_지온01.png','오목부 선을 지우면 — 못 알아본다',['덩어리를 나누는 오목한 곳의 윤곽이 지워졌다','(정답: 손전등)'],'Biederman 1987, Fig 25 p28'),
 ('crop_지온01b.png','같은 만큼 판으로 가리면 — 알아본다',['가림 판 뒤는 눈이 이어 붙인다 = 아모달','지온 장과 아모달 장을 잇는 다리'],'Biederman 1987, Fig 26 p29'),
 ('crop_지온18.png','점토 개 → 상자 템플릿 → 움직임',['손으로 빚은 점토를 스캔해 관절 상자에 맞추면','그대로 애니메이션할 수 있다'],'Princeton CS597D 2003, p35 (Anderson 외)'),
 ('crop_지온22.png','머리를 상자 면으로 잡는다',['얼굴을 그리기 전에 머리를 상자처럼 깎아','앞 · 옆 · 위 면부터 정한다'],'Bridgman 1920, Constructive Anatomy p127'),
 ('crop_지온24.png','단면이 뒤쪽을 알려 준다',['목 · 어깨 · 가슴 · 허리 · 골반 수평 단면을 겹쳐','「보이는 것의 반대편」을 짐작한다'],'Vanderpoel 1907, Plate XXII p89'),
],'교재예시_1_지온.jpg')
sheet('교재 예시 ② 아모달 · 깊이 — 가려진 곳과 안 보이는 깊이',[
 ('crop_아모달11.png','깊이를 바꿔도 정면은 같다',['같은 얼굴을 깊이 배율만 바꾸고 조명을 맞추면','정면 음영이 같다 — 옆(오른쪽 열)에서만 드러난다'],'Belhumeur 외 1999, Fig 2 p4 (람베르트 · 정사영 조건)'),
 ('crop_아모달10.png','한 선화, 여러 해석',['같은 집 선화에 맞는 선 라벨링이 넷 —','어느 모서리가 볼록 · 오목 · 가림인지 하나로 안 정해진다'],'Malik 1987, Fig 31 p27'),
 ('crop_아모달01.png','이어지는 윤곽 · 안 이어지는 윤곽',['a–c: 매끈하게 이을 수 있어 하나로 보인다','d–f: 꺾이거나 되돌아와야 해서 따로 보인다'],'Kellman & Shipley 1991, Fig 23 p18'),
 ('crop_아모달04.png','가려진 곳은 마를 수도 뚱뚱할 수도',['같은 그림의 가린 부분이','(a) 마른 꼴 · (b) 뚱뚱한 꼴 둘 다 말이 된다'],'Tse 1999, Fig 10 p14'),
 ('crop_아모달04b.png','선 하나 없이도 「관」',['음영 · 무늬가 없어도 벌레는 둥근 관으로 보인다','— 눈은 윤곽이 아니라 덩어리를 채운다'],'Tse 1999, Fig 11 p14'),
 ('crop_아모달06.png','단순하게 vs 대칭으로',['A0 는 어느 규칙이든 원(A1)으로 채워지지만','B0 는 국소 이음(B1)과 대칭(B2)이 갈린다'],'Thielen 외 2019, Fig 2 p7 (Sekuler 1994)'),
 ('crop_아모달07.png','가림이 보이는 부분까지 바꾼다',['삼각형에 꼭짓점이 가린 육각형(A)은','안 가린 것(C)보다 비뚤어 보인다'],'Gerbino 2020, Fig 6 p13'),
 ('crop_아모달12.png','선 몇 개가 입체를 바꾼다',['윤곽만(왼) vs 「거의 윤곽」 선을 더한 것(오른) —','콧등 · 볼의 선이 덩어리를 읽게 한다'],'DeCarlo 외 2003, Fig 1 p1'),
 ('crop_아모달14.png','사람마다 다르게 채운다',['파랑 = 보이는 선 · 빨강 = 주석자가 그은 가려진 선','오른쪽 · 아래로 갈수록 가림↑ · 의견 일치↓'],'Zhu 외 2017, Fig 9 p7'),
 ('crop_아모달16.png','AI 가 채운 가려진 곳',['얼룩말 · 사람 · 잎을 통째로 그려 낸다 —','샘플마다 답이 다르고(Fig 8) 상식 실패도 있다(Fig 9)'],'pix2gestalt 2024, Fig 7–9 p8'),
 ('crop_아모달22.png','애니 일러스트를 겹으로',['한 장 → 머리카락 · 얼굴 · 옷 부위 레이어(가려진 곳 채움)','→ 그리는 순서 지도 → 새 포즈 (깊이 mm 는 아님)'],'See-through 2026, Fig 1 p1'),
],'교재예시_2_아모달.jpg')
