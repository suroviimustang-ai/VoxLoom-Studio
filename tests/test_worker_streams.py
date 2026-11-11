import io
import sys


def test_worker_can_log_unicode_through_windows_pipes(monkeypatch):
    import main as entry
    from voxloom import worker

    stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1251")
    stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp1251")

    def execute(_):
        print("✅ model ready", flush=True)
        print("✅ diagnostic", file=sys.stderr, flush=True)
        return 0

    with monkeypatch.context() as context:
        context.setattr(sys, "stdout", stdout)
        context.setattr(sys, "stderr", stderr)
        context.setattr(sys, "argv", ["main.py", "--worker", "unused.json"])
        context.setattr(worker, "execute", execute)
        assert entry.main() == 0
    assert stdout.buffer.getvalue().decode("utf-8").strip() == "✅ model ready"
    assert stderr.buffer.getvalue().decode("utf-8").strip() == "✅ diagnostic"
    stdout.close()
    stderr.close()
