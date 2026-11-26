"""Duck the music under the voice, add the (un-ducked) sound effects if work/sfx.wav exists, normalise loudness
-> DAYDIR/work/mix.wav  (target -14 LUFS, true peak -1.5 dBTP)."""
import os
import subprocess
import sys

D = sys.argv[1].rstrip("/")
has_sfx = os.path.exists(f"{D}/work/sfx.wav")
if has_sfx:
    fc = ("[0:a]asplit=2[v][sc];[1:a]volume=0.5[bg];"
          "[bg][sc]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[duck];"
          "[v][duck][2:a]amix=inputs=3:duration=first:normalize=0[m];[m]loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.7:attack=3:release=60:level=disabled[a]")
    ins = ["-i", f"{D}/work/voice_st.wav", "-i", f"{D}/work/music.wav", "-i", f"{D}/work/sfx.wav"]
else:
    fc = ("[0:a]asplit=2[v][sc];[1:a]volume=0.55[bg];"
          "[bg][sc]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[duck];"
          "[v][duck]amix=inputs=2:duration=first:normalize=0[m];[m]loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.7:attack=3:release=60:level=disabled[a]")
    ins = ["-i", f"{D}/work/voice_st.wav", "-i", f"{D}/work/music.wav"]
subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[a]", "-ar", "48000",
                "-c:a", "pcm_s16le", f"{D}/work/mix.wav"], check=True)
print("mix ->", f"{D}/work/mix.wav", "(with sfx)" if has_sfx else "")
