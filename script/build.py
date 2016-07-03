#!/usr/bin/env python

import os
import sys
import pipes
import subprocess
import shutil

from config import *

def EnsureDirExists(path):
  if not os.path.exists(path):
    print "Creating directory %s" % path
    os.makedirs(path)


def WriteStampFile(s, path=STAMP_FILE):
  """Write s to the stamp file."""
  EnsureDirExists(os.path.dirname(path))
  with open(path, 'w') as f:
    f.write(s)
    f.write('\n')


def ReadStampFile(path=STAMP_FILE):
  """Return the contents of the stamp file, or '' if it doesn't exist."""
  try:
    with open(path, 'r') as f:
      return f.read().rstrip()
  except IOError:
    return ''


def RmCmakeCache(dir):
  """Delete CMake cache related files from dir."""
  for dirpath, dirs, files in os.walk(dir):
    if 'CMakeCache.txt' in files:
      os.remove(os.path.join(dirpath, 'CMakeCache.txt'))
    if 'CMakeFiles' in dirs:
      RmTree(os.path.join(dirpath, 'CMakeFiles'))


def RunCommand(command, msvc_arch=None, env=None, fail_hard=True):
  """Run command and return success (True) or failure; or if fail_hard is
     True, exit on failure.  If msvc_arch is set, runs the command in a
     shell with the msvc tools for that architecture."""

  # https://docs.python.org/2/library/subprocess.html:
  # "On Unix with shell=True [...] if args is a sequence, the first item
  # specifies the command string, and any additional items will be treated as
  # additional arguments to the shell itself.  That is to say, Popen does the
  # equivalent of:
  #   Popen(['/bin/sh', '-c', args[0], args[1], ...])"
  #
  # We want to pass additional arguments to command[0], not to the shell,
  # so manually join everything into a single string.
  # Annoyingly, for "svn co url c:\path", pipes.quote() thinks that it should
  # quote c:\path but svn can't handle quoted paths on Windows.  Since on
  # Windows follow-on args are passed to args[0] instead of the shell, don't
  # do the single-string transformation there.
  if sys.platform != 'win32':
    command = ' '.join([pipes.quote(c) for c in command])
  print 'Running', command
  if subprocess.call(command, env=env, shell=True) == 0:
    return True
  print 'Failed.'
  if fail_hard:
    sys.exit(1)
  return False


def CopyFile(src, dst):
  """Copy a file from src to dst."""
  print "Copying %s to %s" % (src, dst)
  shutil.copy(src, dst)


def CopyDirectoryContents(src, dst, filename_filter=None):
  """Copy the files from directory src to dst
  with an optional filename filter."""
  dst = os.path.realpath(dst)  # realpath() in case dst ends in /..
  EnsureDirExists(dst)
  for root, _, files in os.walk(src):
    for f in files:
      if filename_filter and not re.match(filename_filter, f):
        continue
      CopyFile(os.path.join(root, f), dst)


def RmTree(dir):
  """Delete dir."""
  def ChmodAndRetry(func, path, _):
    # Subversion can leave read-only files around.
    if not os.access(path, os.W_OK):
      os.chmod(path, stat.S_IWUSR)
      return func(path)
    raise

  shutil.rmtree(dir, onerror=ChmodAndRetry)


def Checkout(name, url, dir):
  """Checkout the SVN module at url into dir. Use name for the log message."""
  print "Checking out %s r%s into '%s'" % (name, CLANG_REVISION, dir)

  command = ['svn', 'checkout', '--force', url + '@' + CLANG_REVISION, dir]
  if RunCommand(command, fail_hard=False):
    return

  if os.path.isdir(dir):
    print "Removing %s." % (dir)
    RmTree(dir)

  print "Retrying."
  RunCommand(command)


def main():
  Checkout('LLVM', LLVM_REPO_URL + '/llvm/trunk', LLVM_DIR)
  Checkout('Clang', LLVM_REPO_URL + '/cfe/trunk', CLANG_DIR)
  Checkout('Clang Tools Extra', LLVM_REPO_URL + '/clang-tools-extra/trunk',
           CLANG_TOOLS_EXTRA_DIR)
  if sys.platform == 'darwin':
    # clang needs a libc++ checkout, else -stdlib=libc++ won't find includes
    # (i.e. this is needed for bootstrap builds).
    Checkout('libcxx', LLVM_REPO_URL + '/libcxx/trunk', LIBCXX_DIR)

  EnsureDirExists(LLVM_BUILD_DIR)
  os.chdir(LLVM_BUILD_DIR)
  RmCmakeCache('.')

  cmake_args = ['-GNinja',
                '-DCMAKE_BUILD_TYPE=Release',
                '-DLLVM_ENABLE_ASSERTIONS=ON',
                '-DLLVM_ENABLE_THREADS=OFF']
  RunCommand(['cmake'] + cmake_args + [LLVM_DIR],
             msvc_arch='x64', env=None)
  RunCommand(['ninja', 'clang'], msvc_arch='x64')
  RunCommand(['ninja', 'clang-tidy'], msvc_arch='x64')
  WriteStampFile(CLANG_REVISION)


if __name__ == '__main__':
  sys.exit(main())
