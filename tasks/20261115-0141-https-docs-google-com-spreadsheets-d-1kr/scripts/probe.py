"""Probe all media under a dir: duration, size, rotation, audio. Usage: python3 -I probe.py <dir>"""
import sys, os, json, subprocess

root = sys.argv[1]
for dp, _, fs in sorted(os.walk(root)):
    for f in sorted(fs):
        if f.startswith(".") or not f.lower().endswith((".mp4", ".mov", ".m4a", ".wav", ".mp3")):
            continue
        p = os.path.join(dp, f)
        try:
            j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", p],
                                          capture_output=True, text=True).stdout)
        except Exception as e:
            print("ERR", p, e); continue
        d = float(j.get("format", {}).get("duration", 0))
        v = [s for s in j.get("streams", []) if s["codec_type"] == "video"]
        a = any(s["codec_type"] == "audio" for s in j.get("streams", []))
        vs = ""
        if v:
            s = v[0]
            rot = s.get("tags", {}).get("rotate") or next((sd.get("rotation") for sd in s.get("side_data_list", []) if "rotation" in sd), 0)
            vs = f"{s.get('width')}x{s.get('height')} rot={rot} fps={s.get('r_frame_rate')}"
        print(f"{os.path.relpath(p, root)} | {d:.1f}s | {vs} | audio={a} | {os.path.getsize(p)/1e6:.1f}MB")
