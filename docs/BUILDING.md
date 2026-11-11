# Самостоятельная сборка: Windows, macOS, Ubuntu

Репозиторий распространяется **в исходниках**, без EXE, записей и весов.
Модели скачиваются один раз при подготовке. Собранное приложение работает офлайн.
На каждой ОС нужно собирать нативно: PyInstaller не является кросс-компилятором.

| Платформа | Профиль | Статус |
| --- | --- | --- |
| Windows 10/11 x64 | Python 3.11 x64, CPU | Локально проверяются тесты и полный EXE |
| macOS 15+ Apple Silicon | Python 3.11 ARM64, CPU | Путь сборки и CI подготовлены; нативный прогон требуется |
| Ubuntu 24.04 x64 | Python 3.11, CPU | Путь сборки и CI подготовлены; нативный прогон требуется |

Intel Mac не входит в этот профиль: PyTorch прекратил выпуск macOS x86_64 wheels
после ветки 2.2. Наш набор использует 2.8. Не устанавливайте ARM64 Python через
Rosetta и не подменяйте PyTorch произвольной старой версией: это требует отдельной
проверки всей цепочки. На Apple Silicon `python -c "import platform; print(platform.machine())"`
должен показать `arm64`. На Windows/Linux ARM также нужна отдельная проверка.

Рекомендуется 16 ГБ RAM и 20–30 ГБ свободного места для окружения, моделей и сборки.
На 8 ГБ запуск возможен, но тяжёлые операции выполняйте на коротких фрагментах.
Все команды выполняются из корня скачанного/клонированного проекта.

## Windows

Установите Python 3.11 x64 с python.org и Git. В PowerShell:

```powershell
py -3.11 -m venv .venv311
.venv311/Scripts/python tools/install_dependencies.py
.venv311/Scripts/python tools/doctor.py
.venv311/Scripts/python tools/prepare_models.py
.venv311/Scripts/python tools/prepare_flexsed.py
.venv311/Scripts/python tools/doctor.py --models
.venv311/Scripts/python main.py
```

Сборка переносной папки без Inno Setup:

```powershell
.venv311/Scripts/python tools/build_portable.py
```

Результат: `dist-native/VoxLoom/VoxLoom.exe`; сохраняйте **всю папку**.
Чтобы собрать личный установщик, установите Inno Setup 6 и английский голос Windows
SAPI для тестового аудио, затем `./build.ps1`. Установщик и веса не коммитятся в Git.

## macOS 15+ (Apple Silicon)

В этом профиле требуется macOS 15 или новее: готовый пакет RNNoise 0.4.3 для Mac
собран с минимальной версией macOS 15. Поддержка более старых систем требует
отдельной сборки и проверки этой зависимости.

Установите Python 3.11 ARM64/universal2 с python.org либо через uv. При необходимости
установите инструменты разработчика командой `xcode-select --install`.

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
python tools/install_dependencies.py
python tools/doctor.py
python tools/prepare_models.py
python tools/prepare_flexsed.py
python tools/doctor.py --models
python main.py
python tools/build_portable.py
```

Результат: `dist-native/VoxLoom.app`. CUDA не используется; Whisper выбирает
поддерживаемый CPU-тип вычислений. Apple Developer ID и notarization в этот
локальный процесс сборки не входят. Не обещается переносимость приложения на
более старую macOS, чем поддерживают использованные Python/Qt/wheels.

## Ubuntu 24.04 (x64)

Установите системные библиотеки и pipx:

```bash
sudo apt update
sudo apt install -y git pipx build-essential pkg-config libportaudio2 libsndfile1 libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxcb-render-util0 libxcb-xinerama0 libxcb-randr0 libxcb-shape0 fonts-dejavu-core
pipx install uv
pipx ensurepath
```

Откройте новый терминал, затем:

```bash
uv python install 3.11
uv venv --python 3.11 --seed .venv311
source .venv311/bin/activate
python tools/install_dependencies.py
python tools/doctor.py
python tools/prepare_models.py
python tools/prepare_flexsed.py
python tools/doctor.py --models
python main.py
python tools/build_portable.py
```

Результат: `dist-native/VoxLoom/VoxLoom` и соседние библиотеки. Запуск:
`./dist-native/VoxLoom/VoxLoom`. Сборка использует glibc текущей ОС; для поддержки
более старой Ubuntu нужно собирать и проверять на ней, а не копировать новый bundle.

## Проверки и диагностика

```text
python -m pytest -q
python tools/check_startup.py
python tools/doctor.py --models
```

`doctor` проверяет импорты Qt, кодеков, RNNoise, Torch/DeepFilterNet и CLAP в
отдельных процессах, затем комплектность весов. Это не оценка качества модели.
`check_startup` проверяет границы окна на моделируемых экранах. Сетевые флаги
`HF_HUB_OFFLINE=1` и `TRANSFORMERS_OFFLINE=1` подходят для проверок после скачивания.
Снимите их перед первоначальной подготовкой весов.

- **Windows QtWidgets/DLL:** используйте чистое окружение одной разрядности;
  не копируйте случайные Qt/ICU DLL в папку программы. Сборщик сохраняет проверку импортов.
- **Ubuntu xcb:** установите библиотеки из команды выше; для сеанса XWayland можно
  проверить `QT_QPA_PLATFORM=xcb python main.py`. `offscreen` нужен только для тестов.
- **Нет устройства вывода:** проверьте устройство по умолчанию и доступность звука
  в ОС. Не запускайте Linux GUI через `sudo`.
- **Нет wheel для DeepFilterLib/RNNoise:** сначала проверьте Python 3.11 и архитектуру.
  Компиляция Rust/C зависимостей вручную — отдельный сценарий; не смешивайте чужие DLL/dylib.
- **Не хватает памяти:** используйте Whisper base/small и более короткое выделение.
- **Отсутствуют веса:** повторите оба скрипта подготовки; `model-sources.json`
  фиксирует ревизии Whisper и контрольные суммы. Не скачивайте случайные `.pth`.

Windows lock `requirements-lock.txt` нельзя использовать как универсальный lock
на macOS/Linux: в нём Windows-пакеты и CPU-wheel суффиксы. Для других ОС используется
`install_dependencies.py`; после успешной проверки сохраните свой `pip freeze`.

GitHub Actions содержит матрицу Windows, macOS ARM64 и Ubuntu. Добавленная
конфигурация не означает, что удалённые прогоны уже выполнены.

Источники: [PyInstaller: нативная сборка](https://pyinstaller.org/en/stable/operating-mode.html),
[управление Python через uv](https://docs.astral.sh/uv/guides/install-python/),
[Qt Linux dependencies](https://doc.qt.io/qt-6/linux-requirements.html),
[прекращение Intel Mac wheels PyTorch](https://dev-discuss.pytorch.org/t/pytorch-macos-x86-builds-deprecation-starting-january-2024/1690).
