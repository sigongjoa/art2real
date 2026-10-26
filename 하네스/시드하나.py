# 코드생성 판의 시드 하나만 돎 — 시드를 GPU 마다 따로 띄워 나란히(10-26 152: 시드 1 · 2 를 한 장에서 줄 세워 10 시간 · 다른 장은 놂)
# 사용: CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=<n> python 시드하나.py <설정 이름> <시드> [확인]
# 하네스.시드돌기 와 같은 꼴로 설정을 만들어 같은 폴더(시드<n>/)에 씀 → 이어.pt · lora · 생성.json 을 하네스가 다시 돌 때 그대로 읽음(학습 · 생성 다시 안 함)
# 확인: 설정 글이 그 폴더 이어.pt 의 것과 같은지만 보고 끝(다르면 이어 하기가 안 되고 처음부터 배움)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    from hydra import initialize_config_dir, compose; from omegaconf import OmegaConf; import 과제코드 as K
    이름, s = sys.argv[1], int(sys.argv[2])
    with initialize_config_dir(version_base=None, config_dir=K.뿌리 + "/하네스/conf"): cfg = compose(config_name=이름)
    assert cfg.목표 == "코드생성" and s > 0
    c = OmegaConf.create(OmegaConf.to_container(cfg, resolve=True)); c.학습.시드 = s; 폴 = f"{K.뿌리}/out/하네스/{cfg.판.이름}/시드{s}/"
    if sys.argv[3:] == ["확인"]:
        import torch; 설정 = OmegaConf.to_yaml(c) + f"# 코드 {K.코드해시()}\n"; p = 폴 + "이어.pt"
        print("이어.pt 없음" if not os.path.exists(p) else ("설정 같음 — 이어 함" if torch.load(p, weights_only=False)["설정"] == 설정 else "⚠ 설정 다름")); sys.exit()
    os.makedirs(폴, exist_ok=True); print("시드", s, K.점검(c, 폴), flush=True)
