# Non-negotiable rules (every video)

1. RESPECT RULE. ONLY the Prophet Muhammad (peace be upon him) and the Sahaba, his Companions of the 7th century CE (e.g.
   Abu Bakr, Umar, Uthman, Ali, Khalid ibn al-Walid, Sa'd ibn Abi Waqqas, Mu'awiya), are NEVER shown with a face: their medallion is
   noor light. The engine does this automatically; set noor=True on any other Companion it misses. Never use a PLATE that shows them.
   Everyone later - Umayyad and Abbasid caliphs after the Companions, Ottoman sultans, Safavid shahs, ayatollahs, scholars,
   kings - is shown NORMALLY with a real period portrait (Wikimedia Commons, licence-safe). No crest, no light for them.
2. ACCURACY. Dates, names, numbers from reliable sources (encyclopaedias, academic books). Say "perhaps", "about" for
   uncertain numbers. Current events: flag them ONGOING (ONGOING card) and keep neutral wording. List sources in the json.
3. NO INVENTED FACES. A person with no public-domain likeness gets a heraldic crest medallion (image=None), not an AI face.
4. IMAGES only via `pipeline/tools/commons.py` (public domain / CC0 / CC BY / CC BY-SA; credit is saved automatically and
   printed in the description). Never use another YouTuber's artwork or thumbnails.
5. NARRATION. One continuous voice pass, no added pauses. Every visual is cued to a spoken phrase. Every foreign name
   that Edge mispronounces goes in "say" (respelling); check flags candidates.
6. AUDIO (make_video.sh does it; do not change): narration -14 LUFS, music 20 dB under the voice, SFX bus -7 dB with
   speech-band EQ dip and hard ducking so the voice is ALWAYS clear. Era-appropriate sounds only: no gunfire before
   gunpowder armies, never meme sounds. `qa.py audio` must pass.
7. CAMERA. Long jumps use 'cut' (dissolve); check reports whip pans. Map quality never drops: detail atlases are
   generated automatically for every close camera view.
