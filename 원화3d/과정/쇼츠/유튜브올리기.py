"""쇼츠 한 편을 YouTube 에 — social-auto-upload(G:/social-auto-upload) 업로더를 사람이 로그인해 둔 크롬 프로필로 연다.
    G:/social-auto-upload/.venv/Scripts/python 유튜브올리기.py <프로필폴더> <mp4> <제목> <설명> [private|unlisted|public]
프로필: G:/sau_chrome/suhyeok (이수혁). 첫 편은 private 로."""
import sys, asyncio
sys.path.insert(0, "G:/social-auto-upload")
from uploader.youtube_uploader.main import YouTubeVideo
prof, mp4, title, desc = sys.argv[1:5]; vis = sys.argv[5] if len(sys.argv) > 5 else "private"
asyncio.run(YouTubeVideo(title, mp4, [], prof, description=desc, visibility=vis, headless=False).main())
