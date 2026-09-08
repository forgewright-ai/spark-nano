# Changelog

## 1.0.0

- spark in nano, the first prompt-shaped plugin: nano has no scripting,
  so two `bind` lines put `|spark edit ` on nano's own execute prompt
  (M-S; M-F is fix-spelling in one keystroke). The buffer or the marked
  region is piped and replaced; M-U undoes; there is no completion --
  a prompt cannot hook the cursor.
- The install is a clone and one append to `~/.nanorc` (nano's `include`
  reads only syntax files); the snippet's comment block is the help.
- The pty test (`tests/nano_pty.py`) drives a real GNU nano against a
  stub spark; CI runs it on Ubuntu, Arch and macOS.
