# Pitch deliverables

- `SOVRIVA_VIDEO_PITCH.md` — approved narration, timing, and visual storyboard.
- `RECORDING_AND_EDITING_CHECKLIST.md` — capture and quality checklist.
- `SOVRIVA_Pitch_Visual_Draft.mp4` — 2:43 visual draft with PPT-style cards, real dashboard captures, and extension controls.
- `SOVRIVA_Pitch_Final.mp4` — 2:43 pitch with captions and locally generated narration based on the supplied voice sample.
- `SOVRIVA_InnovateX_Pitch_Final.mp4` — 2:55 InnovateX version using the supplied story structure, polished cards, dashboard footage, extension footage, captions, and locally generated narration.
- `SOVRIVA_InnovateX_Captions.srt` — captions for the InnovateX version.
- `render_innovatex_cards.py` and `innovatex_cards/` — dependency-free source for the PPT-style visual cards.
- `SOVRIVA_Pitch_Captions.srt` — timed captions for the approved narration.
- `mux-founder-voice.ps1` — adds the founder's recorded narration to the visual draft.

The visual draft intentionally contains a silent audio track. The final file uses a local OpenVoice conversion based on the supplied 56-second sample; no voice file or model checkpoint is stored in the repository. If a fully human recording is preferred later, `mux-founder-voice.ps1` can replace the generated narration.
