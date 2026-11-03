# Pitch deliverables

- `SOVRIVA_VIDEO_PITCH.md` — approved narration, timing, and visual storyboard.
- `RECORDING_AND_EDITING_CHECKLIST.md` — capture and quality checklist.
- `SOVRIVA_Pitch_Visual_Draft.mp4` — 2:43 visual draft with PPT-style cards, real dashboard captures, and extension controls.
- `SOVRIVA_Pitch_Final.mp4` — 2:43 pitch with captions and locally generated narration based on the supplied voice sample.
- `SOVRIVA_Pitch_Captions.srt` — timed captions for the approved narration.
- `mux-founder-voice.ps1` — adds the founder's recorded narration to the visual draft.

The visual draft intentionally contains a silent audio track. The final file uses a local OpenVoice conversion based on the supplied 56-second sample; no voice file or model checkpoint is stored in the repository. If a fully human recording is preferred later, `mux-founder-voice.ps1` can replace the generated narration.
