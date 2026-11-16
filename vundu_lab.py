#!/usr/bin/env python3
"""Vundu V0.1.0 - local server: compile, flash and monitor. Python 3.9+.
Run:  python3 vundu_lab.py   (opens http://127.0.0.1:8765, or the next free port)"""
import http.server, json, os, sys, signal, secrets, queue, base64, time, socket, struct, socketserver, math, subprocess, shutil, threading, re, glob, platform
import urllib.request, tarfile, zipfile, webbrowser, urllib.parse, shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENG = ROOT / "data" / "engines"   # every engine lives here; nothing touches ~/.platformio or VS Code
PORT = 8765
WIN = os.name == "nt"
PIOARDUINO = "https://github.com/pioarduino/platform-espressif32/releases/download/stable/platform-espressif32.zip"
BOARD_URLS = ["https://espressif.github.io/arduino-esp32/package_esp32_index.json",
  "https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json",
  "https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json"]
SKIP = {".pio", ".git", ".cw_build", "node_modules", "__pycache__", ".vscode"}
BOOT = {"esp32": 0x1000, "esp32s2": 0x1000, "esp32s3": 0, "esp32c3": 0, "esp32c6": 0, "esp32c5": 0x2000, "esp32p4": 0x2000}
S = {"proj": None, "files": {}, "proc": None, "stop": False}
LOCK = threading.Lock()
PICK = "import sys,tkinter as t,tkinter.filedialog as f;r=t.Tk();r.withdraw();r.attributes('-topmost',1);print(f.askdirectory(title=sys.argv[1],initialdir=sys.argv[2]))"

def exe(d, n): return str(Path(d) / (n + (".exe" if WIN else "")))
def vbin(engine): return ENG / engine / "venv" / ("Scripts" if WIN else "bin")

def kill(p):   # stops the engine and everything it started
    if p.poll() is not None: return
    try:
        if WIN: subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
        else:
            os.killpg(p.pid, signal.SIGTERM)
            threading.Timer(5, lambda: p.poll() is None and os.killpg(p.pid, signal.SIGKILL)).start()
    except Exception: pass

def run(cmd, say, extra=None, stoppable=True):
    if stoppable and S["stop"]: return 1
    env = dict(os.environ); env.update(extra or {})
    say("$ " + shlex.join([str(x) for x in cmd]))   # quoted, so a path with spaces can be copied into a terminal
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
                         env=env, start_new_session=not WIN)
    S["proc" if stoppable else "fproc"] = p
    try:
        for line in p.stdout: say(line.rstrip())
    except Exception:   # browser tab closed mid-build: stop the engine too
        kill(p); raise
    return p.wait()

def chip_of(b):
    b = b.lower()
    for k in ("p4", "c6", "c5", "c3", "s3", "s2"):
        if k in b: return "esp32" + k
    return "esp32"

def board_of(proj):
    ini = proj / "platformio.ini"
    t = ini.read_text(errors="replace") if ini.exists() else ""
    m = re.search(r"(?m)^\s*board\s*=\s*(\S+)", t)
    return (m.group(1) if m else ""), t

def guess(proj):
    b, t = board_of(proj)
    if "pico" in b.lower() or "rp2040" in b.lower(): return "rp2040:rp2040:rpipico"
    if "stm32" in t.lower() or "nucleo" in b.lower() or "blackpill" in b.lower(): return "STMicroelectronics:stm32:GenF4"
    return "esp32:esp32:" + chip_of(b)

# ---- PlatformIO / pioarduino: two separate venvs, two separate core dirs ----
def build_pio(engine, proj, say):
    vb = vbin(engine); pio = exe(vb, "pio")
    if not os.path.exists(pio):
        say(f"First run: installing {engine} into {vb.parent} (one-off)...")
        if run([sys.executable, "-m", "venv", str(vb.parent)], say): return False
        if run([exe(vb, "python"), "-m", "pip", "install", "-U", "platformio"], say): return False
    if not (proj / "platformio.ini").exists():
        say("This folder has no platformio.ini. Choose Arduino IDE, or open an LCD Wizard export."); return False
    args, tmp = [pio, "run", "-d", str(proj)], None
    if engine == "pioarduino":   # same project, newer ESP32 platform; the user's files are never edited
        txt = re.sub(r"(?m)^(\s*platform\s*=\s*)espressif32\b.*$", lambda m: m.group(1) + PIOARDUINO,
                     (proj / "platformio.ini").read_text(errors="replace"))
        tmp = proj / ".cw_pioarduino.ini"; tmp.write_text(txt); args += ["-c", str(tmp)]
    try: return run(args, say, {"PLATFORMIO_CORE_DIR": str(ENG / engine / "core")}) == 0
    finally:
        if tmp: tmp.unlink(missing_ok=True)

def collect_pio(engine, proj, say):
    fw = sorted((proj / ".pio" / "build").glob("*/firmware.bin"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not fw: return {}
    bd, arts = fw[0].parent, {}
    fac = bd / "firmware.factory.bin"   # newer platforms (e.g. pioarduino) already build this themselves
    if fac.exists(): arts[fac.name] = fac
    elif (bd / "bootloader.bin").exists():   # otherwise make one: a single file flashed at 0x0
        core = ENG / engine / "core" / "packages"
        esp = glob.glob(str(core / "tool-esptoolpy*" / "esptool.py"))
        boot = glob.glob(str(core / "framework-arduinoespressif32*" / "tools" / "partitions" / "boot_app0.bin"))
        chip = chip_of(board_of(proj)[0]); out = bd / "firmware.factory.bin"
        # esptool needs the packages PlatformIO installs in its own Python (core/penv), so try that first
        pens = ENG / engine / "core" / "penv" / ("Scripts" if WIN else "bin")
        pys = [p for p in (exe(pens, "python"), exe(vbin(engine), "python")) if os.path.exists(p)]
        done = False
        for py in pys if esp and boot else []:
            if run([py, esp[0], "--chip", chip, "merge_bin", "-o", str(out), hex(BOOT[chip]), str(bd / "bootloader.bin"),
                    "0x8000", str(bd / "partitions.bin"), "0xe000", boot[0], "0x10000", str(fw[0])], say) == 0 and out.exists():
                arts[out.name] = out; done = True; break
        if not done: say("Could not build the merged .bin; the separate files below need their own flash offsets.")
    for n in ("firmware.bin", "bootloader.bin", "partitions.bin"):
        if (bd / n).exists(): arts[n] = bd / n
    return arts

# ---- Arduino IDE engine (arduino-cli, fully local) ----
def ensure_arduino(say):
    d = ENG / "arduino"; cli = exe(d, "arduino-cli")
    if os.path.exists(cli): return cli
    d.mkdir(parents=True, exist_ok=True)
    s = {"Linux": "Linux", "Darwin": "macOS", "Windows": "Windows"}[platform.system()]
    a = "ARM64" if platform.machine().lower() in ("arm64", "aarch64") else "64bit"
    ext = "zip" if WIN else "tar.gz"; arc = d / ("dl." + ext)
    say("First run: downloading arduino-cli (one-off)...")
    urllib.request.urlretrieve(f"https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_{s}_{a}.{ext}", arc)
    zipfile.ZipFile(arc).extractall(d) if WIN else tarfile.open(arc).extractall(d)
    arc.unlink(); return cli

def build_arduino(proj, fqbn, say):
    cli, d = ensure_arduino(say), ENG / "arduino"
    env = {"ARDUINO_DIRECTORIES_DATA": str(d / "data"), "ARDUINO_DIRECTORIES_USER": str(d / "user"),
           "ARDUINO_DIRECTORIES_DOWNLOADS": str(d / "dl"), "ARDUINO_BOARD_MANAGER_ADDITIONAL_URLS": ",".join(BOARD_URLS)}
    if len(fqbn.split(":")) < 3: say("Enter a board (FQBN), e.g. esp32:esp32:esp32s3"); return False
    for c in ([cli, "core", "update-index"], [cli, "core", "install", ":".join(fqbn.split(":")[:2])]):
        if run(c, say, env): return False
    lm = proj / "LIBRARIES.md"
    if lm.exists():
        for ln in re.findall(r"(?m)^\s*arduino-cli lib install\s+(.+)$", lm.read_text(errors="replace")):
            run([cli, "lib", "install", *shlex.split(ln)], say, env)
    out = proj / ".cw_build"; shutil.rmtree(out, ignore_errors=True)
    return run([cli, "compile", "--fqbn", fqbn, "--export-binaries", "--output-dir", str(out), str(proj)], say, env) == 0

def do_compile(engine, fqbn, say):
    proj = S["proj"]
    if engine == "arduino":
        ok = build_arduino(proj, fqbn, say)
        bins = sorted((proj / ".cw_build").glob("*.bin"), key=lambda f: "merged" not in f.name) if ok else []
        return ok, {f.name: f for f in bins}
    ok = build_pio(engine, proj, say)
    return ok, (collect_pio(engine, proj, say) if ok else {})

def pick(title="Choose a folder", start=""):
    start = start if start and os.path.isdir(start) else str(Path.home())
    try:
        r = subprocess.run([sys.executable, "-c", PICK, title, start], capture_output=True, text=True, timeout=600)
        return r.stdout.strip() if r.returncode == 0 else None   # None = no dialog available
    except Exception: return None

def open_project(path):
    p = Path(path)
    if not p.is_dir(): return {"error": "Not a folder"}
    files = []
    for r, d, fs in os.walk(p):
        d[:] = sorted(x for x in d if x not in SKIP)
        files += [str((Path(r) / f).relative_to(p)).replace("\\", "/") for f in sorted(fs)]
        if len(files) > 3000: break
    S["proj"], S["files"] = p, {}
    return {"name": p.name, "files": files, "fqbn": guess(p), "pio": (p / "platformio.ini").exists()}

# ---- Serial: pyserial + esptool live in their own environment (data/engines/serial) ----
TOKEN = secrets.token_urlsafe(16)      # random per run; every request must carry it
SER = {"port": None, "cfg": {}, "want": False, "gen": 0, "flashing": False, "hold": False}
SUBS, SLOCK = [], threading.Lock()
UPL, SETF = ROOT / "data" / "uploads", ROOT / "data" / "settings.json"
serial = None

def emit(o):
    with SLOCK:
        for q in SUBS: q.put(o)

def serial_sps():
    v = ENG / "serial" / "venv"
    return glob.glob(str(v / "lib*" / "python*" / "site-packages")) + glob.glob(str(v / "Lib" / "site-packages"))

def tools_status():   # "ok", "missing" (not there, or incomplete) or "mislabelled" (another engine sits in the serial folder)
    sps = [Path(x) for x in serial_sps()]
    if not sps or not os.path.exists(exe(vbin("serial"), "python")): return "missing"
    if any((sp / "platformio").is_dir() for sp in sps): return "mislabelled"
    return "ok" if any((sp / "serial").is_dir() and (sp / "esptool").is_dir() for sp in sps) else "missing"

def serial_ready():   # never uses a pyserial that happens to be installed elsewhere on the computer
    global serial
    if serial: return True
    if tools_status() != "ok": return False
    for sp in serial_sps():
        if sp not in sys.path: sys.path.insert(0, sp)
    try:
        import serial, serial.tools.list_ports
        return True
    except ImportError: return False

def tools_note():
    return {"mislabelled": "The folder data/engines/serial holds another engine (PlatformIO), so it cannot be used. Rename it to platformio and restart.",
            "missing": "Serial tools (port access and the flasher) are not installed yet."}.get(tools_status(), "")

def repair_layout():   # if an engine folder was renamed to 'serial', give it its own name back
    ser, pio = ENG / "serial", ENG / "platformio"
    if tools_status() == "mislabelled":
        if not pio.exists():
            os.rename(ser, pio); print("Put data/engines/platformio back (it had been renamed to 'serial'). The serial tools will be installed fresh into data/engines/serial.")
        else: print("WARNING: data/engines/serial contains the PlatformIO engine, and data/engines/platformio exists too. Rename or delete one by hand.")

def setup_serial():   # the only thing that ever creates data/engines/serial
    say = lambda m: emit({"t": "setup", "m": m})
    if tools_status() == "mislabelled": say(tools_note()); return emit({"t": "setup_done", "ok": False})
    vb = vbin("serial"); ok = True
    try:
        if not os.path.exists(exe(vb, "python")):
            ok = run([sys.executable, "-m", "venv", "--clear", str(vb.parent)], say, stoppable=False) == 0
        ok = ok and run([exe(vb, "python"), "-m", "pip", "install", "-U", "pyserial", "esptool"], say, stoppable=False) == 0
        ok = ok and run([exe(vb, "python"), "-c", "import serial, esptool"], say, stoppable=False) == 0
    except Exception as e: say("ERROR: %s" % e); ok = False
    emit({"t": "setup_done", "ok": bool(ok and serial_ready())})

def dialout_hint():
    if os.name != "posix" or sys.platform == "darwin": return ""
    try:
        import grp
        mine = {grp.getgrgid(g).gr_name for g in os.getgroups()}
        for n in ("dialout", "uucp"):
            try: grp.getgrnam(n)
            except KeyError: continue
            return "" if n in mine else f"Serial ports need the {n} group. Run: sudo usermod -aG {n} $USER  then log out and back in."
    except Exception: pass
    return ""

def why(e):
    m = str(e)
    if isinstance(e, PermissionError) or re.search(r"denied|busy|in use", m, re.I):
        return "Cannot open the port: it is busy or access is denied. Close other programs using it (Arduino IDE or PlatformIO monitor, another serial tool). " + dialout_hint()
    return m

def open_serial(c):
    def pick(v, ok, default):   # a bad or missing setting falls back to the normal one instead of blocking the connection
        try: v = type(default)(v)
        except (TypeError, ValueError): return default
        return v if v in ok else default
    s = serial.Serial(c["port"], int(c.get("baud") or 115200), bytesize=pick(c.get("bits"), (5, 6, 7, 8), 8), parity=pick(c.get("parity"), "NEOMS", "N"),
                      stopbits=pick(c.get("stop"), (1, 1.5, 2), 1.0), timeout=0.1, rtscts=c.get("flow") == "rtscts", xonxoff=c.get("flow") == "xonxoff")
    s.dtr = bool(c.get("dtr")); s.rts = bool(c.get("rts"))
    return s

def ser_disconnect():
    SER["want"] = False; SER["gen"] += 1
    s, SER["port"] = SER["port"], None
    try: s and s.close()
    except Exception: pass
    emit({"t": "status", "s": "closed"})

def ser_connect(c):
    ser_disconnect()
    SER["port"], SER["cfg"], SER["want"] = open_serial(c), c, True
    SER["gen"] += 1
    emit({"t": "status", "s": "connected", "port": c["port"]})
    threading.Thread(target=reader, args=(SER["gen"],), daemon=True).start()

def reader(gen):   # reads the port; if the board resets or is unplugged, keeps retrying
    live = lambda: SER["want"] and SER["gen"] == gen
    while live():
        if SER["flashing"]: time.sleep(0.1); continue
        s = SER["port"]
        try:
            with RLOCK: d = s.read(s.in_waiting or 1)   # Modbus RTU takes this same lock for a whole transaction
            time.sleep(0.003)
            if d: emit({"t": "rx", "d": base64.b64encode(d).decode()})
        except Exception:
            if not live(): break
            try: s and s.close()
            except Exception: pass
            SER["port"] = None; emit({"t": "status", "s": "lost"})
            if not SER["cfg"].get("auto", True): SER["want"] = False; emit({"t": "status", "s": "closed"}); break
            while live():
                time.sleep(1)
                if SER["flashing"]: continue
                try:
                    SER["port"] = open_serial(SER["cfg"]); emit({"t": "status", "s": "connected", "port": SER["cfg"]["port"]}); break
                except Exception: pass

def start_flash(j):
    if not serial_ready(): return "Serial tools are not installed yet."
    if SER["flashing"]: return "A flash is already running."
    if not j.get("port"): return "Choose a port first."
    items = []
    for f in j.get("files", []):
        src, _, nm = f.get("src", "").partition(":"); nm = os.path.basename(nm)
        path = S["files"].get(nm) if src == "art" else UPL / nm
        if not path or not Path(path).is_file(): return f"File not found: {nm}"
        try: a = int(str(f.get("addr")), 0)
        except ValueError: return f"Bad address for {nm}"
        items.append((a, Path(path)))
    if not items: return "Add at least one .bin file."
    items.sort(key=lambda x: x[0])
    for (a, p), (b, _) in zip(items, items[1:]):
        if a + p.stat().st_size > b: return f"{p.name} overlaps the next file. Check the addresses."
    c = str(j.get("chip", "auto")); c = c if re.fullmatch(r"auto|esp32(s2|s3|c2|c3|c5|c6|h2|p4)?", c) else "auto"
    threading.Thread(target=flash_job, args=(items, j["port"], int(j.get("baud", 460800)), bool(j.get("hold")), c, j.get("verify", True) is not False), daemon=True).start()

CHIPS = {0: "ESP32", 2: "ESP32-S2", 5: "ESP32-C3", 9: "ESP32-S3", 12: "ESP32-C2", 13: "ESP32-C6", 16: "ESP32-H2", 18: "ESP32-P4", 23: "ESP32-C5"}
BOOTADDR = {"ESP32": 0x1000, "ESP32-S2": 0x1000, "ESP32-P4": 0x2000, "ESP32-C5": 0x2000}   # other chips: 0x0

def inspect(path):   # recognise a .bin from its contents, not its name
    path = Path(path); n = path.stat().st_size
    with open(path, "rb") as fh: d = fh.read(0x9000)
    out = {"size": n, "role": "binary file", "chip": "", "addr": "0x10000"}
    chip_at = lambda o: CHIPS.get(int.from_bytes(d[o + 12:o + 14], "little"), "") if d[o:o + 1] == b"\xe9" else ""
    if n > 0x8002 and d[0x8000:0x8002] == b"\xaa\x50":
        out.update(role="merged image", chip=next((chip_at(o) for o in (0, 0x1000, 0x2000) if chip_at(o)), ""), addr="0x0")
    elif d[:2] == b"\xaa\x50": out.update(role="partition table", addr="0x8000")
    elif n == 4096 and d[:4] == b"\x01\0\0\0": out.update(role="boot_app0", addr="0xe000")
    elif d[:1] == b"\xe9":
        c = chip_at(0)
        if d[32:36] == b"\x32\x54\xcd\xab": out.update(role="app", chip=c)
        else: out.update(role="bootloader", chip=c, addr=hex(BOOTADDR.get(c, 0)))
    return out

def port_list():   # one board at a time: show real USB serial devices only
    allp = list(serial.tools.list_ports.comports())
    if sys.platform == "darwin": allp = [x for x in allp if not x.device.startswith("/dev/tty.")]
    return sorted(({"device": x.device, "desc": "" if x.description in ("n/a", x.device) else x.description}
                   for x in allp if getattr(x, "vid", None)), key=lambda d: d["device"])

def esp_run(args, line):   # frees our own port, runs esptool, then lets the reader reopen the port
    SER["flashing"] = True
    s, SER["port"] = SER["port"], None
    try: s and s.close()
    except Exception: pass
    emit({"t": "status", "s": "flashing"})
    py = exe(vbin("serial"), "python")
    if tools_status() != "ok": line("The flasher is not installed. Press Install (one-off) in the sidebar. " + tools_note()); return 1
    try: return run([py, "-m", "esptool"] + args, line, stoppable=False)
    except Exception as e: line("ERROR: %s" % e); return 1
    finally:
        SER["flashing"] = False
        emit({"t": "status", "s": "lost" if SER["want"] else "closed"})

def detect_job(port, baud, hold):
    got = []
    def line(m):
        emit({"t": "flog", "m": m}); r = re.search(r"(?:Chip is|Chip type:)\s+(ESP32(?:-[SCHP]\d)?)", m)
        if r and not got: got.append(r.group(1))
    rc = esp_run(["--port", port, "--baud", str(baud)] + (["--before", "no_reset"] if hold else []) + ["flash_id"], line)
    emit({"t": "chip", "chip": got[0] if got else "", "ok": rc == 0 and bool(got)})

def flash_job(items, port, baud, hold, chip, verify):
    def line(m):
        emit({"t": "flog", "m": m}); r = re.search(r"\((\d+)\s?%\)", m)
        if r: emit({"t": "fprog", "p": int(r.group(1))})
    args = ["--chip", chip, "--port", port, "--baud", str(baud)] + (["--before", "no_reset"] if hold else []) + \
           ["write_flash"] + ([] if verify else ["--no-verify"])
    for a, p in items: args += [hex(a), str(p)]
    emit({"t": "fdone", "ok": esp_run(args, line) == 0})

# ---- Modbus: written from the Modbus specification, no libraries. RTU uses the sidebar's port; TCP opens a socket. ----
RLOCK = threading.Lock()
DEMO = {}

def crc16(b):
    c = 0xFFFF
    for x in b:
        c ^= x
        for _ in range(8): c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return c

def rtu_need(b):   # how many bytes the reply frame will have, as far as we can tell yet
    if len(b) < 3: return 5
    return 5 if b[1] & 0x80 else (5 + b[2] if b[1] in (1, 2, 3, 4) else 8)

def _rd(sk, n):
    b = b""
    while len(b) < n:
        c = sk.recv(n - len(b))
        if not c: raise ConnectionError("connection closed")
        b += c
    return b

def mb_txn(j):
    try: unit, pdu = int(j.get("unit", 1)) & 255, bytes.fromhex(j.get("pdu", ""))
    except ValueError: return {"error": "Bad request"}
    tmo = max(0.1, float(j.get("timeout", 1000)) / 1000); t0 = time.time(); rsp = b""
    if j.get("mode") == "tcp":
        req = struct.pack(">HHHB", int(t0 * 1000) & 0xFFFF, 0, len(pdu) + 1, unit) + pdu
        try:
            with socket.create_connection((j.get("host") or "127.0.0.1", int(j.get("port", 502))), timeout=tmo) as sk:
                sk.sendall(req); rsp = _rd(sk, 7); rsp += _rd(sk, struct.unpack(">H", rsp[4:6])[0] - 1)
        except Exception as e: return {"error": "TCP: %s" % e, "req": req.hex()}
        out = rsp[7:]
    else:
        s = SER["port"]
        if not s: return {"error": "Serial port not connected. Use Connect in the sidebar."}
        body = bytes([unit]) + pdu; req = body + struct.pack("<H", crc16(body))
        try:
            with RLOCK:
                s.reset_input_buffer(); s.write(req); end = time.time() + tmo
                while time.time() < end and len(rsp) < rtu_need(rsp): rsp += s.read(max(1, rtu_need(rsp) - len(rsp)))
        except Exception as e: return {"error": why(e), "req": req.hex()}
        e = lambda m: {"error": m, "req": req.hex(), "rsp": rsp.hex()}
        if len(rsp) < 5: return e("No reply (timeout)")
        if crc16(rsp[:-2]) != struct.unpack("<H", rsp[-2:])[0]: return e("CRC error in the reply")
        if rsp[0] != unit: return e("Reply came from unit %d" % rsp[0])
        out = rsp[1:-2]
    return {"pdu": out.hex(), "req": req.hex(), "rsp": rsp.hex(), "ms": round((time.time() - t0) * 1000)}

MEM = {"r": [0] * 256, "c": [0] * 256}
def demo_reply(pdu):   # a small pretend device: reg 0 counter, reg 1 sine, regs 2-3 float temperature; the rest is writable memory
    f = pdu[0]; a, n = struct.unpack(">HH", pdu[1:5]) if len(pdu) >= 5 else (0, 0); t = time.time()
    if f in (1, 2, 3, 4, 15, 16) and (a + n > 256 or n < 1): return bytes([f | 0x80, 2])
    if f in (3, 4):
        r = MEM["r"][:]; w = struct.unpack(">HH", struct.pack(">f", 22.5 + 2 * math.sin(t / 3)))
        r[0], r[1], r[2], r[3] = int(t) & 0xFFFF, int(1000 + 500 * math.sin(t)), w[0], w[1]
        return bytes([f, n * 2]) + b"".join(struct.pack(">H", x) for x in r[a:a + n])
    if f in (1, 2):
        by = bytearray((n + 7) // 8)
        for i, v in enumerate(MEM["c"][a:a + n]):
            if v: by[i >> 3] |= 1 << (i & 7)
        return bytes([f, len(by)]) + bytes(by)
    if f == 6: MEM["r"][a] = n; return pdu[:5]
    if f == 5: MEM["c"][a] = 1 if n else 0; return pdu[:5]
    if f == 16:
        for i in range(n): MEM["r"][a + i] = struct.unpack(">H", pdu[6 + 2 * i:8 + 2 * i])[0]
        return pdu[:5]
    if f == 15:
        for i in range(n): MEM["c"][a + i] = (pdu[6 + (i >> 3)] >> (i & 7)) & 1
        return pdu[:5]
    return bytes([f | 0x80, 1])

class MBHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            while True:
                h = _rd(self.request, 7); pdu = _rd(self.request, struct.unpack(">H", h[4:6])[0] - 1); r = demo_reply(pdu)
                self.request.sendall(h[:4] + struct.pack(">H", len(r) + 1) + h[6:7] + r)
        except Exception: pass

def demo_start():
    if not DEMO.get("srv"):
        class DemoSrv(socketserver.ThreadingTCPServer): daemon_threads = True
        DEMO["srv"] = DemoSrv(("127.0.0.1", 0), MBHandler)
        threading.Thread(target=DEMO["srv"].serve_forever, daemon=True).start()
    return DEMO["srv"].server_address[1]

def load_settings():
    try: return json.loads(SETF.read_text())
    except Exception: return {}

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ctype="application/json", code=200, extra=None):
        if isinstance(body, (dict, list)): body = json.dumps(body)
        if isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        p, proj = u.path, S["proj"]
        if not self.allowed(p, q): return self.send("forbidden", "text/plain", 403)
        if p == "/": return self.send((ROOT / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN), "text/html; charset=utf-8")
        if p == "/api/pick": return self.send({"path": pick("Choose your project folder", str(proj.parent) if proj else "")})
        if p == "/api/open": return self.send(open_project(q.get("path", "")))
        if p == "/api/file" and proj:
            f = (proj / q.get("p", "")).resolve()
            if proj.resolve() not in f.parents or not f.is_file(): return self.send("no", "text/plain", 403)
            b = f.read_bytes()[:400000]
            return self.send("(binary file)" if b"\0" in b else b.decode("utf-8", "replace"), "text/plain; charset=utf-8")
        if p == "/api/stop":
            S["stop"] = True
            if S["proc"]: kill(S["proc"])
            return self.send({"ok": True})
        if p == "/api/compile" and proj: return self.compile(q)
        if p == "/api/ports":
            ok = serial_ready()
            pl = port_list() if ok else []
            return self.send({"ready": ok, "ports": pl, "hint": dialout_hint(), "note": "" if ok else tools_note()})
        if p == "/api/inspect":
            nm = os.path.basename(q.get("src", "").partition(":")[2]); f = S["files"].get(nm)
            return self.send({"name": nm, **inspect(f)} if f else {"error": "not found"})
        if p == "/api/last": return self.send({"files": list(S["files"])})
        if p == "/api/settings": return self.send(load_settings())
        if p == "/api/events":
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.end_headers()
            qu = queue.Queue()
            with SLOCK: SUBS.append(qu)
            try:
                st = "flashing" if SER["flashing"] else ("connected" if SER["port"] else "closed")
                self.wfile.write(("data: " + json.dumps({"t": "status", "s": st, "port": SER["cfg"].get("port", "")}) + "\n\n").encode()); self.wfile.flush()
                while True:
                    try: self.wfile.write(("data: " + json.dumps(qu.get(timeout=15)) + "\n\n").encode())
                    except queue.Empty: self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except Exception: pass
            finally:
                with SLOCK: SUBS.remove(qu)
            return
        f = S["files"].get(q.get("n", ""))
        if p == "/dl" and f:
            return self.send(f.read_bytes(), "application/octet-stream",
                             extra={"Content-Disposition": f'attachment; filename="{proj.name}_{f.name}"'})
        if p == "/api/save" and f:
            d = pick("Save to which folder?", str(Path.home() / "Downloads"))
            if not d: return self.send({"saved": None, "manual": d is None})
            dest = Path(d) / f"{proj.name}_{f.name}"; shutil.copy2(f, dest)
            return self.send({"saved": str(dest)})
        self.send("not found", "text/plain", 404)

    def allowed(self, p, q):   # local host only, same-site only, and the per-run token
        return (self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")
                and self.headers.get("Sec-Fetch-Site", "same-origin") in ("same-origin", "none")
                and (p == "/" or q.get("t") == TOKEN))

    def do_POST(self):   # everything that changes state or touches hardware
        u = urllib.parse.urlparse(self.path); q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}; p = u.path
        if not self.allowed(p, q): return self.send("forbidden", "text/plain", 403)
        n = int(self.headers.get("Content-Length") or 0)
        if p == "/api/upload":
            if n > 64_000_000: return self.send({"error": "File too large"})
            UPL.mkdir(parents=True, exist_ok=True)
            name = os.path.basename(q.get("name", "")) or "file.bin"
            (UPL / name).write_bytes(self.rfile.read(n))
            return self.send({"name": name, **inspect(UPL / name)})
        try: j = json.loads(self.rfile.read(n) or b"{}")
        except ValueError: j = {}
        s = SER["port"]
        if p == "/api/setup": threading.Thread(target=setup_serial, daemon=True).start(); return self.send({"ok": True})
        if p == "/api/settings": SETF.parent.mkdir(parents=True, exist_ok=True); SETF.write_text(json.dumps(j)); return self.send({"ok": True})
        if p == "/api/serial/connect":
            if not serial_ready(): return self.send({"error": "Serial tools are not installed yet."})
            if SER["flashing"]: return self.send({"error": "Flashing is in progress. The Monitor comes back when it finishes."})
            if SER["hold"]: return self.send({"error": "The port is reserved while the Flash tab is open. Open the Monitor tab to connect."})
            try: ser_connect(j)
            except Exception as e: return self.send({"error": why(e)})
            return self.send({"ok": True})
        if p == "/api/serial/hold":
            SER["hold"] = bool(j.get("on"))
            if SER["hold"]: ser_disconnect()
            return self.send({"ok": True})
        if p == "/api/serial/disconnect": ser_disconnect(); return self.send({"ok": True})
        if p in ("/api/serial/send", "/api/serial/ctl"):
            if not s: return self.send({"error": "Not connected"})
            try:
                if p.endswith("send"): s.write(base64.b64decode(j.get("d", "")))
                else: s.dtr, s.rts = bool(j.get("dtr")), bool(j.get("rts"))
            except Exception as e: return self.send({"error": why(e)})
            return self.send({"ok": True})
        if p == "/api/modbus": return self.send(mb_txn(j))
        if p == "/api/modbus/demo": return self.send({"port": demo_start()})
        if p == "/api/detect":
            if not serial_ready() or SER["flashing"] or not j.get("port"): return self.send({"error": "Choose a port first."})
            threading.Thread(target=detect_job, args=(j["port"], int(j.get("baud", 115200)), bool(j.get("hold"))), daemon=True).start()
            return self.send({"ok": True})
        if p == "/api/flash/cancel":
            if S.get("fproc"): kill(S["fproc"])
            return self.send({"ok": True})
        if p == "/api/flash": err = start_flash(j); return self.send({"error": err} if err else {"ok": True})
        self.send("not found", "text/plain", 404)

    def compile(self, q):
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.end_headers()
        def ev(o): self.wfile.write(("data: " + json.dumps(o) + "\n\n").encode()); self.wfile.flush()
        say = lambda m: ev({"t": "log", "m": m})
        if not LOCK.acquire(False): say("A compile is already running."); return ev({"t": "done", "ok": False})
        ok, arts, S["stop"] = False, {}, False
        try: ok, arts = do_compile(q.get("engine", "platformio"), q.get("fqbn", ""), say)
        except Exception as e: say("ERROR: %s" % e)
        finally: LOCK.release()
        S["files"] = arts
        ev({"t": "done", "ok": bool(ok and arts and not S["stop"]), "files": list(arts), "stopped": S["stop"]})

def startup_report():   # one block when the server starts: what is there, what is missing, and the exact command to fix it
    import importlib.util as iu
    rows, bad, need_net = [], 0, False
    def add(label, state, *fix):
        nonlocal bad
        rows.append((label, state, fix)); bad += state not in ("ok", "installed", "not installed yet")
    v = sys.version_info
    add("Python %d.%d.%d" % v[:3], "ok" if v >= (3, 9) else "TOO OLD", *([] if v >= (3, 9) else ["install Python 3.9 or newer"]))
    venv_ok = bool(iu.find_spec("venv") and iu.find_spec("ensurepip"))
    add("Virtual environments (venv + pip)", "ok" if venv_ok else "MISSING", *([] if venv_ok else ["sudo apt install python3-venv     (Ubuntu / Debian)"]))
    tk_ok = bool(iu.find_spec("tkinter") and iu.find_spec("_tkinter"))
    add("Folder dialog (tkinter)", "ok" if tk_ok else "MISSING", *([] if tk_ok else ["sudo apt install python3-tk     (without it you paste folder paths instead)"]))
    st, sdir = tools_status(), ENG / "serial"
    if st == "mislabelled":
        add("Serial tools (data/engines/serial)", "WRONG FOLDER", "it holds another engine (PlatformIO). Rename it to platformio, then restart.")
    else:
        sps = [Path(x) for x in serial_sps()]
        have = lambda pkg: any((sp / pkg).is_dir() for sp in sps)
        vpy = exe(vbin("serial"), "python")
        manual = ("%s -m pip install -U pyserial esptool" % shlex.quote(vpy)) if os.path.exists(vpy) else \
                 ("python3 -m venv %s && %s -m pip install -U pyserial esptool" % (shlex.quote(str(sdir / "venv")), shlex.quote(vpy)))
        fix = ("open the Monitor or Flash tab and press Install (one-off)", "or in a terminal:  " + manual)
        pkgs = (("pyserial (Monitor, Plot, Modbus)", "serial"), ("esptool (Flash)", "esptool"))
        last = [p for _, p in pkgs if not have(p)][-1:]   # the fix is printed once, under the last missing item
        for label, pkg in pkgs:
            if have(pkg): add(label, "ok")
            else: add(label, "MISSING", "not installed in %s" % (sdir / "venv"), *(fix if [pkg] == last else ())); need_net = True
    for label, name, tool in (("PlatformIO engine", "platformio", "pio"), ("pioarduino engine", "pioarduino", "pio"), ("Arduino CLI engine", "arduino", "arduino-cli")):
        folder = ENG / name
        if os.path.exists(exe(vbin(name) if tool == "pio" else folder, tool)): add(label, "installed")
        else: add(label, "not installed yet", "the first Compile with it installs it (needs internet)"); need_net = True
    if os.name == "posix" and sys.platform != "darwin":
        hint = dialout_hint(); add("Serial port access (dialout group)", "ok" if not hint else "MISSING", *([hint] if hint else []))
    if need_net:
        try: socket.create_connection(("pypi.org", 443), timeout=2).close(); add("Internet (for installs)", "ok")
        except OSError: add("Internet (for installs)", "OFFLINE", "the engines and serial tools are downloaded, so connect first")
    print("\nVundu V0.1.0 - start-up check")
    for label, state, fix in rows:
        print("  " + (label + " ").ljust(40, ".") + " " + state)
        for f in fix: print("      -> " + f)
    print("  " + ("All good." if not bad else "%d item(s) need attention (see the -> lines). The app still starts." % bad) + "\n")

def open_browser(url):   # quiet launch, so the browser's own messages stay out of this terminal
    try:
        if platform.system() == "Linux" and shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else: webbrowser.open(url)
    except Exception: pass

if __name__ == "__main__":
    repair_layout()
    try: startup_report()
    except Exception as e: print("(start-up check could not run: %s)" % e)   # never stops the app from starting
    class Srv(http.server.ThreadingHTTPServer):
        allow_reuse_address = os.name != "nt"   # on Windows this flag would let two servers share a port
        daemon_threads = True
    srv = None
    for port in range(PORT, PORT + 20):         # port busy? take the next free one
        try: srv = Srv(("127.0.0.1", port), H); break
        except OSError: continue
    if not srv: sys.exit("No free port found between %d and %d." % (PORT, PORT + 19))
    print(f"Vundu running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    threading.Timer(0.8, lambda: open_browser(f"http://127.0.0.1:{port}")).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
