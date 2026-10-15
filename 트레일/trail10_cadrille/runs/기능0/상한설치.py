# -*- coding: utf-8 -*-
# sitecustomize.py(메모리 상한)를 이 프로젝트가 쓰는 파이썬마다 site-packages 에 복사하고, 1 GB 상한에서 2 GB 를 잡으면 막히는지 확인한다 · 10-15
# 사용: python 상한설치.py   (원본을 고치면 다시 돌린다)
import os, shutil, subprocess
원 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitecustomize.py")
파이썬 = ["G:/art2real/트레일/trail10_cadrille/venv/Scripts/python.exe", "G:/art2real/트레일/trail11_zerotocad/venv/Scripts/python.exe", "G:/art2real/out/tts/melo/Scripts/python.exe", "G:/art2real/out/tts/chatterbox/Scripts/python.exe",
       "C:/Users/zesky/AppData/Local/Programs/Python/Python311/python.exe", "C:/Users/zesky/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe"]
시험 = "import os\ntry: bytearray(2 * 2**30); print('안 막힘', os.environ.get('ART_MEM_CAPPED'))\nexcept MemoryError: print('막힘', os.environ.get('ART_MEM_CAPPED'))"
for p in 파이썬:
    if not os.path.exists(p): print("없음", p); continue
    환 = {k: v for k, v in os.environ.items() if k not in ("ART_MEM_CAPPED", "ART_MEM_GB")}
    물음 = "import site; print(site.getusersitepackages())" if "WindowsApps" in p else "import sysconfig; print(sysconfig.get_paths()['purelib'])"   # 스토어판은 설치 폴더가 읽기 전용 → 사용자 site
    곳 = subprocess.run([p, "-c", 물음], capture_output=True, text=True, env=환).stdout.strip()
    os.makedirs(곳, exist_ok=True); shutil.copy(원, os.path.join(곳, "sitecustomize.py"))
    r = subprocess.run([p, "-c", 시험], capture_output=True, text=True, env=dict(환, ART_MEM_GB="1")).stdout.strip()
    print(("ok " if r.startswith("막힘") else "실패 ") + r, "←", 곳)
