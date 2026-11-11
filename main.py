from __future__ import annotations

import os
import sys

for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(variable, "2")


def main():
    if "--worker" in sys.argv:
        # Windowed executables have no console; native model loggers need streams.
        if sys.stdout is None:
            sys.stdout = open(
                os.devnull, "w", encoding="utf-8", errors="backslashreplace"
            )
        if sys.stderr is None:
            sys.stderr = open(
                os.devnull, "w", encoding="utf-8", errors="backslashreplace"
            )
        # QProcess can provide real pipes even to a windowed frozen worker.
        # Their locale encoding must not make third-party Unicode logging fatal.
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        from voxloom.worker import execute

        return execute(sys.argv[sys.argv.index("--worker") + 1])
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication

    from voxloom.startup import (
        StartupSplash,
        assets_root,
        launch_screen,
        show_workspace,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("VoxLoom Studio")
    app.setOrganizationName("MatSoftAI")
    app.setStyle("Fusion")
    from voxloom.diagnostics import configure_logging, install_exception_handler

    log_path = configure_logging()
    install_exception_handler(app, log_path)
    app.setWindowIcon(QIcon(str(assets_root() / "voxloom.ico")))
    screen = launch_screen(app)
    splash = StartupSplash(screen)
    splash.show()
    app.processEvents()
    if "--smoke-test" in sys.argv:
        from pathlib import Path

        index = sys.argv.index("--smoke-test")
        destination = Path(sys.argv[index + 2])
        destination.mkdir(parents=True, exist_ok=True)
        splash.grab().save(str(destination / "startup-splash.png"))
    from voxloom.window import MainWindow

    window = MainWindow()
    splash.set_status("Открытие рабочего пространства…")
    show_workspace(window, screen)
    splash.finish(window)
    if "--smoke-test" in sys.argv:
        from voxloom.smoke import run

        index = sys.argv.index("--smoke-test")
        return run(app, window, sys.argv[index + 1], sys.argv[index + 2])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
