---
name: sb-parse-whisper
user-invocable: false
description: Parse Whisper transcription files (.whisper ZIP archives) into readable text with speaker labels and timestamps.
---

# Parse Whisper Transcript

## Input

A path to a `.whisper` file. This is a ZIP archive containing `metadata.json`.

## Workflow

### 1. Extract the ZIP

Use Bash to extract and read `metadata.json` from the ZIP:

```bash
python3 -c "
import zipfile, json, sys

with zipfile.ZipFile(sys.argv[1], 'r') as z:
    with z.open('metadata.json') as f:
        data = json.load(f)
        print(json.dumps(data, indent=2))
" "/path/to/file.whisper"
```

> [!WARNING]
> The JSON can be very large (200k+ tokens). Do NOT dump the full JSON. Use the extraction script below to get only the transcript segments.

### 2. Extract transcript segments

Use this script to extract a clean, readable transcript:

```bash
python3 -c "
import zipfile, json, sys

def ms_to_time(ms):
    s = ms // 1000
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'

with zipfile.ZipFile(sys.argv[1], 'r') as z:
    with z.open('metadata.json') as f:
        data = json.load(f)

prev_speaker = None
for seg in data.get('transcripts', []):
    text = seg.get('text', '').strip()
    if not text:
        continue
    speaker_info = seg.get('speaker', {})
    speaker = speaker_info.get('name', 'Unknown')
    # Normalize Kenzo's microphone
    if speaker in ('Microphone', 'Kenzo'):
        speaker = 'Kenzo'
    start = ms_to_time(seg.get('start', 0))
    if speaker != prev_speaker:
        print(f'\n[{start}] **{speaker}**:')
        prev_speaker = speaker
    print(f'{text}')
" "/path/to/file.whisper"
```

### 3. Output format

The output should be a markdown document with this structure:

```markdown
# Transcript: {original_media_filename}

**Bron:** {path_to_whisper_file}
**Duur:** {formatted_duration}

---

[00:00:32] **Kenzo**:
Segment tekst hier.

[00:01:15] **Speaker 1**:
Andere segment tekst.

[00:02:30] **Kenzo**:
Nog een segment.
```

## Audio Reality

See `references/whisper-format.md` for details on speaker label reliability.

- "Kenzo" is reliably identified (microphone channel)
- All other speakers are from a single Teams audio stream — diarization is best-effort
- Do NOT attribute specific statements to named individuals based solely on speaker labels
