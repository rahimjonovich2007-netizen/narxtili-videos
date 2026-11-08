"""Duck the music under the voice and normalise loudness -> DAYDIR/work/mix.wav  (target -14 LUFS, true peak -1.5 dBTP)."""
import subprocess
import sys

D = sys.argv[1].rstrip("/")
fc = ("[0:a]asplit=2[v][sc];[1:a]volume=0.55[bg];"
      "[bg][sc]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[duck];"
      "[v][duck]amix=inputs=2:duration=first:normalize=0[m];[m]loudnorm=I=-14:TP=-1.5:LRA=9[a]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{D}/work/voice_st.wav", "-i", f"{D}/work/music.wav",
                "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "-c:a", "pcm_s16le", f"{D}/work/mix.wav"], check=True)
print("mix ->", f"{D}/work/mix.wav")
