#!/usr/bin/env python

import os

CLANG_REVISION = '298696'
LLVM_REPO_URL='https://llvm.org/svn/llvm-project'
SRC_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
LLVM_DIR = os.path.join(SRC_DIR, 'deps', 'llvm-src')
CLANG_DIR = os.path.join(LLVM_DIR, 'tools', 'clang')
LIBCXX_DIR = os.path.join(LLVM_DIR, 'projects', 'libcxx')
CLANG_TOOLS_EXTRA_DIR = os.path.join(CLANG_DIR, 'tools', 'extra')
LLVM_BUILD_DIR = os.path.join(SRC_DIR, 'deps', 'llvm-build', 'Release+Asserts')
STAMP_FILE = os.path.join(LLVM_BUILD_DIR, 'cr_build_revision')
