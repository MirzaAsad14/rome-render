# Rendering long videos (render takes ~1-3 CPU-seconds per frame; 20 min at 24 fps = 28,800 frames)

On one computer: `python produce.py build <slug>` uses all cores (8 cores ~ 2-3 h for 20 min).

Split across machines / free notebooks (Kaggle CPU sessions have 4 cores and 12 h; Colab works too):
1. Locally run voice + check + preview so build/<slug>/ has words.json, narration.wav and the cached atlases.
2. Zip the whole folder, upload it as a Kaggle Dataset (or to Google Drive for Colab).
3. In each notebook:  `!cp -r /kaggle/input/<dataset>/history-map-studio /kaggle/working/ && cd /kaggle/working/history-map-studio
   && pip -q install -r pipeline/requirements.txt && python produce.py part <slug> 0/4`   (next notebook 1/4, 2/4, 3/4)
   Each writes pipeline/build/<slug>/part_<i>.mp4 - download it into the same place locally.
4. Locally: `python produce.py join <slug> 4` -> joins the parts, mixes audio, runs audio QA.
