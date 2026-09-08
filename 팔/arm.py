"""3D 프린터를 3축 로봇팔로 쓴다. G-code 한 줄 쏘고 'ok' 받는다. 그게 전부."""
import sys, time, serial, serial.tools.list_ports as list_ports

# ponytail: 보드마다 다르다. 안 붙으면 여기부터 만진다.
BAUDS = [115200, 250000, 57600, 9600]


def find_port():
    """CH340/CP210 계열 USB-시리얼을 찾는다. 메인보드 레거시 COM1은 버린다."""
    cands = [p for p in list_ports.comports() if "PNP0501" not in (p.hwid or "")]
    if not cands:
        raise SystemExit("시리얼 포트 없음 — USB 안 꽂혔거나, 이 프린터는 SD 전용이다.")
    for p in cands:  # USB-시리얼 칩이 명확한 걸 우선
        if any(k in (p.description + p.hwid).upper() for k in ("CH340", "CP210", "FTDI", "USB")):
            return p.device
    return cands[0].device


class Arm:
    def __init__(self, port=None, baud=None):
        self.port = port or find_port()
        self.ser = None
        for b in ([baud] if baud else BAUDS):
            s = serial.Serial(self.port, b, timeout=2)
            time.sleep(2)  # Marlin은 시리얼 열면 리셋된다. 부팅 기다린다.
            s.reset_input_buffer()
            self.ser = s
            if self._talk("M115"):  # 펌웨어 정보 — 응답하면 이 보율이 맞다
                self.baud = b
                return
            s.close()
        raise SystemExit(f"{self.port}: 어떤 보율에도 응답 없음. Marlin이 아니거나 SD 전용 보드다.")

    def _talk(self, line, timeout=10):
        """한 줄 쏘고 'ok' 올 때까지 읽는다. 응답 줄들을 돌려준다."""
        self.ser.write((line.strip() + "\n").encode())
        out, deadline = [], time.time() + timeout
        while time.time() < deadline:
            r = self.ser.readline().decode(errors="replace").strip()
            if not r:
                continue
            if r.startswith("ok"):
                return out or ["ok"]
            if r.lower().startswith(("error", "!!")):
                raise RuntimeError(f"{line} -> {r}")
            out.append(r)
        return None  # 무응답

    def send(self, *lines):
        """G-code 여러 줄. 각 줄이 'ok' 받을 때까지 블로킹 = 동작이 실제로 끝난 뒤 리턴."""
        return [self._talk(l) for l in lines if l.strip() and not l.startswith(";")]

    def home(self):
        return self.send("G28")

    def move(self, x=None, y=None, z=None, f=3000):
        """절대좌표 mm. G-code 하나로 압축한다."""
        axes = "".join(f"{a}{v:.2f}" for a, v in (("X", x), ("Y", y), ("Z", z)) if v is not None)
        return self.send("G90", f"G1 {axes} F{f}", "M400")  # M400 = 이동 완료까지 대기

    def where(self):
        """M114 -> {'X':..,'Y':..,'Z':..}"""
        for r in (self._talk("M114") or []):
            if "X:" in r:
                return {k: float(v) for k, v in
                        (t.split(":") for t in r.split() if ":" in t and t[0] in "XYZE")}
        return None

    def close(self):
        if self.ser:
            self.ser.close()


def demo():
    """자체 점검: 붙고, 펌웨어 말하고, 원점 잡고, 움직이고, 그 자리에 있는지 확인."""
    a = Arm()
    print(f"연결 {a.port} @ {a.baud}")
    print("펌웨어:", a._talk("M115"))
    a.home()
    a.move(x=20, y=20, z=10)
    p = a.where()
    print("위치:", p)
    assert p and abs(p["X"] - 20) < 1 and abs(p["Y"] - 20) < 1, f"명령한 데로 안 갔다: {p}"
    print("OK — G-code로 팔이 움직인다.")
    a.close()


if __name__ == "__main__":
    if "--ports" in sys.argv:
        for p in list_ports.comports():
            print(p.device, "|", p.description, "|", p.hwid)
    else:
        demo()
