<p align="center">
  <img src="assets/voxloom.png" width="112" alt="VoxLoom Studio logo">
</p>

<h1 align="center">VoxLoom Studio</h1>

<p align="center"><a href="README.md">English</a> | <strong>Русский</strong></p>

<p align="center">
  Очистка аудио, поиск речи и расшифровка фрагментов — локально на вашем компьютере.
  <br>
  Offline audio restoration, speech detection and transcription.
</p>

<p align="center">
  <a href="docs/BUILDING.ru.md">Собрать приложение</a> ·
  <a href="docs/DOWNLOADS.ru.md">Скачать и установить</a> ·
  <a href="#возможности">Возможности</a> ·
  <a href="docs/ARCHITECTURE.md">Архитектура</a> ·
  <a href="CONTRIBUTING.md">Участие</a> ·
  <a href="https://github.com/suroviimustang-ai/VoxLoom-Studio/issues">Сообщить об ошибке</a>
</p>

<p align="center">
  <a href="https://github.com/suroviimustang-ai/VoxLoom-Studio/actions/workflows/ci.yml"><img src="https://github.com/suroviimustang-ai/VoxLoom-Studio/actions/workflows/ci.yml/badge.svg" alt="Native platform checks"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--only-blue" alt="License: GPL-3.0-only"></a>
  <a href="docs/BUILDING.ru.md"><img src="https://img.shields.io/badge/Python-3.11-blue" alt="Python 3.11"></a>
</p>

![Интерфейс VoxLoom: исходная и обработанная дорожки, метки речи и текст](assets/screenshots/workspace.png)

*VoxLoom 0.2.2, рабочая область 1366×768. Синтетическая демонстрационная дорожка
и пример текста показывают интерфейс, а не качество распознавания.*

**Готовые приложения и отдельные пакеты моделей публикуются в
[GitHub Releases](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases).**
Выберите EXE для Windows, AppImage для Linux или DMG для macOS Apple Silicon,
затем установите нужные модели через «Модели → Установить пакет».
[Инструкция установки](docs/DOWNLOADS.ru.md). В истории Git остаются исходники
и документация; бинарные файлы и веса находятся в материалах выпуска.
После установки моделей обработка работает без интернета.

| Платформа | Самостоятельная сборка | Проверка |
| --- | --- | --- |
| Windows 10/11 x64 | [Инструкция](docs/BUILDING.ru.md#windows) | Локальная проверка упакованного приложения и CI прошли |
| macOS 15+ Apple Silicon | [Инструкция](docs/BUILDING.ru.md#macos-15-apple-silicon) | Нативные тесты и проверки интерфейса в CI прошли |
| Ubuntu 24.04 x64 | [Инструкция](docs/BUILDING.ru.md#ubuntu-2404-x64) | Нативные тесты и проверки интерфейса в CI прошли |

Актуальные результаты удалённых проверок доступны в
[GitHub Actions](https://github.com/suroviimustang-ai/VoxLoom-Studio/actions).
Проверка CI не заменяет проверку установщика на чистой системе.
В [первом успешном прогоне 11 ноября 2026 года](https://github.com/suroviimustang-ai/VoxLoom-Studio/actions/runs/42965738853)
на каждой ОС выполнены 47 тестов и проверки шести конфигураций экрана.

## Возможности

- WAV, FLAC, MP3, OGG, AAC/M4A и другие форматы через libsndfile/PyAV.
- Неизменяемый исходник A, отдельный результат B, выделение и прослушивание.
- Spectral Gate, RNNoise, DeepFilterNet3, фильтрация гула, LUFS/пиковая нормировка.
- Silero VAD и FlexSED + CLAP: цветные метки речи и звуковых событий.
- Whisper base, small и large-v3-turbo: русский и другие языки, экспорт TXT/SRT.
- Экспорт WAV/FLAC/OGG и меток JSON; отмена фоновой обработки.
- Заставка при запуске и окно в рабочую область текущего монитора с учётом DPI.
- Компактная компоновка без прокрутки всего окна: нормировка на вкладке «Уровень»,
  метки и текст на узком экране переключаются вкладками. Проверяются рабочие области
  от 800×600 логических пикселей; текст и длинные списки прокручиваются внутри панели.

Компактная сборка включает Python, Qt, кодеки, RNNoise и Silero VAD.
Spectral Gate и DSP также работают сразу. Whisper, DeepFilterNet3 и FlexSED
устанавливаются отдельными проверяемыми пакетами. После установки выбранных моделей
интернет, API-ключи, отдельный Python и CUDA не нужны. Аудио остаётся на компьютере.
Полную сборку со всеми весами по-прежнему можно собрать из исходников.

## Работа

1. Откройте запись кнопкой или перетащите файл.
2. Выберите A/B: это вход прослушивания и последующей обработки.
3. «Очистка»: выберите метод и силу. Профиль шума берётся из паузы без речи.
4. «Речь» → «Найти речь» или «События» → запрос на английском, например
   `Speech; Conversation; Whispering` (работает и с русской записью).
5. Выберите метку или выделите участок мышью, прослушайте и распознайте его.
6. Экспортируйте аудио, текст или метки. Правки текста сохраняются в TXT;
   SRT сохраняет исходные сегменты модели с таймкодами записи.

Для нормировки откройте вкладку «Уровень». При небольшой высоте окна отступы
автоматически уменьшаются, пояснения доступны во всплывающих подсказках.
Полные имена длинных файлов и сообщения можно прочитать, наведя на них указатель.

Space — пуск/пауза, Esc — стоп, Ctrl+O — открыть, Ctrl+S — экспорт аудио,
Ctrl+Z — отменить обработку, Ctrl+колесо — масштаб времени.

## Запуск из исходников

Скачайте исходники через **Code → Download ZIP** либо клонируйте репозиторий:

```bash
git clone https://github.com/suroviimustang-ai/VoxLoom-Studio.git
cd VoxLoom-Studio
```

В PowerShell, в каталоге проекта, с Python 3.11 x64:

```powershell
py -3.11 -m venv .venv311
.venv311/Scripts/python tools/install_dependencies.py
.venv311/Scripts/python tools/doctor.py
.venv311/Scripts/python tools/prepare_models.py
.venv311/Scripts/python tools/prepare_flexsed.py
./run.ps1
```

Подготовка требует сети и нескольких гигабайт места. Ревизии Whisper и SHA-256
зафиксированы в `model-sources.json`; FlexSED/CLAP — в скрипте подготовки.
Модель base — быстрый черновик; small — баланс; turbo — более мощный вариант.
Наличие модели не гарантирует правильность текста на тихой или повреждённой речи.

## Проверки и сборка

```powershell
.venv311/Scripts/python -m pytest -q
.venv311/Scripts/python tools/check_startup.py
.venv311/Scripts/python tools/build_portable.py
./build.ps1
.venv311/Scripts/python tools/finalize_flexsed_release.py
```

`build_portable.py` создаёт нативную папку приложения / macOS `.app`. Для личного
Windows-установщика через `build.ps1` нужен Inno Setup 6; для речевого теста — английский
голос Windows SAPI. Сборка проверяет обязательные веса, DLL, настоящий EXE,
кодеки, VAD, шумоподавители, FlexSED и все три Whisper без сетевой загрузки.
Результат: `release/VoxLoom-Studio-Setup-0.3.0-Offline-win-x64.exe`.
Переносная версия: `dist-flexsed/VoxLoom/VoxLoom.exe`, нужна вся папка целиком.

Для компактного EXE/AppImage/DMG выполните `python tools/build_portable.py --compact`,
затем `python tools/package_release.py` на целевой ОС.
Подробнее — в [инструкции сборки](docs/BUILDING.ru.md#компактные-пакеты-выпуска).

## Ограничения

- Whisper может пропускать, повторять и придумывать слова: проверяйте прослушиванием.
  Отсутствие отметки «неразборчиво» не означает доказанную точность.
- FlexSED ищет события, но не очищает звук, не распознаёт слова и не устанавливает
  личность говорящего. Его оценки не являются проверенными вероятностями.
- До 8 каналов и PCM до 1.5 ГБ; обработка в памяти. На 8 ГБ RAM используйте короткие
  фрагменты для тяжёлых моделей. LUFS поддерживает до 5 каналов.
- История проекта не сохраняется между запусками. Перед закрытием экспортируйте
  результаты. Лимитер контролирует sample peak; true-peak не заявлен.
- Проверки исходников и упаковки выполняются отдельными процессами CI. Перед
  публикацией проверяются нативная сборка, установка всех пакетов моделей и запуск
  установленного или смонтированного дистрибутива. Отчёты привязаны к коммиту выпуска.
- EXE не подписан цифровым сертификатом. Проверки на текущем ПК не заменяют теста
  установки в чистой виртуальной машине.

## Лицензия и участие

Copyright (C) 2026 MatSoftAI and VoxLoom contributors. Код приложения и его
собственные ресурсы доступны по [GPLv3](LICENSE), без гарантий. Разрешены
использование, изменение и распространение с соблюдением лицензии, в том числе
коммерческое. Сторонний код и веса сохраняют свои лицензии.

[Компоненты и лицензии](THIRD_PARTY_NOTICES.ru.md) · [Архитектура](docs/ARCHITECTURE.md) ·
[Участие](CONTRIBUTING.md) · [Безопасность](SECURITY.md) · [Выпуск](docs/RELEASING.md) ·
[Изменения](CHANGELOG.md) · [Публикация исходников](docs/PUBLISHING.ru.md).

Для разработчиков: [стандарт Python, PowerShell и конфигурации](docs/CODING_STANDARDS.ru.md).

Организация страницы проекта вдохновлена [Nota](https://github.com/nota-daw/nota).
VoxLoom — самостоятельное приложение MatSoftAI; код и графические ресурсы Nota
не используются. Зависимости VoxLoom перечислены в `THIRD_PARTY_NOTICES.ru.md`.
