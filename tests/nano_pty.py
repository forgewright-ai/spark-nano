#!/usr/bin/env python3
# nano_pty.py -- the spark binds inside a real GNU nano, in a pty, against
# a stub `spark` (on PATH: the snippet says `spark` plainly, and that is
# what must be proven) that logs what it was asked and answers a fixed
# word. Proves the whole loop the snippet promises: M-S opens the execute
# prompt pre-filled with `|spark edit `, the words reach spark with the
# buffer (or the marked region) on stdin and no path, the answer replaces
# the text, M-F is one keystroke, Ctrl-C runs nothing. The test performs
# the README's install line: the repo's spark.nanorc is appended to a
# throwaway ~/.nanorc. Skips (exit 0) without GNU nano 5.4 (macOS ships
# pico under nano's name).
#
#   python3 tests/nano_pty.py

import fcntl
import os
import re
import pty
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = REPO                                   # the repo root is the plugin
CSI = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\([A-Za-z0-9]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")

STUB = r'''#!/bin/sh
# the stub spark: log argv and stdin, answer one word
printf '%s\n' "$*" >> "$STUB_LOG"
cat > "$STUB_LOG.stdin"
case " $* " in
    *" ? "*)      printf 'STUB-ASK'; exit 0 ;;
    *" fail "*)   printf 'spark: no brain today -- spark serve\n' >&2; exit 1 ;;
esac
printf 'STUB-EDIT'
'''


class Editor:
    def __init__(self, argv, env, cwd, rows=30, cols=100):
        self.buf = b""
        self.pos = 0
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execvpe(argv[0], argv, env)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def read(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if r:
                try:
                    data = os.read(self.fd, 4096)
                except OSError:
                    return
                if not data:
                    return
                self.buf += data

    def plain(self):
        """what was drawn since mark(), with the escape sequences removed"""
        return CSI.sub("", self.buf[self.pos:].decode("utf-8", "replace"))

    def expect(self, text, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if text in self.plain():
                return True
            self.read(0.2)
        return False

    def send(self, s):
        os.write(self.fd, s.encode())
        time.sleep(0.2)

    def mark(self):
        self.pos = len(self.buf)

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, 0)
        except OSError:
            pass


def main():
    nano = shutil.which("nano")
    if not nano:
        print("nano_pty: nano is not installed here -- skipped (apt-get install nano / brew install nano)")
        return 0
    ver = subprocess.run([nano, "--version"], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT).stdout.decode().splitlines()[0]
    m = re.search(r"GNU nano, version (\d+)\.(\d+)", ver)
    if not m or (int(m.group(1)), int(m.group(2))) < (5, 4):
        print("nano_pty: not GNU nano 5.4 or newer here -- skipped (%s)" % ver.strip())
        return 0
    fail = 0

    def ok(cond, what, extra=""):
        nonlocal fail
        print("  %s %s%s" % ("ok  " if cond else "FAIL", what, ("   " + extra) if extra and not cond else ""))
        if not cond:
            fail += 1

    with tempfile.TemporaryDirectory(prefix="spark-nano-") as tmp:
        work, bindir = [os.path.join(tmp, d) for d in ("work", "bin")]
        os.makedirs(work)
        os.makedirs(bindir)
        # the README's install line, performed: the snippet appended to
        # a fresh ~/.nanorc (the payload file is the fixture)
        with open(os.path.join(REPO, "spark.nanorc")) as f:
            snippet = f.read()
        with open(os.path.join(tmp, ".nanorc"), "w") as f:
            f.write(snippet)
        stub = os.path.join(bindir, "spark")
        with open(stub, "w") as f:
            f.write(STUB)
        os.chmod(stub, 0o755)
        log = os.path.join(tmp, "stub.log")
        note = os.path.join(work, "note.txt")
        with open(note, "w") as f:
            f.write("hello world\n")
        env = {"HOME": tmp, "TERM": "xterm-256color",
               "PATH": bindir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
               "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "STUB_LOG": log}
        argv = [nano, "note.txt"]

        def logged():
            try:
                with open(log) as f:
                    return f.read()
            except OSError:
                return ""

        def fresh(text="hello world\n"):
            if os.path.exists(log):
                os.unlink(log)
            with open(note, "w") as f:
                f.write(text)
            m = Editor(argv, env, work)
            ok(m.expect(text.splitlines()[0]), "nano draws the file")
            m.mark()
            return m

        # A. M-S: the execute prompt opens pre-filled with `|spark edit `
        m = fresh()
        m.send("\x1bs")
        ok(m.expect("spark edit"), "M-S pre-fills the execute prompt with |spark edit", m.plain()[-300:])
        m.send("shorter\r")
        ok(m.expect("STUB-EDIT"), "the words run the pipe: the answer replaces the buffer", m.plain()[-300:])
        m.send("\x0f\r")            # Ctrl-O save, confirm the name
        time.sleep(0.5)
        m.send("\x18")              # Ctrl-X quit
        m.read(1.0)
        m.close()
        with open(note) as f:
            saved = f.read()
        ok(saved in ("STUB-EDIT", "STUB-EDIT\n"), "the saved file is the answer, nothing doubled", repr(saved))
        got = logged()
        ok(got.strip() == "edit shorter", "spark edit got exactly the words -- no name, no path", got)
        ok(work not in got, "the file's path never reaches spark", got)
        with open(log + ".stdin") as f:
            stdin = f.read()
        ok(stdin == "hello world\n", "the whole buffer travelled on stdin", repr(stdin))

        # B. the marked region (M-A, arrows) is piped and replaced alone
        m = fresh()
        m.send("\x1ba")             # M-A: set the mark at the start
        for _ in range(5):
            m.send("\x1b[C")        # Right: the mark covers `hello`
        m.send("\x1bs")
        m.expect("spark edit")
        m.send("shorter\r")
        ok(m.expect("STUB-EDIT"), "the marked region is replaced", m.plain()[-300:])
        m.send("\x0f\r")
        time.sleep(0.5)
        m.send("\x18")
        m.read(1.0)
        m.close()
        with open(note) as f:
            saved = f.read()
        ok(saved == "STUB-EDIT world\n", "only the marked region became the answer", repr(saved))
        with open(log + ".stdin") as f:
            ok(f.read() == "hello", "the marked region alone travelled on stdin")

        # C. an ask through the same pipe: the answer replaces the text
        # (M-U brings it back -- here we just quit unsaved)
        m = fresh()
        m.send("\x1bs")
        m.expect("spark edit")
        m.send("? is this clear\r")
        ok(m.expect("STUB-ASK"), "an ask answers through the pipe", m.plain()[-300:])
        ok("edit ? is this clear" in logged(), "the question reached spark edit as ? words", logged())
        m.send("\x18")              # quit, modified: nano asks
        time.sleep(0.4)
        m.send("n")
        m.read(1.0)
        m.close()
        with open(note) as f:
            ok(f.read() == "hello world\n", "the file on disk is untouched")

        # D. M-F: fix spelling and punctuation, one keystroke
        m = fresh()
        m.send("\x1bf")
        ok(m.expect("STUB-EDIT"), "M-F runs in one keystroke", m.plain()[-300:])
        ok("edit fix spelling and punctuation" in logged(), "the one-shot words reached spark", logged())
        m.send("\x18")
        time.sleep(0.4)
        m.send("n")
        m.read(1.0)
        m.close()

        # E. Ctrl-C at the pre-filled prompt cancels: nothing runs
        m = fresh()
        m.send("\x1bs")
        m.expect("spark edit")
        m.send("\x03")              # Ctrl-C: cancel
        time.sleep(0.4)
        ok(not os.path.exists(log), "a cancelled prompt runs nothing")
        m.send("\x18")
        m.read(1.0)
        m.close()

        # F. spark's failure leaves the buffer alone (nano shows the pipe
        # failed; the text stays)
        m = fresh()
        m.send("\x1bs")
        m.expect("spark edit")
        m.send("fail\r")
        time.sleep(0.8)
        m.send("\x18")
        time.sleep(0.4)
        m.send("n")
        m.read(1.0)
        m.close()
        with open(note) as f:
            ok(f.read() == "hello world\n", "a failed pipe leaves the file untouched")

    print("nano_pty: %s" % ("all ok" if not fail else "%d FAILED" % fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
