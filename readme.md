# Clang tools tarball

The tarball generates binaries for [clang extra tools](http://clang.llvm.org/extra/),
and upload them to [release](https://github.com/hokein/clang-tools-tarball/releases) page.

Currently, it has the following tools, only macOS and Linux binaries are provided.

  * clang-apply-replacements
  * clang-rename
  * clang-tidy
  * clang-include-fixer
  * find-all-symbols

If you want to add other clang tools, feel free to file an issue.

## Usage

Check out a specific revision of clang source and build it.

```
$ ./script/build.py
```

Package all prebuilt binaries and upload them to GitHub Release.

```
$ ./script/package.py
```
