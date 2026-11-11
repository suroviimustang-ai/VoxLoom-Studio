# Security and privacy

The installed application processes audio locally. It has no upload endpoint,
telemetry or model downloader. Build-time scripts download public upstream weights.

The maintained release line is 0.2.x. Use the repository's private vulnerability
reporting feature when available. Do not put sensitive reproductions or exploit
details in public issues.

Local diagnostics: `%LOCALAPPDATA%/VoxLoom/logs/voxloom.log` on Windows,
`~/Library/Logs/VoxLoom/voxloom.log` on macOS, or
`${XDG_STATE_HOME:-~/.local/state}/voxloom/logs/voxloom.log` on Linux, limited to 1 MiB
with two rotated backups. Exception details may contain local paths. Review
logs before sharing. Audio and transcripts are not deliberately logged, and
the application never submits a report itself.

Codecs and neural runtimes contain native code. Keep dependencies updated and
test packaged workers. Worker crashes are handled where possible; recovery from
every conceivable failure is not guaranteed. Projects are not autosaved.
