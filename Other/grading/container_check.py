"""Run the trusted test entrypoint; early exit is not test completion.

This protocol detects premature process termination. It is not a security
boundary between Python tests and code imported in the same interpreter.
"""
import os
import runpy
import shutil
import sys

COMPLETED = b'course-tests-completed\n'


def check(script):
    # Suppress Python and native writes to ordinary stdout/stderr. Only the
    # wrapper reports completion, after the test entrypoint actually returned.
    status_fd = os.dup(1)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null_fd, 1)
    os.dup2(null_fd, 2)
    os.close(null_fd)
    write, close = os.write, os.close
    try:
        runpy.run_path(script, run_name='__main__')
    except BaseException:
        close(status_fd)
        return 1
    write(status_fd, COMPLETED)
    close(status_fd)
    return 0


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--local':
        script = os.path.abspath(sys.argv[2])
        os.chdir(os.path.dirname(script))
        sys.path.insert(0, os.getcwd())
        return check(script)
    try:
        shutil.copytree('/input', '/tmp/hw')
        os.chdir('/tmp/hw/' + sys.argv[1])
    except OSError:
        os.write(1, b'course-infrastructure-error\n')
        return 2
    sys.path.insert(0, os.getcwd())
    return check('test.py')


if __name__ == '__main__':
    raise SystemExit(main())
