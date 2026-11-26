# SIRLI MAHALLA — seriya "bible"i (qoralama v1)

> Yangi loyiha (Narx Tili loyihasi to'xtatilgan). 30 kun · har kuni 1 qism · 45–60 soniya · o'zbek tilida · jumboq/sir janri · yangi Instagram akkaunt.

## 1. G'oya bir gapda
Chinor mahallasida har tun g'alati narsalar yuz beradi. Ikki o'smir — kuzatuvchi Jasur va muhandis Malika — mushuk Tuman bilan "daliillar"ni yig'ib, sirni 4 qismda yechadi. Har qism **klifhanger** bilan tugaydi, har hikoya oxirida **yangi sirning uchquni** bor.

## 2. Nega bu tuzilma o'sadi (Instagram mantig'i)
- **Ketma-ket qism = qaytib keladigan tomoshabin.** "2-qism ertaga 18:00" — obuna bo'lish uchun sabab.
- **Topishmoq = izoh.** Har qism oxirida savol ("Sizningcha kim?") — izohlar reach'ni oshiradi.
- **Adolatli ma'lumotlar.** Tomoshabin javobni ekrandagi "DALIL" kartalaridan topa oladi — qayta ko'rish (rewatch) bo'ladi.
- **Birinchi 3 soniya** — yarim yo'lda to'xtagan sirli jumla (hook), uzoq intro yo'q.
- Eski loyihadan olingan saboq: 1–2 obunachi bilan muammo ishlab chiqarish emas, **tarqatish**. Shuning uchun har qismda ulashishga sabab (jumboq), Trial Reels, qismlar o'rtasida o'zaro havola.

## 3. Dunyo va uslub
- **Joy:** xayoliy "Chinor mahallasi" — eski soat minorasi, soatsoz ustaxona, tandirli non do'koni, chinor daraxti, kutubxona.
- **Palitra:** tungi indigo + issiq qahrabo (chiroq nuri), alohida dalil uchun firozarang aksent. Premium nur, bokeh, ovozli hajmli yorug'lik (Narx Tili kit'dagi PremiumReel).
- **Animatsiya:** 2D, kod bilan chizilgan (PIL/numpy → ffmpeg 1080×1920@30), kamera siljishi, parallaks, lip-sync (ovoz → og'iz ochilishi), ko'z qisish, qo'l IK.
- **Epizod qolipi (50 s):**
  1. 0–3 s: HOOK (yarim ochilgan sir, bitta jumla)
  2. 3–8 s: "SIRLI MAHALLA · n-hikoya · k/4" sarlavha + 1 jumlalik eslatma (2–4-qismlarda)
  3. 8–40 s: 2–3 sahna, kamida **1 yangi DALIL** (ekranda karta)
  4. 40–48 s: burilish → klifhanger (freeze-frame)
  5. 48–50 s: savol + "keyingi qism ertaga 18:00"

## 4. Personajlar va ovozlar (Speko · Gemini TTS)
| Personaj | Kim | Ovoz (variant) |
|---|---|---|
| **Jasur** (15) | kuzatuvchi, daftarcha, "raqamlar" odami | Puck (expressive male) |
| **Malika** (15) | muhandis qiz, asboblar sumkasi, mantiqiy | Zephyr (bright female) |
| **Ustoz Karim** (68) | soatsoz, kamgap, sirli | Charon (deep male) |
| **Hilola xola** (55) | do'konchi, ko'p gapiradi, "arvoh" tarafdori | Kore (warm female) |
| **Tuman** | kulrang mushuk, dalil topuvchi | ovozsiz (miyov SFX) |
| **Hikoyachi** | qisqa hook / eslatma | Aoede (calm narrator) |

Eslatma: ovozlarning o'zbekchada sifati har biri uchun alohida sinab ko'riladi (STT tekshiruvi), mos kelmagan bo'lsa almashtiramiz. Provayder doim `google-tts:gemini-3.8-flash-tts` bo'lishi shart.

## 5. 30 kunlik xarita
| Kun | Hikoya | Qismlar |
|---|---|---|
| 1–4 | **1. Soat 03:07** — soat nega har tun to'xtaydi? | 4 |
| 5–8 | **2. Chinor tagidagi sir** — konvertdagi "uch qadam" xaritasi | 4 |
| 9–12 | **3. Ovoz kim?** — mahalla karnayida ertalab g'alati ovoz | 4 |
| 13–16 | **4. Yo'qolayotgan nonlar** — Hilola xola tandiridan non g'oyib (Tuman gumon ostida) | 4 |
| 17–20 | **5. Qora xatlar** — pochta qutilarida topishmoqli xatlar | 4 |
| 21–24 | **6. Akslar maktabi** — kutubxonadagi ko'zgu va teskari yozuv | 4 |
| 25–28 | **7. Oxirgi xona** — kutubxonaning qulflangan xonasi; oldingi dalillar birlashadi | 4 |
| 29 | Jasur daftari — qisqa eslatma + 2-fasl uchun ovoz berish | 1 |
| 30 | Finale-teaser — 2-fasl e'loni | 1 |

## 6. Ishlab chiqarish rejasi
1. **Personaj tizimi:** `nt_char.Host`ga yangi palitralar + stillar (yosh bola/qiz, soqolli/mo'ylovli keksa, ro'mol, ko'zoynak, doppi), bir kadrda 2–3 personaj (`cx`, `sc` bilan joylash), mushuk uchun alohida sprite.
2. **Sahna kutubxonasi:** tungi ko'cha, minora (ichi/tashqi), ustaxona, xona — qayta ishlatiladigan fon qatlamlari.
3. **Ovoz:** personaj va qism bo'yicha bitta TTS chaqiruvi (qatorlar uzun pauza bilan ajratiladi) → STT bilan kesish → har personaj uchun alohida lip-sync envelope. Musiqa: kichik minor-pentatonik mavzu + har personaj uchun motiv, sfx.
4. **QA darvozasi:** `qa.py` ALL PASS bo'lmasa joylanmaydi (hajm < 90 MB, ovoz −14 LUFS / TP −1.5, 1080×1920@30, davomiylik 45–60 s).
5. **Joylash:** yangi akkaunt Metricool'ga ulangach — `createScheduledPost` (REEL, `isAiGenerated: true`), kunlik 18:00 Toshkent (Metricool brendining vaqt zonasi bilan tekshiriladi).
6. **Tezlik:** oldindan 4–5 qism zaxira tayyorlanadi, keyin kunlik rejalashtirilgan vazifa keyingi qismlarni oldinga tayyorlab boradi.

## 7. Boshqa shartlar
- Hamma kontent original (mavjud personaj/animatsiya nusxasi yo'q), zo'ravonlik/qo'rqinchli sahnalar yo'q — "sirli", lekin oila uchun xavfsiz.
- Instagram'da "AI yordamida yaratilgan" belgisi yoqilgan holda.
- Repo hozir ochiq (public): maxfiy kalitlar va akkaunt ma'lumotlari hech qachon yozilmaydi.
