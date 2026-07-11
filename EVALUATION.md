### Hindi/English Code-Mixing — Additional Data Point (Jul 11)

Ran `audio-in-hindi-2_SRhbcHI0.wav` (short clip, ~60s) through the full pipeline
with `small` model. Whisper correctly detected `hi` (Hindi) with 0.98 confidence,
but output quality was poor — much of the transcribed text reads as garbled/
hallucinated Devanagari rather than coherent Hindi, with occasional stray English
words bleeding through ("light", "idiot").

This is a second, independent data point supporting the earlier finding from the
37-min clip: language detection itself works correctly, but transcription quality
degrades significantly on code-switched or code-mixed audio — a code-mixing
failure, not a language-detection failure. Reinforces the case for English-only
v1 scoping, with multilingual support deferred to stretch goals.