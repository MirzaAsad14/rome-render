# ChatGPT (Custom GPT / Project) setup
1. Create a GPT or Project. Instructions: paste CLAUDE.md, then workflow/RULES.md and workflow/QUALITY.md.
2. Knowledge: upload pipeline/templates/story_template.py, pipeline/episodes/demo_chaldiran.py and .json, workflow/*.md.
3. Ask: "Make a 10-minute video about <topic>". ChatGPT writes <slug>.json and <slug>.py (storyboard data).
4. On your computer in this folder: `bash setup.sh`, then `python pipeline/voice.py pipeline/episodes/<slug>.json`,
   `python produce.py check <slug>` - paste the output back to ChatGPT until 0 errors - `python produce.py preview <slug>`
   (upload sheet.jpg to ChatGPT for review), then `python produce.py build <slug>`.
Codex CLI / Claude Code / Cursor can run all of this themselves (they read AGENTS.md / CLAUDE.md).
