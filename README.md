# Lift Tracker Exercise Audio

This repository stores ElevenLabs MP3 narration for the Lift Tracker exercise
catalog. Audio files are named by the stable exercise ID from
`Sources/LiftTrackerCore/Resources/exercises.json`, for example `0001.mp3`.

## Generate audio

From this directory, set the credentials in your shell. They are never stored in
the repository:

```sh
export ELEVENLABS_API_KEY="..."
export ELEVENLABS_VOICE_ID="..."
python3 generate-exercise-audio.py --limit 1
```

The default dataset is the Lift Tracker catalog and output goes to `audio/`.
The full catalog can be generated with:

```sh
python3 generate-exercise-audio.py
```

Useful options:

```sh
python3 generate-exercise-audio.py --exercise-id 0001 --exercise-id 0025
python3 generate-exercise-audio.py --limit 10
python3 generate-exercise-audio.py --overwrite
```

The script skips existing MP3s by default, so interrupted runs can safely be
resumed. Review generated files before committing them.