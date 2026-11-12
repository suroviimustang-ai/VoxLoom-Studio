# Architecture

The Qt window owns an immutable original audio array and a separate processed
array. Audio contracts are float32, samples × channels, 1–8 channels. Selected
intervals use the original timeline; processing must preserve shape and duration.

Every decoding, restoration, detection, ASR and export operation runs in a
disposable QProcess. The parent exchanges JSON metadata and NumPy arrays through
a private temporary directory. Loading arrays disables pickle. Process failures,
invalid responses and cancellation settle the job and restore the controls.

Silero VAD finds speech intervals. FlexSED is an optional description-driven
event detector with its own trained decoder, Dasheng encoder and CLAP text
encoder. English queries can locate events in Russian audio. Start with
`Speech; Conversation; Whispering`; labels and scores require listening checks.
FlexSED does not clean audio or transcribe words. It processes channels separately
at 16 kHz in blocks up to ten seconds, with final padding only to a 40 ms frame.

RNNoise and DeepFilterNet3 operate at their internal sample rates and return a
duration-matched copy. Spectral Gate is DSP and has no learned weights. Whisper
base/small/large-v3-turbo use CPU INT8 with local files only. No key is required.

Audio and text exports use temporary files and replacement. Runtime diagnostics
are local and bounded. The original file is protected in the UI. Playback can
mix multichannel files for monitoring; VAD uses channels separately and Whisper
selects the highest-energy channel. Streaming capture and speaker identity are
outside the current version.
