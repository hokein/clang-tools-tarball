#!/usr/bin/env python

import fnmatch
import itertools
import os
import shutil
import subprocess
import sys
import tarfile

from config import *
from github import GitHub

GITHUB_REPO = 'hokein/clang-tools-prebuilt'

def PrintTarProgress(tarinfo):
  print 'Adding', tarinfo.name
  return tarinfo


def create_or_get_release_draft(github, releases):
  # Search for existing draft.
  for release in releases:
    if release['draft']:
      return release
  return create_release_draft(github)


def create_release_draft(github):
  name = '{0} r{1}'.format('ClangTools', CLANG_REVISION)
  body = 'Update to revision {0}.'.format(CLANG_REVISION)
  data = dict(tag_name='r' + CLANG_REVISION, name=name, body=body, draft=True)
  r = github.repos(GITHUB_REPO).releases.post(data=data)
  return r


def auth_token():
  token = os.environ.get('CLANG_TOOLS_PREBUILT_GITHUB_TOKEN')
  message = ('Error: Please set the $CLANG_TOOLS_PREBUILT_GITHUB_TOKEN '
             'environment variable, which is your personal token.')
  assert token, message
  return token


def upload_to_github(file_path):
  github = GitHub(auth_token())
  releases = github.repos(GITHUB_REPO).releases.get()
  release = create_or_get_release_draft(github, releases)
  # Upload clang-tools-rXXXXX.tgz.
  params = {'name':  os.path.basename(file_path) }
  headers = {'Content-Type': 'application/zip'}
  with open(file_path, 'rb') as f:
    github.repos(GITHUB_REPO).releases(release['id']).assets.post(
        params=params, headers=headers, data=f, verify=False)


def main():
  if sys.platform == 'darwin':
    platform = 'mac'
  elif sys.platform == 'win32':
    platform = 'win'
  else:
    platform = 'linux'
  pdir = 'clang-tools-r{0}-{1}'.format(CLANG_REVISION, platform)

  stamp = open(STAMP_FILE).read().rstrip()
  if stamp != CLANG_REVISION:
    print 'Actual stamp (%s) != expected stamp (%s).' % (stamp, CLANG_REVISION)
    return 1

  shutil.rmtree(pdir, ignore_errors=True)

  want = ['cr_build_revision',
          'lib/clang/*/include/*',
          'bin/clang-tidy',
          'bin/clang-include-fixer',
          'bin/find-all-symbols']

  for root, dirs, files in os.walk(LLVM_BUILD_DIR):
    # root: third_party/llvm-build/Release+Asserts/lib/..., rel_root: lib/...
    rel_root = root[len(LLVM_BUILD_DIR)+1:]
    rel_files = [os.path.join(rel_root, f) for f in files]
    wanted_files = list(set(itertools.chain.from_iterable(
        fnmatch.filter(rel_files, p) for p in want)))
    if wanted_files:
      # Guaranteed to not yet exist at this point:
      os.makedirs(os.path.join(pdir, rel_root))
    for f in wanted_files:
      src = os.path.join(LLVM_BUILD_DIR, f)
      dest = os.path.join(pdir, f)
      shutil.copy(src, dest)

  if sys.platform == 'darwin':
    shutil.copytree(os.path.join(LLVM_BUILD_DIR, 'include', 'c++'),
                    os.path.join(pdir, 'include', 'c++'))

  tar_entries = ['bin', 'lib', 'cr_build_revision']
  if sys.platform == 'darwin':
    tar_entries += ['include']
  with tarfile.open(pdir + '.tgz', 'w:gz') as tar:
    for entry in tar_entries:
      tar.add(os.path.join(pdir, entry), arcname=entry, filter=PrintTarProgress)


if __name__ == '__main__':
  sys.exit(main())
