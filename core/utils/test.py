from contextlib import contextmanager


@contextmanager
def suppress_stdout():
    from contextlib import redirect_stderr, redirect_stdout
    from os import devnull

    with open(devnull, 'w') as fnull:
        with redirect_stderr(fnull) as err, redirect_stdout(fnull) as out:
            yield (err, out)
