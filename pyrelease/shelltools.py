import os
import sys
import contextlib
import subprocess


@contextlib.contextmanager
def ignore_stdout():
    """ A context manager that suppresses stdout."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stdout = os.dup(2)
    sys.stdout.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stdout, 2)
        os.close(old_stdout)


@contextlib.contextmanager
def ignore_stderr():
    """ A context manager that suppresses stderr."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)


def execute_shell_command(cmd, suppress=True):
    """ Call subprocess on cmd and silence any exceptions to
     be sent to log for postmortem error handling
     """
    null_file = open(os.devnull, 'w')
    try:
        if suppress:
            with ignore_stdout():
                rv = subprocess.call(cmd, shell=True, stdout=null_file, stderr=subprocess.STDOUT)
        else:
            rv = subprocess.call(cmd, shell=True, stdout=null_file, stderr=subprocess.STDOUT)
    except Exception as e:
        print("Error processing", str(cmd))
        print(e)
        return False
    else:
        return rv


# find('*.py', 'some/path/')
# def find(pattern, path):
#     result = []
#     for root, _, files in os.walk(path):
#         for name in files:
#             if fnmatch(name, pattern):
#                 result.append(os.path.join(root, name))
#     return result
