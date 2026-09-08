# spark-nano -- spark inside nano

spark (https://spark.forgewright.ai) is your own AI on your own machine;
this plugin puts it under one key in nano. nano has no scripting, so the
plugin is two `bind` lines: the key opens nano's own execute prompt
pre-filled with `|spark edit ` -- type your words, press Enter, and the
buffer (or the marked region) is piped through spark and replaced by the
answer.

    M-S words          rewrite the whole file, or the marked region
                       (M-A marks); M-U undoes
    M-S ? words        ask about it: the answer replaces the text --
                       read it, then M-U brings your text back
    M-F                fix spelling and punctuation, one keystroke

Nothing runs until you press Enter: a proposal you asked for, never a
surprise. A prompt cannot hook the cursor, so there is no completion
here -- micro's, neovim's and vim's plugins have it.

## Install

You need spark 1.7 or newer on this machine (`spark edit -h` answers), and
GNU nano 5.4 or newer (`nano --version`; macOS ships pico under nano's
name -- `brew install nano` gets the real one). Then:

```sh
git clone https://github.com/forgewright-ai/spark-nano ~/.config/nano/spark
cat ~/.config/nano/spark/spark.nanorc >> ~/.nanorc
```

The append is the install: nano's `include` reads only syntax files, so a
bind cannot ride it. An update is `git -C ~/.config/nano/spark pull`, then
delete the old spark lines from `~/.nanorc` and append again. The comment
block in `spark.nanorc` is the help; M-S and M-F are suggestions -- edit
the two lines to taste.

## What leaves this machine

The piped text -- at most 12 kB for a rewrite, 16 kB for a question --
and only to the brain spark is configured for. nano's pipe carries no
file name, so not even that travels. Every run is one call to `spark
edit` with the text on stdin; the plugin never speaks HTTP and never
sees a token.

## Contributing

`git config core.hooksPath .githooks` once; the hook keeps the tree free of
private names, ASCII, and the payload bind-only. `python3 tests/nano_pty.py`
drives a real nano in a pty against a stub spark (skips without GNU nano
5.4). Another editor joins spark the same way this one does: one client of
`spark edit`, in its own repo.

MIT. Credits in `CREDITS.md`. Built with Claude.
