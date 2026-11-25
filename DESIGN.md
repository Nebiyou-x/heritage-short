# Design

## Creative premise

The sample is a fictional Amharic family comedy titled “My Uncle's First
Computer.” Uncle Tadesse buys a computer and treats the unfamiliar interface
with complete confidence. A sequence of small mishaps escalates until his
ten-year-old niece fixes an upside-down display with two keys; he immediately
claims that was his plan all along.

The script is organized as eight storyboard shots, each with a reason for its
place in the story, a keyframe prompt, a motion prompt, Amharic narration, an
English subtitle, and a deterministic seed. The sequence establishes the room
and character, introduces the mouse and password gags, turns the screen upside
down, brings in the niece, resolves the problem, and lands the punchline.

The characters are fictional. The story is not intended to portray a specific
real family or to reproduce a real person's voice or likeness.

## Visual direction

The storyboard sets a warm, stylized Addis Ababa living room in golden morning
light, with expressive faces, clean lines, rich colors, and a recurring
character reference. The global style and character description are included
in every keyframe request so each shot has consistent prompt context. Per-shot
seeds are sent to the image provider for repeatability where supported.

The sample asks for both 16:9 and 9:16. The production renderer generates each
keyframe once, then creates a centered crop and a slow Ken Burns zoom for each
format. This is intentionally a simple, reproducible motion treatment: the
current renderer does not follow each storyboard `motion_prompt`, animate
characters, synthesize camera movement, or generate Wan video.

The vertical crop is center-based. A human review is necessary to ensure faces,
hands, and important props remain visible in both versions. If a composition
fails in one format, revise the image prompt or source keyframe rather than
assuming the crop will adapt intelligently.

## Narration and subtitles

The spoken track is Amharic and comes from the storyboard's `narration_am`
field. Gemini TTS voice and delivery style are configurable; the default voice
is `Kore` and the default style asks for warm, conversational storytelling.
The model returns WAV audio for each shot. The stage rejects narration whose
measured duration exceeds that shot's duration by more than 0.25 seconds,
preventing the final edit from silently cutting off words.

English subtitle text is authored alongside each Amharic line in
`subtitle_en`. It is timed to the shot boundaries and burned into the story
portion of each export. This automatic timing is a first pass, not word-level
captioning; a speaker of Amharic and English should review meaning, line breaks,
reading speed, and synchronization.

## Score and sound

The storyboard describes a playful instrumental score and its tempo. In the
current production path, that description is creative guidance only: the
pipeline does not synthesize music. Instead, the user supplies one licensed
audio file through `MUSIC_FILE`; the declared license and optional attribution
are recorded in the manifest and run log.

The soundtrack is looped or trimmed to cover the story, reduced in level,
ducked under narration with FFmpeg sidechain compression, and faded out over
the final two seconds of the story. The final mix is loudness-normalized to
−14 LUFS and a −1 dB true-peak ceiling. These are technical targets; listening
tests on real speakers/headphones are still required.

## Delivery intent

The final edit is intended to:

- Last 60–90 seconds including its four-second end card.
- Provide both 1920×1080 landscape and 1080×1920 portrait MP4s.
- Include Amharic narration, readable English subtitles, and one licensed score.
- Finish with a visible “Made with AI” disclosure.
- Include an edit manifest and run records describing inputs and processing.

The current storyboard totals 69 seconds; the end card brings each export to
73 seconds. The pipeline can verify stream presence, dimensions, and duration,
but cannot judge story clarity, cultural accuracy, pronunciation, visual
continuity, licensing, or platform suitability. Those remain human approval
checks before publication.
