# Whisper File Format

`.whisper` files are ZIP archives containing a single `metadata.json` file.

## JSON Structure

```json
{
  "translatedFullText": {},
  "modelEngine": "whisperKit",
  "originalMediaFilename": "2026-05-06 14.28.34 Microphone",
  "startTimeOffset": {"seconds": 0, "milliseconds": 0, "hours": 0, "minutes": 0},
  "transcripts": [
    {
      "id": "UUID",
      "start": 1900,
      "end": 19560,
      "text": "Segment text here.",
      "favorited": false,
      "unEven": false,
      "speaker": {
        "id": "UUID",
        "name": "Speaker 1",
        "color": 0
      },
      "words": [
        {
          "startTime": 1900,
          "endTime": 3300,
          "text": " Word"
        }
      ]
    }
  ]
}
```

## Speaker Labels

- `"Microphone"` or `"Kenzo"` = Kenzo (reliable)
- All other speakers = Teams audio stream (unreliable diarization)
- Speaker names are generic: "Speaker 1", "Speaker 2", etc.
- Do NOT rely on speaker separation for attributing statements to specific people

## Timestamps

- `start` and `end` are in milliseconds
- Convert to `HH:MM:SS` for readable output
