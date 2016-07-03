#!/usr/bin/env python

import fnmatch
import itertools
import os
import shutil
import subprocess
import sys
import tarfile

from config import *


def PrintTarProgress(tarinfo):
  print 'Adding', tarinfo.name
  return tarinfo


def main():
  if sys.platform == 'darwin':
    platform = 'mac'
  elif sys.platform == 'win32':
    platform = 'win'
  else:
    platform = 'linux'
  pdir = 'clang-r{0}-{1}'.format(CLANG_REVISION, platform)

  stamp = open(STAMP_FILE).read().rstrip()
  if stamp != CLANG_REVISION:
    print 'Actual stamp (%s) != expected stamp (%s).' % (stamp, CLANG_REVISION)
    return 1

  shutil.rmtree(pdir, ignore_errors=True)

  want = ['cr_build_revision',
          'lib/clang/*/include/*',
          'bin/clang-tidy']

  for root, dirs, files in os.walk(LLVM_RELEASE_DIR):
    # root: third_party/llvm-build/Release+Asserts/lib/..., rel_root: lib/...
    rel_root = root[len(LLVM_RELEASE_DIR)+1:]
    rel_files = [os.path.join(rel_root, f) for f in files]
    wanted_files = list(set(itertools.chain.from_iterable(
        fnmatch.filter(rel_files, p) for p in want)))
    if wanted_files:
      # Guaranteed to not yet exist at this point:
      os.makedirs(os.path.join(pdir, rel_root))
    for f in wanted_files:
      src = os.path.join(LLVM_RELEASE_DIR, f)
      dest = os.path.join(pdir, f)
      shutil.copy(src, dest)

  if sys.platform == 'darwin':
    shutil.copytree(os.path.join(LLVM_RELEASE_DIR, 'include', 'c++'),
                    os.path.join(pdir, 'include', 'c++'))

  tar_entries = ['bin', 'lib']
  if sys.platform == 'darwin':
    tar_entries += ['include']
  with tarfile.open(pdir + '.tgz', 'w:gz') as tar:
    for entry in tar_entries:
      tar.add(os.path.join(pdir, entry), arcname=entry, filter=PrintTarProgress)


if __name__ == '__main__':
  sys.exit(main())
