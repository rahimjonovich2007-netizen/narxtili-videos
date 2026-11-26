"""python3 tts_extract.py RESULT_FILE OUT.wav  -> decodes the base64 audio of a saved Speko audio_synthesize result and prints provider/model."""
import base64, json, subprocess, sys
raw = json.load(open(sys.argv[1]))
body = raw[0]["text"] if isinstance(raw, list) else raw
d = json.loads(body) if isinstance(body, str) else body
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + "/" + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, path + f"[{i}]")
    else:
        yield path, o
meta = {p: v for p, v in walk(d) if not (isinstance(v, str) and len(v) > 400)}
print(json.dumps(meta, indent=1, ensure_ascii=False)[:1500])
b64 = next(v for p, v in walk(d) if isinstance(v, str) and len(v) > 400 and not v.startswith("http"))
raw_audio = base64.b64decode(b64)
tmp = sys.argv[2] + ".raw"
open(tmp, "wb").write(raw_audio)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-ar", "48000", "-ac", "1", sys.argv[2]], check=True)
print("saved", sys.argv[2], len(raw_audio), "bytes raw")
