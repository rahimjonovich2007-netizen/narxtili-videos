# Narx Tili: video ishlab chiqarish protokoli (@narxtili)

Bu repo **Narx Tili** (@narxtili, oddiy tilda iqtisod va marketing) Instagram akkaunti uchun har 2 kunda bitta Reels tayyorlaydigan ishlab chiqarish kiti va arxivi.
Ish tili: o'zbek (lotin). Egasi: Yodgorbek. Repo OCHIQ (public): Metricool videoni `raw.githubusercontent.com` havolasidan oladi, shuning uchun hech qanday maxfiy ma'lumot, parol yoki token yozilmaydi.

## Doimiy ruxsat va qoidalar
- Egasi **butun seriya uchun** ruxsat bergan: har bir video o'zing tayyorlaysan va Metricool orqali **o'zing rejalashtirib joylaysan** (qo'shimcha so'ramasdan).
- Hech qachon egasining parolini/tokenini kiritma. Faqat o'z yaratgan yoki litsenziyali material (ovoz = Speko/Gemini "Orus", musiqa = kitdagi `music.py` sintezi). Boshqalarning videolari/musiqasi/rasmlari YO'Q. Boshqa odam ovozi klon qilinmaydi.
- Har bir fakt tekshiriladi (web qidiruv). Tekshirilmagan raqam/da'vo ishlatilmaydi. Moliyaviy/investitsiya maslahati yo'q. Moliya videolarida oxirgi kartada: "Bu umumiy ma‘lumot, shaxsiy maslahat emas." (`Reel(disclaimer=...)`). Misol raqamlar ekranda "MISOL" belgisi bilan chiqadi. Joriy raqamlar (inflyatsiya, kurs, foiz) faqat rasmiy manbadan va chiqarish kunida.
- Sinab ko'rilmagan narsani "tayyor" dema: har bosqichda tekshir (pastda "Sifat darvozasi").

## Asosiy ma'lumotlar
- Metricool brand (blogId): **7935375**, vaqt zonasi `Indian/Maldives` (UTC+5 = Toshkent). Instagram: `narxtili`. Post vaqti har doim **19:30** (Toshkent).
- Reja: 15 ta video, har 2 kunda: Kun 1 = 8-noyabr, Kun 3 = 10-noy, 5 = 12, 7 = 14, 9 = 16, 11 = 18, 13 = 20, 15 = 22, 17 = 24, 19 = 26, 21 = 28, 23 = 30-noyabr, 25 = 2-dek, 27 = 4-dek, 29 = 6-dek. Har video post kunidan **bir kun oldin** tayyorlanadi.
- Stsenariylar: `scripts/dayNN.md` (Hook, qadamlar, CTA, Caption, Heshteglar, Tekshiruv). Umumiy qoidalar: `scripts/RULES.md`. Asl hujjat: Claude Docs "Iqtisod va marketing Instagram akkaunti: 30 kunlik video reja" (agar Docs ulangan bo'lsa).
- Brend: NAVY #0B1F3A, AMBER #FFB020, CREAM #F7F3EA, SLATE #3B4F6B. Shrift Inter. Logo = kit ichida `logo()`. Muqaddima: tepada "Narx Tili" logosi (y=300), progress chizig'i (y=1488), oxirida brend kartasi.
- Xavfsiz zona: y 250..1500, yon tomondan kamida 90 px (Instagram interfeysi qolganini yopadi).

## Muhit
- Python (numpy, scipy, PIL), ffmpeg, 2 CPU. Shrift: `/usr/share/fonts/opentype/inter/` (bo'lmasa DejaVu).
- Tarmoq ruxsat ro'yxati orqali ishlaydi. Ovoz havolalari `storage.googleapis.com` da (ruxsat berilgan). Boshqa saytlarga curl bilan chiqishga urinma; to'siq bo'lsa aylanib o'tma, egasiga xabar ber.
- GitHub: `add_repo` (owner `rahimjonovich2007-netizen`, repo `narxtili-videos`, access `push`), so'ng `git clone --depth 1 https://github.com/rahimjonovich2007-netizen/narxtili-videos /home/claude/narxtili-videos` (timeout 10 daqiqa), so'ng `register_repo_root`.
- Ishchi papka: `/home/claude/narxtili/dayNN/` (repo tashqarisida). `in/`, `work/`, `out/` shu yerda.

## Bosqichlar (har video uchun)
0. **Kontekst.** Repoga qarab `LOG.md` ni o'qi (qaysi ko'rinishlar ishlatilgan) va `scripts/dayNN.md` dagi stsenariyni ol. Bugungi sanani `current_time` bilan tekshir. Metricool'da shu kunga post allaqachon bor-yo'qligini `getScheduledPosts` bilan ko'r (takror post qilma).
1. **Faktlarni tekshir** (WebSearch). Stsenarida "Tekshiruv" qatori nimani ochib tekshirishni aytadi. Raqam/muallif/yil manbadan tasdiqlanmasa, jumlani yumshat yoki olib tashla. Caption oxiriga `Manba:` qatori (tadqiqotga asoslangan da'volar uchun).
2. **Nutq matni.** Stsenariy qadamlari = ovoz matni (aynan shu matn ekranda ham). Raqamlarni so'z bilan yoz ("yuz o'n ming", "o'n foiz", "to'qson to'qqiz ming"), chunki TTS raqamni noto'g'ri o'qishi mumkin. Gaplar nuqta/so'roq bilan tugasin (kit gaplarni shu bo'yicha ajratadi). Ovoz 22-32 soniya.
3. **TTS (Speko).** `mcp__Speko__audio_synthesize` (ToolSearch bilan yukla), body:
   `{"text": "...", "intent": {"language":"uz","region":"UZ","optimizeFor":"accuracy"}, "voice":"Orus", "constraints":{"allowedProviders":{"tts":["google-tts:gemini-3.8-flash-tts"]}}}`
   **Natija satrida "google-tts gemini-3.8-flash-tts" yozilgan bo'lishi SHART.** Pin qat'iy emas: agar "elevenlabs" (yoki boshqa) chiqsa, o'zbekchani buzadi, u faylni ISHLATMA, qayta urin (3 martagacha). Hech biri ishlamasa, to'xta va egasiga `SendUserMessage` bilan yoz.
   Havola (15 daqiqa amal qiladi) `storage.googleapis.com` da: `curl -sS -o DAYDIR/in/voice.wav '<url>'`.
4. **STT tekshiruvi + vaqtlar.** `mcp__Speko__audio_transcribe` (`audio_url` = o'sha havola, `language:"uz"`, `word_timestamps:true`). Matnni stsenariy bilan solishtir (xato o'qilgan so'z bo'lsa, qayta sintez qil). `words` massivini `DAYDIR/in/words.json` ga `[[text,start_ms,end_ms],...]` ko'rinishida yoz (raqamlar raqam bilan yoziladi, bu normal).
5. **Ovoz tayyorlash:** `python3 kit/audio.py DAYDIR`. Jimliklar qisqartiriladi, EQ + kompressor, `work/timing.json` yoziladi va **so'zlar/gaplar indekslari + vaqtlar chop etiladi**. Sahnalarni shu vaqtlarga bog'la (`tim.S(k)`, `tim.ws(i)`, `tim.find("so'z")`).
6. **Dizayn.** `DAYDIR/scenes.py` yoz (`days/day03/scenes.py` to'liq namuna, `examples/day01_visuals_standalone.py` matnli uslub namunasi). `build(tim)` -> `Reel(...)` qaytaradi.
7. **Musiqa + miks:** `python3 kit/music.py DAYDIR --style pluck|arp|keys --bpm N --prog "Dm Bb F C" --seed N`, so'ng `python3 kit/mix.py DAYDIR` (-14 LUFS, TP -1.5). Har video uchun **boshqacha** style/bpm/akkord/seed tanla.
8. **Ko'zdan kechir:** `python3 kit/render.py DAYDIR stills t1 t2 ...` (taxminan 12-16 kadr, har sahna boshida/o'rtasida/oxirida), PNG larni `Read` bilan KO'R: matn xatosi, chegaradan chiqish, ustma-ust tushish, bo'sh kadr. Muammoni tuzat, qayta tekshir.
9. **Render:** `nohup python3 kit/render.py DAYDIR full dayNN <cover_t> > work/render.log 2>&1 &` (taxminan 2-5 daqiqa; fonda ishga tushir va `ls`/`tail` bilan kuzat, foreground buyruq 10 daqiqadan oshsa o‘ldiriladi). `cover_t` = hook eng yaxshi ko'rinadigan soniya (1.5-3.0).
10. **Sifat darvozasi:** `python3 kit/qa.py DAYDIR/out/dayNN.mp4 DAYDIR/qa` hamma PASS bo'lsin va `DAYDIR/qa/qa_sheet.png` ni `Read` bilan ko'rib chiq. Ovoz so'zlari va ekrandagi matn mos ekanini tekshir.
11. **Arxiv + havola:** `python3 kit/publish.py --repo /home/claude/narxtili-videos --day N --mp4 ... --cover ... --daydir DAYDIR --msg "Day N: <mavzu>" --trailer "<sessiyangizdagi attribution qatorlari>"`. Skript push qiladi va `VIDEO_URL`/`COVER_URL` chop etadi (200 va hajm mos kelguncha kutadi). Push rad etilsa (403): Claude GitHub App repoga o'rnatilmagan, egasiga xabar ber.
12. **Metricool:** `createScheduledPost` (blogId `7935375`, `date` = `2026-MM-DDT19:30:00+05:00`), `info` = `kit/metricool_post.json` shabloni (VIDEO_URL, COVER_URL, DATETIME, CAPTION ni to'ldir). Caption = stsenariydagi Caption + (bo'lsa) `\n\nManba: ...` + `\n\n` + 4 ta heshteg. `isAiGenerated: true` (sintetik ovoz). Keyin `getScheduledPosts` bilan post vaqti, media va caption to'g'riligini tekshir.
13. **Egasiga yubor:** `SendUserFile` bilan MP4 va muqova JPG + qisqa o'zbekcha xabar (nima haqida, qaysi vaqtga rejalashtirilgan, qanday dizayn).
14. **Jurnal:** `LOG.md` ga qator qo'sh (kun, mavzu, tema/fon/overlay, musiqa parametrlari, vizual metafora, Metricool post id), `git commit` + `git push` (publish.py dan keyin alohida commit).

## Dizayn qoidalari (har video bir-biriga O'XSHAMASIN)
Egasining talabi: **har bir videoning dizayni va montaji boshqacha bo'lsin; keyingilari faqat raqam va matn emas, ANIMATSIYALI TUSHUNTIRISH bo'lsin.**
- Har video uchun yangi **vizual metafora**: ob'ektlar so'zlar bilan birga harakatlanadi va o'zgaradi (savat to'ladi, balon shishadi, tarozi og'adi, grafik chiziladi, odamlar/yuzlar, tangalar, narx yorliqlari, kalendar, shkala, chiziq bo'ylab harakat). Faqat matn chiqarma. Har gapga kamida bitta harakatlanuvchi ob'ekt.
- Ekrandagi matn qisqa (bir lavhada 8 so'zdan kam), stsenariy so'zlariga aynan mos. Muhim raqam/so'z so'z aytilayotgan paytda paydo bo'lsin.
- Hook (0-1.5 soniya): darhol harakat + katta matn. Montaj: har 1.5-3.5 soniyada sahna/kompozitsiya almashadi. Oxirida CTA animatsiyasi, so'ng brend kartasi.
- `LOG.md` dagi oldingi videolardan farq qil: **tema** (`navy|ink|slate|cream|amber`), **fon** (`radial|diag|top|spot|flat`), **overlay** (`dots|grid|diag|rings|none`), **musiqa** (style/bpm/akkord/seed), **vizual metafora**. Ketma-ket ikki videoda tema ham, musiqa ham bir xil bo'lmasin. Yangi ikonka/obyektlarni o'z `scenes.py` ingda PIL bilan chiz (kitda: tanga, balon, savat, yuz, odam, narx yorlig'i, sumka, strelka, belgi/xoch, chiziq `poly`, ustun `bar`).
- Dizayn eslatmasini `DAYDIR/design.md` ga yoz (3-5 qator: metafora, sahnalar, nima uchun).

## Xatolar bilan ishlash
- Biror bosqich ishlamasa, **noto'g'ri/buzuq video POST QILMA.** Sababni aniqla; 2 urinishdan keyin ham bo'lmasa, nima bo'lgani va nima kerakligini `SendUserMessage` bilan egasiga yoz (qisqa) va to'xta.
- Post vaqti o'tib ketgan bo'lsa (Metricool o'tmish sanani qabul qilmaydi), eng yaqin 19:30 (ertasi kun) ga rejalashtir va egasiga aytib o't.
- Videoni qayta rejalashtirish kerak bo'lsa `updateScheduledPost` (id o'zgaradi, uuid qoladi).

## Fayl xaritasi
- `kit/nt_kit.py` kutubxona (tema, matn, shakllar, ikonkalar, `Reel`, `render`); `kit/audio.py`, `kit/music.py`, `kit/mix.py`, `kit/render.py`, `kit/qa.py`, `kit/publish.py`; `kit/metricool_post.json` shablon.
- `scripts/` stsenariylar; `days/dayNN/` har kunning `scenes.py`, `design.md`, `timing.json`; `videos/dayNN.mp4/.jpg` tayyor videolar; `examples/` birinchi video (matnli uslub); `LOG.md` jurnal.
