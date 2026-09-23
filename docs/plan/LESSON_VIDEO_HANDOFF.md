# Lesson video handoff

Video binaries should not be committed to this repository. Keep master files in a
local project-media folder or shared private drive until the delivery provider is
chosen. Git should contain only reviewed metadata, captions/transcripts where
appropriate, poster assets, and stable playback references.

## Proposed Lesson 1 package

```text
n1-lesson-01-v1-master.mp4
n1-lesson-01-v1-captions-en.vtt
n1-lesson-01-v1-transcript.md
n1-lesson-01-v1-poster.webp
n1-lesson-01-v1-video.json
```

The application does not require these files yet. This naming scheme prevents a
new lesson edit from silently replacing an earlier published revision.

## Metadata to collect while producing the video

```json
{
  "schema_version": "1.0.0",
  "video_key": "n1-lesson-01-video-01",
  "lesson_key": "n1-lesson-01",
  "lesson_revision": 1,
  "title": "Primes and prime factorisation",
  "duration_seconds": null,
  "source_filename": "n1-lesson-01-v1-master.mp4",
  "source_sha256": null,
  "poster_filename": "n1-lesson-01-v1-poster.webp",
  "caption_tracks": [
    {
      "language": "en-SG",
      "kind": "captions",
      "format": "webvtt",
      "filename": "n1-lesson-01-v1-captions-en.vtt"
    }
  ],
  "transcript_filename": "n1-lesson-01-v1-transcript.md",
  "delivery": {
    "provider": null,
    "playback_reference": null,
    "access": null
  }
}
```

Leave provider and playback fields blank until hosting is decided. Do not place a
private upload URL, API key, signed playback token, or storage credential in this
file.

## Review before application handoff

- Spoken Mathematics matches the approved lesson outcome.
- On-screen notation and transcript use the same terms and symbols.
- Captions include meaningful spoken and non-speech information.
- The transcript is readable without watching the video.
- Any worksheet/example shown in the video has an approved source revision.
- The opening frame and poster communicate the lesson title clearly.
- The final duration and SHA-256 are recorded.

Once the host is chosen, the backend video contract can be finalised without
re-encoding or reauthoring the lesson.
