# nano with spark -- the cheatsheet

nano edits; spark writes with you. Section 1 is nano on its own,
section 2 is the key that puts your own AI inside it.

The key spellings here are nano's own: `^X` means hold Ctrl and
press x; `M-S` is Meta-S -- hold Alt (Option on a Mac; spark's
Terminal profile makes it the Meta key) and press s, or press Esc
and then s. Case matters after Meta: `M-S` is Shift-s.

## 1. nano, the basics

Files

    ^O             save (nano says WriteOut)
    ^X             exit (asks when unsaved)

Editing

    M-U            undo         M-E      redo
    M-A            start marking (select); move, then act
    ^K             cut the line, or the marked text
    M-6            copy the marked text
    ^U             paste

Finding

    ^W             search -- then M-W for the next match
    ^\             search and replace
    ^_             go to a line number

Help

    ^G             nano's own help; the key list lives at the bottom
                   of the screen

## 2. the text, with spark

The key opens nano's own execute prompt pre-filled with
`|spark edit ` -- type your words, press Enter, and the buffer (or
the marked region, M-A) is piped through spark and REPLACED by the
answer. Nothing runs until that Enter, and M-U always brings your
text back. nano has no panes, so there is no completion here.

    M-S words      rewrite the whole file, or the marked region
    M-S ? words    ask about it: the answer replaces the text --
                   read it, then M-U restores your text
    M-F            fix spelling and punctuation, one keystroke

By example

    M-S shorter                   the text, tighter
    M-S fix grammar               grammar only, nothing else moves
    M-S translate to Portuguese   the same text, in Portuguese
    M-S ? is the title too long   read the answer, then M-U
    M-F                           the one-keystroke cleanup

The comment block in `spark.nanorc` is the help; M-S and M-F are
suggestions -- edit the two bind lines to taste.
