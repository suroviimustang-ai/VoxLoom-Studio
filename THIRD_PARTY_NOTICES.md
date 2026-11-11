# Компоненты VoxLoom Studio

Новый проект MatSoftAI. Интерфейс создан отдельно по рабочим принципам Keyboard_Lab:
транспорт, временная шкала, выделения и таблица событий. Прямых runtime-зависимостей
от Keyboard_Lab и SpeechCleaner нет. Концепция look-ahead limiter адаптирована из
`SpeechCleaner-Avalonia/app/dsp/limiter.py`: добавлено общее управление усилением каналов.
Подход к ресемплингу нейросетевых backend также опирается на SpeechCleaner.

Сторонние библиотеки и веса сохраняют свои лицензии. Тексты доступных лицензий
собираются из установленных дистрибутивов в `licenses/`; версии — в
`licenses/dependencies.json` и `requirements-lock.txt`.

- PyQt6: GPLv3 / коммерческая лицензия Riverbank. Эта сборка использует публичную GPL-версию.
- Qt: лицензии соответствующих модулей в дистрибутиве PyQt6-Qt6.
- noisereduce: MIT, https://github.com/timsainb/noisereduce
- DeepFilterNet: MIT / Apache-2.0, https://github.com/Rikorose/DeepFilterNet
- RNNoise: BSD-3-Clause, https://github.com/xiph/rnnoise
- pyrnnoise: https://github.com/pengzhendong/pyrnnoise
- Silero VAD: MIT, https://github.com/snakers4/silero-vad
- faster-whisper: MIT, https://github.com/SYSTRAN/faster-whisper
- Whisper: MIT, https://github.com/openai/whisper
- CTranslate2: MIT, https://github.com/OpenNMT/CTranslate2
- ONNX Runtime: MIT, https://github.com/microsoft/onnxruntime
- PyAV и входящие библиотеки FFmpeg: лицензии конкретной бинарной поставки.
- NumPy, SciPy, soundfile, sounddevice, pyloudnorm, PyTorch: тексты в `licenses/`.

При внешнем распространении нужны соответствующие исходники/уведомления для
компонентов с copyleft, включая PyQt. Этот файл не перелицензирует зависимости.
# FlexSED addition

FlexSED inference sources: JHU-LCAP/FlexSED, copyright (c) 2025 Jiarui Hai,
MIT; license retained in licenses/FlexSED/LICENSE. Checkpoint Higobeatz/FlexSED
is tagged MIT by its publisher. Pinned versions and SHA-256 are recorded in
licenses/FlexSED/provenance.json and models/flexsed/manifest.json.
The CLAP text encoder is derived from laion/clap-htsat-unfused; its model card
is retained in licenses/CLAP/README.md. Transformers is Apache-2.0 and einops MIT;
installed distribution notices are collected by tools/collect_licenses.py.

