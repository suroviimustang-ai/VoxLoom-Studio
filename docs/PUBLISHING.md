# Publish sources on GitHub


Project repository: `suroviimustang-ai/VoxLoom-Studio`.
Only publish the reviewed source export to Git. The development workspace contains
processing results, environments, models and builds; do not upload it wholesale
or include the history of a parent repository.

## Prepare the export

1. Run the checks described in the [coding standards](CODING_STANDARDS.md) and
   [release procedure](RELEASING.md).
2. Create a fresh export from the project root. The destination directory and ZIP
   must not exist; the script deliberately preserves previous exports:

   ```text
   python tools/export_public.py --destination public-export/VoxLoom-Studio-source
   ```

3. Review `SOURCE_MANIFEST.json`, the directory contents and images. Publish only
   code, documentation, licenses and original assets. The README screenshot uses
   a synthetic signal and sample text.
4. Keep recordings, transcripts, models, tokens, diagnostic logs, environments,
   EXE/DLL files and installers out of Git. `.gitignore` is an additional safeguard;
   the primary publication boundary is the allowlist in `tools/export_public.py`.

## Create the repository

Create a public `VoxLoom-Studio` repository in your GitHub account. The export already
includes its license, README and `.gitignore`; for a Git upload, create an empty
repository without template files.

Sign in to GitHub normally through the browser or Git credential manager. Do not
put tokens in URLs, source files, commands, scripts or chat messages. A GitHub
connector and a browser login are separate sessions. If the connector only has
access to selected repositories, the owner must add the new repository to that list.

Open a terminal **inside the reviewed exported directory**, then run:

```bash
git init -b main
git add .
git diff --cached --stat
git status --short
git commit -m "Publish VoxLoom Studio sources"
git remote add origin https://github.com/suroviimustang-ai/VoxLoom-Studio.git
git push -u origin main
```

For a fork, replace the owner in the URL with your own account. Git will ask you
to configure an author name and email if they are missing; you can use the noreply
address shown in your GitHub account settings. Do not initialize Git in a parent
directory containing all your projects. Do not use `--force` to bypass a conflict
with an existing repository.

You can also upload the same files through a GitHub connector by creating blobs,
a tree and a commit, then updating `main`. The reviewed export remains the
publication boundary. The connector needs file and workflow write access to the
new repository.

## Verify publication

- Open the README and check the logo, screenshot and relative links.
- Verify the license, third-party notices and build instructions.
- Wait for GitHub Actions: code quality, Windows, macOS and Ubuntu. Do not mark a
  platform as validated before its native run succeeds.
- Compare files against `SOURCE_MANIFEST.json`. Manifest hashes describe the
  original exported bytes; a local Git checkout may change line endings.
- Update the version and changelog before a subsequent release, then create a tag.
  Keep binaries and model weights in release assets, separate from source history.

Review the diff before updates. Refresh the manifest from a new export and publish
ordinary commits, preserving repository history.
