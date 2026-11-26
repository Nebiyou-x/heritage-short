# Ethics, consent, licensing, and disclosure

This document describes the sample project and operational safeguards. It is
not legal advice; confirm rights and platform rules for the intended
distribution territory and channel.

## People, likeness, and voice

The sample characters—Uncle Tadesse and his niece—are fictional. The current
storyboard is not intended to depict or identify a real person, and Gemini TTS
uses a configured provider voice rather than cloning a family member's voice.
The supplied project reflection confirms that no real person was intended to
be shown or voiced. No individual consent record applies to the fictional
sample; generated outputs should still be reviewed for unintended recognizable
likenesses before release.

If a later version uses a real person's image, likeness, personal story, or
voice:

- Obtain documented, informed permission before sending source material to a
  model provider or generating the likeness/voice.
- Explain the planned use, audience, duration of use, provider processing,
  storage/retention, and whether the content may be published or monetized.
- Confirm the person can decline or withdraw permission where practicable.
- Do not use voice replication or custom voice features without the speaker's
  explicit permission and provider-policy compliance.
- Keep evidence of consent securely and outside public prompts, source control,
  and `runs.jsonl`.

The fictional niece is described as a child character. Do not base her
appearance, voice, or story on a real minor without the appropriate informed
guardian permission and safeguards.

## Personal information and provider data

Production sends keyframe prompts to Cloudflare Workers AI and narration text,
voice choice, and style direction to Gemini. Treat those prompts and transcripts
as data disclosures to external services. The sample story contains invented
details, but future authors should:

- Remove private family details, contact information, locations, and other
  personally identifiable information unless needed and explicitly approved.
- Read the providers' current privacy, retention, training, and regional
  processing terms before production.
- Use only the minimum content necessary for generation.
- Keep API tokens in local `.env` or a managed secret store. Never commit them,
  put them in the storyboard, include them in logs, or paste them into chat.
- Restrict access to generated files and logs; prompts and transcripts may
  themselves contain sensitive information.

## Copyright and licences

The project owner must verify the current terms and output-use rights for each
provider/model and any local assets. The pipeline does not perform legal or
copyright review. The repository does not yet record a verified license/terms
statement for each generated model and output:

| Asset/model | Current evidence | Rights status |
|---|---|---|
| Cloudflare-hosted `@cf/black-forest-labs/flux-1-schnell` keyframes | Model name and provider are recorded in the architecture and run log. | Applicable model and output terms have not been recorded here; verify the terms in effect for the account and generation date. |
| Google Gemini `gemini-3.8-flash-tts` narration | Model name is recorded in the architecture and run log. | Applicable service and output terms have not been recorded here; verify the terms in effect for the account and generation date. |
| Music in the current production manifest | The manifest declares “ACE-Step 1.5 open-weight output,” while the run log identifies the staged source file as `mixkit-game-show-suspense-waiting-667.wav`. | Provenance and license are unresolved. The declaration alone is not evidence that the file is ACE-Step-generated or that it is licensed for the intended use. Verify the source and retain its applicable license before publication. |
| FFmpeg-rendered video, subtitles, and end card | Produced locally from the storyboard and generated/staged inputs. | No separate output license has been documented; rights depend on all included inputs and applicable provider terms. |

Do not treat “open-weight output” or a license name entered in `.env` or the
manifest as proof of the source model, ownership, or publication rights.

The production soundtrack must be a track the user has permission to use for
the intended distribution, including any needed synchronization, adaptation,
commercial, and platform rights. Set `MUSIC_LICENSE` in `.env` to document the
rights basis and optionally set `MUSIC_ATTRIBUTION`. These fields are records
supplied by the operator; the software does not validate the license or prove
ownership.

Keep receipts, license files, source/creator attribution, and permission
records in a suitable private or project-controlled location. Do not rely on a
provider free tier as proof that an output is unrestricted.

## Cultural and language review

Amharic narration, English subtitles, humor, character depiction, and cultural
details need review by people familiar with the language and context. TTS may
mispronounce names or flatten emotion; a technically valid WAV is not evidence
of a respectful or accurate performance. Review:

- Amharic spelling, meaning, pronunciation, dialect, and naturalness.
- English subtitle accuracy, reading speed, line breaks, and timing.
- Whether the Addis Ababa setting, family relationships, clothing, and humor
  are represented respectfully and as intended.
- Whether the image model introduces stereotypes, unintended objects, or
  inconsistent character details.

Correct the source storyboard and rerun affected stages rather than accepting
harmful or misleading output.

## Labelling, provenance, and publication

Production exports include a visible four-second end card reading
“Made with AI / Heritage Short.” The operator must also use any applicable
platform AI-content disclosure controls and provide additional context when a
platform or audience needs it.

The pipeline records inputs, model names, cache keys, parameters, seeds where
available, attempt outcomes, and output paths in a local manifest and JSONL
log. These records are useful provenance notes, not cryptographic proof. The
current code does not create C2PA/SynthID credentials or guarantee preservation
of provider metadata through FFmpeg encoding.

Before publication, inspect both aspect ratios, confirm the disclosure is
visible, and check that captions and audio remain accessible and intelligible.
Do not present generated narration, images, or events as documentary evidence
of real people or events.

## Accountability

The project operator is responsible for:

- Reviewing generated content and deciding whether it is fit to publish.
- Maintaining consent and rights evidence.
- Configuring provider billing alerts/limits; the runner has no hard dollar cap.
- Correcting inaccurate or harmful output and responding to removal requests.
- Retaining only the outputs, prompts, and logs necessary for the work.
