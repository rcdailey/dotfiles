[![](logo.svg)](/)

* [Documentation](index.html)
* [Supported hooks](hooks.html)
* [Demo](https://github.com/pre-commit/demo-repo#readme)

* [Download on GitHub](https://github.com/pre-commit/pre-commit)

# pre-commit

A framework for managing and maintaining multi-language pre-commit hooks.

[![build status](https://github.com/pre-commit/pre-commit/actions/workflows/main.yml/badge.svg)](https://github.com/pre-commit/pre-commit/actions/workflows/main.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pre-commit/pre-commit/main.svg)](https://results.pre-commit.ci/latest/github/pre-commit/pre-commit/main)

[Star](https://github.com/pre-commit/pre-commit)

![pre-commit logo](logo-top-shelf.png)

[Introduction](#intro)
[Installation](#install)
[Adding plugins](#plugins)
[Usage](#usage)
[Creating new hooks](#new-hooks)
[Command line interface](#cli)
[Advanced features](#advanced)
[Contributing](#contributing)

# Introduction [¶](#introduction)

Git hook scripts are useful for identifying simple issues before submission to
code review. We run our hooks on every commit to automatically point out
issues in code such as missing semicolons, trailing whitespace, and debug
statements. By pointing these issues out before code review, this allows a
code reviewer to focus on the architecture of a change while not wasting time
with trivial style nitpicks.

As we created more libraries and projects we recognized that sharing our
pre-commit hooks across projects is painful. We copied and pasted unwieldy
bash scripts from project to project and had to manually change the hooks to
work for different project structures.

We believe that you should always use the best industry standard linters.
Some of the best linters are written in languages that you do not use in your
project or have installed on your machine. For example scss-lint is a linter
for SCSS written in Ruby. If you’re writing a project in node you should be
able to use scss-lint as a pre-commit hook without adding a Gemfile to your
project or understanding how to get scss-lint installed.

We built pre-commit to solve our hook issues. It is a multi-language package
manager for pre-commit hooks. You specify a list of hooks you want and
pre-commit manages the installation and execution of any hook written in any
language before every commit. pre-commit is specifically designed to not
require root access. If one of your developers doesn’t have node installed
but modifies a JavaScript file, pre-commit automatically handles downloading
and building node to run eslint without root.

# Installation [¶](#installation)

Before you can run hooks, you need to have the pre-commit package manager
installed.

Using pip:

```
pip install pre-commit

```

In a python project, add the following to your requirements.txt (or
requirements-dev.txt):

```
pre-commit

```

As a 0-dependency [zipapp](https://docs.python.org/3/library/zipapp.html):

* locate and download the `.pyz` file from the [github releases](https://github.com/pre-commit/pre-commit/releases)
* run `python pre-commit-#.#.#.pyz ...` in place of `pre-commit ...`

## Quick start [¶](#quick-start)

### 1. Install pre-commit [¶](#1-install-pre-commit)

* follow the [install](#install) instructions above
* `pre-commit --version` should show you what version you're using

```
$ pre-commit --version
pre-commit 4.2.0

```

### 2. Add a pre-commit configuration [¶](#2-add-a-pre-commit-configuration)

* create a file named `.pre-commit-config.yaml`
* you can generate a very basic configuration using
  [`pre-commit sample-config`](#pre-commit-sample-config)
* the full set of options for the configuration are listed [below](#plugins)
* this example uses a formatter for python code, however `pre-commit` works for
  any programming language
* other [supported hooks](hooks.html) are available

```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.3.0
    hooks:
    -   id: check-yaml
    -   id: end-of-file-fixer
    -   id: trailing-whitespace
-   repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
    -   id: black

```

### 3. Install the git hook scripts [¶](#3-install-the-git-hook-scripts)

* run `pre-commit install` to set up the git hook scripts

```
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit

```

* now `pre-commit` will run automatically on `git commit`!

### 4. (optional) Run against all the files [¶](#4-optional-run-against-all-the-files)

* it's usually a good idea to run the hooks against all of the files when adding
  new hooks (usually `pre-commit` will only run on the changed files during
  git hooks)

```
$ pre-commit run --all-files
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Initializing environment for https://github.com/psf/black.
[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/psf/black.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
Check Yaml...............................................................Passed
Fix End of Files.........................................................Passed
Trim Trailing Whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1

Files were modified by this hook. Additional output:

Fixing sample.py

black....................................................................Passed

```

* oops! looks like I had some trailing whitespace
* consider running that in [CI](#usage-in-continuous-integration) too

# Adding pre-commit plugins to your project [¶](#adding-pre-commit-plugins-to-your-project)

Once you have pre-commit installed, adding pre-commit plugins to your project
is done with the `.pre-commit-config.yaml` configuration file.

Add a file called `.pre-commit-config.yaml` to the root of your project. The
pre-commit config file describes what repositories and hooks are installed.

## .pre-commit-config.yaml - top level [¶](#pre-commit-configyaml---top-level)

|  |  |
| --- | --- |
| [`repos`](#top_level-repos) | A list of [repository mappings](#pre-commit-configyaml---repos). |
| [`default_install_hook_types`](#top_level-default_install_hook_types) | (optional: default `[pre-commit]`) a list of `--hook-type`s which will be used by default when running [`pre-commit install`](#pre-commit-install). |
| [`default_language_version`](#top_level-default_language_version) | (optional: default `{}`) a mapping from language to the default [`language_version`](#config-language_version) that should be used for that language. This will only override individual hooks that do not set [`language_version`](#config-language_version).  For example to use `python3.7` for `language: python` hooks:  ``` default_language_version:     python: python3.7  ``` |
| [`default_stages`](#top_level-default_stages) | (optional: default (all stages)) a configuration-wide default for the [`stages`](#config-stages) property of hooks. This will only override individual hooks that do not set [`stages`](#config-stages).  For example:  ``` default_stages: [pre-commit, pre-push]  ``` |
| [`files`](#top_level-files) | (optional: default `''`) global file include pattern. |
| [`exclude`](#top_level-exclude) | (optional: default `^$`) global file exclude pattern. |
| [`fail_fast`](#top_level-fail_fast) | (optional: default `false`) set to `true` to have pre-commit stop running hooks after the first failure. |
| [`minimum_pre_commit_version`](#top_level-minimum_pre_commit_version) | (optional: default `'0'`) require a minimum version of pre-commit. |

A sample top-level:

```
exclude: '^$'
fail_fast: false
repos:
-   ...

```

## .pre-commit-config.yaml - repos [¶](#pre-commit-configyaml---repos)

The repository mapping tells pre-commit where to get the code for the hook
from.

|  |  |
| --- | --- |
| [`repo`](#repos-repo) | the repository url to `git clone` from or one of the special sentinel values: [`local`](#repository-local-hooks), [`meta`](#meta-hooks). |
| [`rev`](#repos-rev) | the revision or tag to clone at. |
| [`hooks`](#repos-hooks) | A list of [hook mappings](#pre-commit-configyaml---hooks). |

A sample repository:

```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v1.2.3
    hooks:
    -   ...

```

## .pre-commit-config.yaml - hooks [¶](#pre-commit-configyaml---hooks)

The hook mapping configures which hook from the repository is used and allows
for customization. All optional keys will receive their default from the
repository's configuration.

|  |  |
| --- | --- |
| [`id`](#config-id) | which hook from the repository to use. |
| [`alias`](#config-alias) | (optional) allows the hook to be referenced using an additional id when using `pre-commit run <hookid>`. |
| [`name`](#config-name) | (optional) override the name of the hook - shown during hook execution. |
| [`language_version`](#config-language_version) | (optional) override the language version for the hook. See [Overriding Language Version](#overriding-language-version). |
| [`files`](#config-files) | (optional) override the default pattern for files to run on. |
| [`exclude`](#config-exclude) | (optional) file exclude pattern. |
| [`types`](#config-types) | (optional) override the default file types to run on (AND). See [Filtering files with types](#filtering-files-with-types). |
| [`types_or`](#config-types_or) | (optional) override the default file types to run on (OR). See [Filtering files with types](#filtering-files-with-types). |
| [`exclude_types`](#config-exclude_types) | (optional) file types to exclude. |
| [`args`](#config-args) | (optional) list of additional parameters to pass to the hook. |
| [`stages`](#config-stages) | (optional) selects which git hook(s) to run for. See [Confining hooks to run at certain stages](#confining-hooks-to-run-at-certain-stages). |
| [`additional_dependencies`](#config-additional_dependencies) | (optional) a list of dependencies that will be installed in the environment where this hook gets run. One useful application is to install plugins for hooks such as `eslint`. |
| [`always_run`](#config-always_run) | (optional) if `true`, this hook will run even if there are no matching files. |
| [`verbose`](#config-verbose) | (optional) if `true`, forces the output of the hook to be printed even when the hook passes. |
| [`log_file`](#config-log_file) | (optional) if present, the hook output will additionally be written to a file when the hook fails or [verbose](#config-verbose) is `true`. |

One example of a complete configuration:

```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v1.2.3
    hooks:
    -   id: trailing-whitespace

```

This configuration says to download the pre-commit-hooks project and run its
trailing-whitespace hook.

## Updating hooks automatically [¶](#updating-hooks-automatically)

You can update your hooks to the latest version automatically by running
[`pre-commit autoupdate`](#pre-commit-autoupdate). By default, this will
bring the hooks to the latest tag on the default branch.

# Usage [¶](#usage)

Run `pre-commit install` to install pre-commit into your git hooks. pre-commit
will now run on every commit. Every time you clone a project using pre-commit
running `pre-commit install` should always be the first thing you do.

If you want to manually run all pre-commit hooks on a repository, run
`pre-commit run --all-files`. To run individual hooks use
`pre-commit run <hook_id>`.

The first time pre-commit runs on a file it will automatically download,
install, and run the hook. Note that running a hook for the first time may be
slow. For example: If the machine does not have node installed, pre-commit
will download and build a copy of node.

```
$ pre-commit install
pre-commit installed at /home/asottile/workspace/pytest/.git/hooks/pre-commit
$ git commit -m "Add super awesome feature"
black....................................................................Passed
blacken-docs.........................................(no files to check)Skipped
Trim Trailing Whitespace.................................................Passed
Fix End of Files.........................................................Passed
Check Yaml...........................................(no files to check)Skipped
Debug Statements (Python)................................................Passed
Flake8...................................................................Passed
Reorder python imports...................................................Passed
pyupgrade................................................................Passed
rst ``code`` is two backticks........................(no files to check)Skipped
rst..................................................(no files to check)Skipped
changelog filenames..................................(no files to check)Skipped
[main 146c6c2c] Add super awesome feature
 1 file changed, 1 insertion(+)

```

# Creating new hooks [¶](#creating-new-hooks)

pre-commit currently supports hooks written in
[many languages](#supported-languages). As long as your git repo is an
installable package (gem, npm, pypi, etc.) or exposes an executable, it can be
used with pre-commit. Each git repo can support as many languages/hooks as you
want.

The hook must exit nonzero on failure or modify files.

A git repo containing pre-commit plugins must contain a `.pre-commit-hooks.yaml`
file that tells pre-commit:

|  |  |
| --- | --- |
| [`id`](#hooks-id) | the id of the hook - used in pre-commit-config.yaml. |
| [`name`](#hooks-name) | the name of the hook - shown during hook execution. |
| [`entry`](#hooks-entry) | the entry point - the executable to run. `entry` can also contain arguments that will not be overridden such as `entry: autopep8 -i`. |
| [`language`](#hooks-language) | the language of the hook - tells pre-commit how to install the hook. |
| [`files`](#hooks-files) | (optional: default `''`) the pattern of files to run on. |
| [`exclude`](#hooks-exclude) | (optional: default `^$`) exclude files that were matched by [`files`](#hooks-files). |
| [`types`](#hooks-types) | (optional: default `[file]`) list of file types to run on (AND). See [Filtering files with types](#filtering-files-with-types). |
| [`types_or`](#hooks-types_or) | (optional: default `[]`) list of file types to run on (OR). See [Filtering files with types](#filtering-files-with-types). |
| [`exclude_types`](#hooks-exclude_types) | (optional: default `[]`) the pattern of files to exclude. |
| [`always_run`](#hooks-always_run) | (optional: default `false`) if `true` this hook will run even if there are no matching files. |
| [`fail_fast`](#hooks-fail_fast) | (optional: default `false`) if `true` pre-commit will stop running hooks if this hook fails. |
| [`verbose`](#hooks-verbose) | (optional: default `false`) if `true`, forces the output of the hook to be printed even when the hook passes. |
| [`pass_filenames`](#hooks-pass_filenames) | (optional: default `true`) if `false` no filenames will be passed to the hook. |
| [`require_serial`](#hooks-require_serial) | (optional: default `false`) if `true` this hook will execute using a single process instead of in parallel. |
| [`description`](#hooks-description) | (optional: default `''`) description of the hook. used for metadata purposes only. |
| [`language_version`](#hooks-language_version) | (optional: default `default`) see [Overriding language version](#overriding-language-version). |
| [`minimum_pre_commit_version`](#hooks-minimum_pre_commit_version) | (optional: default `'0'`) allows one to indicate a minimum compatible pre-commit version. |
| [`args`](#hooks-args) | (optional: default `[]`) list of additional parameters to pass to the hook. |
| [`stages`](#hooks-stages) | (optional: default (all stages)) selects which git hook(s) to run for. See [Confining hooks to run at certain stages](#confining-hooks-to-run-at-certain-stages). |

For example:

```
-   id: trailing-whitespace
    name: Trim Trailing Whitespace
    description: This hook trims trailing whitespace.
    entry: trailing-whitespace-fixer
    language: python
    types: [text]

```

## Developing hooks interactively [¶](#developing-hooks-interactively)

Since the [`repo`](#repos-repo) property of `.pre-commit-config.yaml` can refer to anything
that `git clone ...` understands, it's often useful to point it at a local
directory while developing hooks.

[`pre-commit try-repo`](#pre-commit-try-repo) streamlines this process by
enabling a quick way to try out a repository. Here's how one might work
interactively:

*note*: you may need to provide `--commit-msg-filename` when using this
command with hook types `prepare-commit-msg` and `commit-msg`.

a commit is not necessary to `try-repo` on a local
directory. `pre-commit` will clone any tracked uncommitted changes.

```
~/work/hook-repo $ git checkout origin/main -b feature

# ... make some changes

# In another terminal or tab

~/work/other-repo $ pre-commit try-repo ../hook-repo foo --verbose --all-files
===============================================================================
Using config:
===============================================================================
repos:
-   repo: ../hook-repo
    rev: 84f01ac09fcd8610824f9626a590b83cfae9bcbd
    hooks:
    -   id: foo
===============================================================================
[INFO] Initializing environment for ../hook-repo.
Foo......................................................................Passed
- hook id: foo
- duration: 0.02s

Hello from foo hook!

```

## Supported languages [¶](#supported-languages)

* [conda](#conda)
* [coursier](#coursier)
* [dart](#dart)
* [docker](#docker)
* [docker\_image](#docker_image)
* [dotnet](#dotnet)
* [fail](#fail)
* [golang](#golang)
* [haskell](#haskell)
* [lua](#lua)
* [node](#node)
* [perl](#perl)
* [python](#python)
* [r](#r)
* [ruby](#ruby)
* [rust](#rust)
* [swift](#swift)
* [pygrep](#pygrep)
* [script](#script)
* [system](#system)

### conda [¶](#conda)

The hook repository must contain an `environment.yml` file which will be used
via `conda env create --file environment.yml ...` to create the environment.

The `conda` language also supports [`additional_dependencies`](#config-additional_dependencies)
and will pass any of the values directly into `conda install`. This language can therefore be
used with [local](#repository-local-hooks) hooks.

`mamba` or `micromamba` can be used to install instead via the
`PRE_COMMIT_USE_MAMBA=1` or `PRE_COMMIT_USE_MICROMAMBA=1` environment
variables.

**Support:** `conda` hooks work as long as there is a system-installed `conda`
binary (such as [`miniconda`](https://docs.conda.io/en/latest/miniconda.html)).
It has been tested on linux, macOS, and windows.

### coursier [¶](#coursier)

The hook repository must have a `.pre-commit-channel` folder and that folder
must contain the coursier
[application descriptors](https://get-coursier.io/docs/2.0.0-RC6-10/cli-install.html#application-descriptor-reference)
for the hook to install. For configuring coursier hooks, your
[`entry`](#hooks-entry) should correspond to an executable installed from the
repository's `.pre-commit-channel` folder.

**Support:** `coursier` hooks are known to work on any system which has the
`cs` or `coursier` package manager installed. The specific coursier
applications you install may depend on various versions of the JVM, consult
the hooks' documentation for clarification. It has been tested on linux.

pre-commit also supports the `coursier` naming of the package manager
executable.

*new in 3.0.0*: `language: coursier` hooks now support `repo: local` and
`additional_dependencies`.

### dart [¶](#dart)

The hook repository must have a `pubspec.yaml` -- this must contain an
`executables` section which will list the binaries that will be available
after installation. Match the [`entry`](#hooks-entry) to an executable.

`pre-commit` will build each executable using `dart compile exe bin/{executable}.dart`.

`language: dart` also supports [`additional_dependencies`](#config-additional_dependencies).
to specify a version for a dependency, separate the package name by a `:`:

```
        additional_dependencies: ['hello_world_dart:1.0.0']

```

**Support:** `dart` hooks are known to work on any system which has the `dart`
sdk installed. It has been tested on linux, macOS, and windows.

### docker [¶](#docker)

The hook repository must have a `Dockerfile`. It will be installed via
`docker build .`.

Running Docker hooks requires a running Docker engine on your host. For
configuring Docker hooks, your [`entry`](#hooks-entry) should correspond to an executable
inside the Docker container, and will be used to override the default container
entrypoint. Your Docker `CMD` will not run when pre-commit passes a file list
as arguments to the run container command. Docker allows you to use any
language that's not supported by pre-commit as a builtin.

pre-commit will automatically mount the repository source as a volume using
`-v $PWD:/src:rw,Z` and set the working directory using `--workdir /src`.

**Support:** docker hooks are known to work on any system which has a working
`docker` executable. It has been tested on linux and macOS. Hooks that are
run via `boot2docker` are known to be unable to make modifications to files.

See [this repository](https://github.com/pre-commit/pre-commit-docker-flake8)
for an example Docker-based hook.

### docker\_image [¶](#docker_image)

A more lightweight approach to `docker` hooks. The `docker_image`
"language" uses existing docker images to provide hook executables.

`docker_image` hooks can be conveniently configured as [local](#repository-local-hooks)
hooks.

The [`entry`](#hooks-entry) specifies the docker tag to use. If an image has an
`ENTRYPOINT` defined, nothing special is needed to hook up the executable.
If the container does not specify an `ENTRYPOINT` or you want to change the
entrypoint you can specify it as well in your [`entry`](#hooks-entry).

For example:

```
-   id: dockerfile-provides-entrypoint
    name: ...
    language: docker_image
    entry: my.registry.example.com/docker-image-1:latest
-   id: dockerfile-no-entrypoint-1
    name: ...
    language: docker_image
    entry: --entrypoint my-exe my.registry.example.com/docker-image-2:latest
# Alternative equivalent solution
-   id: dockerfile-no-entrypoint-2
    name: ...
    language: docker_image
    entry: my.registry.example.com/docker-image-3:latest my-exe

```

### dotnet [¶](#dotnet)

dotnet hooks are installed using the system installation of the dotnet CLI.

Hook repositories must contain a dotnet CLI tool which can be `pack`ed and
`install`ed as per [this](https://docs.microsoft.com/en-us/dotnet/core/tools/global-tools-how-to-create)
example. The `entry` should match an executable created by building the
repository. Additional dependencies are not currently supported.

**Support:** dotnet hooks are known to work on any system which has the dotnet
CLI installed. It has been tested on linux and windows.

### fail [¶](#fail)

A lightweight [`language`](#hooks-language) to forbid files by filename. The `fail` language is
especially useful for [local](#repository-local-hooks) hooks.

The [`entry`](#hooks-entry) will be printed when the hook fails. It is suggested to provide
a brief description for [`name`](#hooks-name) and more verbose fix instructions in [`entry`](#hooks-entry).

Here's an example which prevents any file except those ending with `.rst` from
being added to the `changelog` directory:

```
-   repo: local
    hooks:
    -   id: changelogs-rst
        name: changelogs must be rst
        entry: changelog filenames must end in .rst
        language: fail
        files: 'changelog/.*(?<!\.rst)$'

```

### golang [¶](#golang)

The hook repository must contain go source code. It will be installed via
`go install ./...`. pre-commit will create an isolated `GOPATH` for each hook
and the [`entry`](#hooks-entry) should match an executable which will get installed into the
`GOPATH`'s `bin` directory.

This language supports `additional_dependencies` and will pass any of the values directly to `go install`. It can be used as a `repo: local` hook.

*changed in 2.17.0*: previously `go get ./...` was used

*new in 3.0.0*: pre-commit will bootstrap `go` if it is not present. `language: golang`
also now supports `language_version`

**Support:** golang hooks are known to work on any system which has go
installed. It has been tested on linux, macOS, and windows.

### haskell [¶](#haskell)

*new in 3.4.0*

The hook repository must have one or more `*.cabal` files. Once installed
the `executable`s from these packages will be available to use with `entry`.

This language supports `additional_dependencies` so it can be used as a
`repo: local` hook.

**Support:** haskell hooks are known to work on any system which has `cabal`
installed. It has been tested on linux, macOS, and windows.

### julia [¶](#julia)

*new in 4.1.0*

For configuring julia hooks, your [`entry`](#hooks-entry) should be a path to a julia source
file relative to the hook repository (optionally with arguments).

Hooks run in an isolated package environment defined by a `Project.toml` file (optionally
with a `Manifest.toml` file) in the hook repository. If no `Project.toml` file is found the
hook is run in an empty environment.

Julia hooks support [`additional_dependencies`](#config-additional_dependencies) which can
be used to augment, or override, the existing environment in the hooks repository. This also
means that julia can be used as a `repo: local` hook. `additional_dependencies` are passed
to `pkg> add` and should be specified using
[Pkg REPL mode syntax](https://pkgdocs.julialang.org/v1/repl/#repl-add).

Examples:

```
- id: foo-without-args
  name: ...
  language: julia
  entry: bin/foo.jl
- id: bar-with-args
  name: ...
  language: julia
  entry: bin/bar.jl --arg1 --arg2
- id: baz-with-extra-deps
  name: ...
  language: julia
  entry: bin/baz.jl
  additional_dependencies:
   - 'ExtraDepA@1'
   - '[email protected]'

```

**Support:** julia hooks are known to work on any system which has `julia` installed.

### lua [¶](#lua)

Lua hooks are installed with the version of Lua that is used by Luarocks.

**Support:** Lua hooks are known to work on any system which has Luarocks
installed. It has been tested on linux and macOS and *may* work on windows.

### node [¶](#node)

The hook repository must have a `package.json`. It will be installed via
`npm install .`. The installed package will provide an executable that will
match the [`entry`](#hooks-entry) – usually through `bin` in package.json.

**Support:** node hooks work without any system-level dependencies. It has
been tested on linux, windows, and macOS and *may* work under cygwin.

### perl [¶](#perl)

Perl hooks are installed using the system installation of
[cpan](https://perldoc.perl.org/cpan), the CPAN package installer
that comes with Perl.

Hook repositories must have something that `cpan` supports, typically
`Makefile.PL` or `Build.PL`, which it uses to install an executable to
use in the [`entry`](#hooks-entry) definition for your hook. The repository will be installed
via `cpan -T .` (with the installed files stored in your pre-commit cache,
not polluting other Perl installations).

When specifying [`additional_dependencies`](#config-additional_dependencies) for Perl, you can use any of the
[install argument formats understood by `cpan`](https://perldoc.perl.org/CPAN#get%2c-make%2c-test%2c-install%2c-clean-modules-or-distributions).

**Support:** Perl hooks currently require a pre-existing Perl installation,
including the `cpan` tool in `PATH`. It has been tested on linux, macOS, and
Windows.

### python [¶](#python)

The hook repository must be installable via `pip install .` (usually by either
`setup.py` or `pyproject.toml`). The installed package will provide an
executable that will match the [`entry`](#hooks-entry) – usually through `console_scripts` or
`scripts` in setup.py.

This language also supports `additional_dependencies`
so it can be used with [local](#repository-local-hooks) hooks.
The specified dependencies will be appended to the `pip install` command.

**Support:** python hooks work without any system-level dependencies. It
has been tested on linux, macOS, windows, and cygwin.

### r [¶](#r)

This hook repository must have a `renv.lock` file that will be restored with
[`renv::restore()`](https://rstudio.github.io/renv/reference/restore.html) on
hook installation. If the repository is an R package (i.e. has `Type: Package`
in `DESCRIPTION`), it is installed. The supported syntax in [`entry`](#hooks-entry) is
`Rscript -e {expression}` or `Rscript path/relative/to/hook/root`. The
R Startup process is skipped (emulating `--vanilla`), as all configuration
should be exposed via [`args`](#hooks-args) for maximal transparency and portability.

When specifying [`additional_dependencies`](#config-additional_dependencies)
for R, you can use any of the install argument formats understood by
[`renv::install()`](https://rstudio.github.io/renv/reference/install.html#examples).

**Support:** `r` hooks work as long as [`R`](https://www.r-project.org) is
installed and on `PATH`. It has been tested on linux, macOS, and windows.

### ruby [¶](#ruby)

The hook repository must have a `*.gemspec`. It will be installed via
`gem build *.gemspec && gem install *.gem`. The installed package will
produce an executable that will match the [`entry`](#hooks-entry) – usually through
`executables` in your gemspec.

**Support:** ruby hooks work without any system-level dependencies. It has
been tested on linux and macOS and *may* work under cygwin.

### rust [¶](#rust)

Rust hooks are installed using [Cargo](https://github.com/rust-lang/cargo),
Rust's official package manager.

Hook repositories must have a `Cargo.toml` file which produces at least one
binary ([example](https://github.com/chriskuehl/example-rust-pre-commit-hook)),
whose name should match the [`entry`](#hooks-entry) definition for your hook. The repo will be
installed via `cargo install --bins` (with the binaries stored in your
pre-commit cache, not polluting your user-level Cargo installations).

When specifying [`additional_dependencies`](#config-additional_dependencies) for Rust, you can use the syntax
`{package_name}:{package_version}` to specify a new library dependency (used to
build *your* hook repo), or the special syntax
`cli:{package_name}:{package_version}` for a CLI dependency (built separately,
with binaries made available for use by hooks).

pre-commit will bootstrap `rust` if it is not present.
`language: rust` also supports `language_version`

**Support:** It has been tested on linux, Windows, and macOS.

### swift [¶](#swift)

The hook repository must have a `Package.swift`. It will be installed via
`swift build -c release`. The [`entry`](#hooks-entry) should match an executable created by
building the repository.

**Support:** swift hooks are known to work on any system which has swift
installed. It has been tested on linux and macOS.

### pygrep [¶](#pygrep)

A cross-platform python implementation of `grep` – pygrep hooks are a quick
way to write a simple hook which prevents commits by file matching. Specify
the regex as the [`entry`](#hooks-entry). The [`entry`](#hooks-entry) may be any python
[regular expression](#regular-expressions). For case insensitive regexes you
can apply the `(?i)` flag as the start of your entry, or use `args: [-i]`.

For multiline matches, use `args: [--multiline]`.

To require all files to match, use `args: [--negate]`.

**Support:** pygrep hooks are supported on all platforms which pre-commit runs
on.

### script [¶](#script)

Script hooks provide a way to write simple scripts which validate files. The
[`entry`](#hooks-entry) should be a path relative to the root of the hook repository.

This hook type will not be given a virtual environment to work with – if it
needs additional dependencies the consumer must install them manually.

**Support:** the support of script hooks depend on the scripts themselves.

### system [¶](#system)

System hooks provide a way to write hooks for system-level executables which
don't have a supported language above (or have special environment
requirements that don't allow them to run in isolation such as pylint).

This hook type will not be given a virtual environment to work with – if it
needs additional dependencies the consumer must install them manually.

**Support:** the support of system hooks depend on the executables.

# Command line interface [¶](#command-line-interface)

All pre-commit commands take the following options:

* `--color {auto,always,never}`: whether to use color in output.
  Defaults to `auto`. can be overridden by using
  `PRE_COMMIT_COLOR={auto,always,never}` or disabled using `TERM=dumb`.
* `-c CONFIG`, `--config CONFIG`: path to alternate config file
* `-h`, `--help`: show help and available options.

`pre-commit` exits with specific codes:

* `1`: a detected / expected error
* `3`: an unexpected error
* `130`: the process was interrupted by `^C`

## pre-commit autoupdate [options] [¶](#pre-commit-autoupdate)

Auto-update pre-commit config to the latest repos' versions.

Options:

* `--bleeding-edge`: update to the bleeding edge of the default branch instead
  of the latest tagged version (the default behaviour).
* `--freeze`: Store "frozen" hashes in [`rev`](#repos-rev) instead of tag names.
* `--repo REPO`: Only update this repository. This option may be specified
  multiple times.
* `-j` / `--jobs`: *new in 3.3.0* Number of threads to use (default: 1).

Here are some sample invocations using this `.pre-commit-config.yaml`:

```
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v2.1.0
    hooks:
    -   id: trailing-whitespace
-   repo: https://github.com/asottile/pyupgrade
    rev: v1.25.0
    hooks:
    -   id: pyupgrade
        args: [--py36-plus]

```

```
$ : default: update to latest tag on default branch
$ pre-commit autoupdate  # by default: pick tags
Updating https://github.com/pre-commit/pre-commit-hooks ... updating v2.1.0 -> v2.4.0.
Updating https://github.com/asottile/pyupgrade ... updating v1.25.0 -> v1.25.2.
$ grep rev: .pre-commit-config.yaml
    rev: v2.4.0
    rev: v1.25.2

```

```
$ : update a specific repository to the latest revision of the default branch
$ pre-commit autoupdate --bleeding-edge --repo https://github.com/pre-commit/pre-commit-hooks
Updating https://github.com/pre-commit/pre-commit-hooks ... updating v2.1.0 -> 5df1a4bf6f04a1ed3a643167b38d502575e29aef.
$ grep rev: .pre-commit-config.yaml
    rev: 5df1a4bf6f04a1ed3a643167b38d502575e29aef
    rev: v1.25.0

```

```
$ : update to frozen versions
$ pre-commit autoupdate --freeze
Updating https://github.com/pre-commit/pre-commit-hooks ... updating v2.1.0 -> v2.4.0 (frozen).
Updating https://github.com/asottile/pyupgrade ... updating v1.25.0 -> v1.25.2 (frozen).
$ grep rev: .pre-commit-config.yaml
    rev: 0161422b4e09b47536ea13f49e786eb3616fe0d7  # frozen: v2.4.0
    rev: 34a269fd7650d264e4de7603157c10d0a9bb8211  # frozen: v1.25.2

```

pre-commit will preferentially pick tags containing a `.` if there are ties.

## pre-commit clean [options] [¶](#pre-commit-clean)

Clean out cached pre-commit files.

Options: (no additional options)

## pre-commit gc [options] [¶](#pre-commit-gc)

Clean unused cached repos.

`pre-commit` keeps a cache of installed hook repositories which grows over
time. This command can be run periodically to clean out unused repos from
the cache directory.

Options: (no additional options)

## pre-commit init-templatedir DIRECTORY [options] [¶](#pre-commit-init-templatedir)

Install hook script in a directory intended for use with
`git config init.templateDir`.

Options:

* `-t HOOK_TYPE, --hook-type HOOK_TYPE`:
  which hook type to install.

Some example useful invocations:

```
git config --global init.templateDir ~/.git-template
pre-commit init-templatedir ~/.git-template

```

For Windows cmd.exe use `%HOMEPATH%` instead of `~`:

```
pre-commit init-templatedir %HOMEPATH%\.git-template

```

For Windows PowerShell use `$HOME` instead of `~`:

```
pre-commit init-templatedir $HOME\.git-template

```

Now whenever a repository is cloned or created, it will have the hooks set up
already!

## pre-commit install [options] [¶](#pre-commit-install)

Install the pre-commit script.

Options:

* `-f`, `--overwrite`: Replace any existing git hooks with the pre-commit
  script.
* `--install-hooks`: Also install environments for all available hooks now
  (rather than when they are first executed). See [`pre-commit install-hooks`](#pre-commit-install-hooks).
* `-t HOOK_TYPE, --hook-type HOOK_TYPE`:
  Specify which hook type to install.
* `--allow-missing-config`: Hook scripts will permit a missing configuration
  file.

Some example useful invocations:

* `pre-commit install`: Default invocation. Installs the hook scripts
  alongside any existing git hooks.
* `pre-commit install --install-hooks --overwrite`: Idempotently replaces
  existing git hook scripts with pre-commit, and also installs hook
  environments.

`pre-commit install` will install hooks from
[`default_install_hook_types`](#top_level-default_install_hook_types) if
`--hook-type` is not specified on the command line.

## pre-commit install-hooks [options] [¶](#pre-commit-install-hooks)

Install all missing environments for the available hooks. Unless this command or
`install --install-hooks` is executed, each hook's environment is created the
first time the hook is called.

Each hook is initialized in a separate environment appropriate to the language
the hook is written in. See [supported languages](#supported-languages).

This command does not install the pre-commit script. To install the script along with
the hook environments in one command, use `pre-commit install --install-hooks`.

Options: (no additional options)

## pre-commit migrate-config [options] [¶](#pre-commit-migrate-config)

Migrate list configuration to the new map configuration format.

Options: (no additional options)

## pre-commit run [hook-id] [options] [¶](#pre-commit-run)

Run hooks.

Options:

* `[hook-id]`: specify a single hook-id to run only that hook.
* `-a`, `--all-files`: run on all the files in the repo.
* `--files [FILES [FILES ...]]`: specific filenames to run hooks on.
* `--from-ref FROM_REF` + `--to-ref TO_REF`: run against the files changed
  between `FROM_REF...TO_REF` in git.
* `--hook-stage STAGE`: select a [`stage` to run](#confining-hooks-to-run-at-certain-stages).
* `--show-diff-on-failure`: when hooks fail, run `git diff` directly afterward.
* `-v`, `--verbose`: produce hook output independent of success. Include hook
  ids in output.

Some example useful invocations:

* `pre-commit run`: this is what pre-commit runs by default when committing.
  This will run all hooks against currently staged files.
* `pre-commit run --all-files`: run all the hooks against all the files. This
  is a useful invocation if you are using pre-commit in CI.
* `pre-commit run flake8`: run the `flake8` hook against all staged files.
* `git ls-files -- '*.py' | xargs pre-commit run --files`: run all hooks
  against all `*.py` files in the repository.
* `pre-commit run --from-ref HEAD^^^ --to-ref HEAD`: run against the files that
  have changed between `HEAD^^^` and `HEAD`. This form is useful when
  leveraged in a pre-receive hook.

## pre-commit sample-config [options] [¶](#pre-commit-sample-config)

Produce a sample `.pre-commit-config.yaml`.

Options: (no additional options)

## pre-commit try-repo REPO [options] [¶](#pre-commit-try-repo)

Try the hooks in a repository, useful for developing new hooks.
`try-repo` can also be used for testing out a repository before adding it to
your configuration. `try-repo` prints a configuration it generates based on
the remote hook repository before running the hooks.

Options:

* `REPO`: required clonable hooks repository. Can be a local path on
  disk.
* `--ref REF`: Manually select a ref to run against, otherwise the `HEAD`
  revision will be used.
* `pre-commit try-repo` also supports all available options for
  [`pre-commit run`](#pre-commit-run).

Some example useful invocations:

* `pre-commit try-repo https://github.com/pre-commit/pre-commit-hooks`: runs
  all the hooks in the latest revision of `pre-commit/pre-commit-hooks`.
* `pre-commit try-repo ../path/to/repo`: run all the hooks in a repository on
  disk.
* `pre-commit try-repo ../pre-commit-hooks flake8`: run only the `flake8` hook
  configured in a local `../pre-commit-hooks` repository.
* See [`pre-commit run`](#pre-commit-run) for more useful `run` invocations
  which are also supported by `pre-commit try-repo`.

## pre-commit uninstall [options] [¶](#pre-commit-uninstall)

Uninstall the pre-commit script.

Options:

* `-t HOOK_TYPE, --hook-type HOOK_TYPE`: which hook type to uninstall.

# Advanced features [¶](#advanced-features)

## Running in migration mode [¶](#running-in-migration-mode)

By default, if you have existing hooks `pre-commit install` will install in a
migration mode which runs both your existing hooks and hooks for pre-commit.
To disable this behavior, pass `-f` / `--overwrite` to the `install` command.
If you decide not to use pre-commit, `pre-commit uninstall` will
restore your hooks to the state prior to installation.

## Temporarily disabling hooks [¶](#temporarily-disabling-hooks)

Not all hooks are perfect so sometimes you may need to skip execution of one
or more hooks. pre-commit solves this by querying a `SKIP` environment
variable. The `SKIP` environment variable is a comma separated list of hook
ids. This allows you to skip a single hook instead of `--no-verify`ing the
entire commit.

```
$ SKIP=flake8 git commit -m "foo"

```

## Confining hooks to run at certain stages [¶](#confining-hooks-to-run-at-certain-stages)

pre-commit supports many different types of `git` hooks (not just
`pre-commit`!).

Providers of hooks can select which git hooks they run on by setting the
[`stages`](#hooks-stages) property in `.pre-commit-hooks.yaml` -- this can
also be overridden by setting [`stages`](#config-stages) in
`.pre-commit-config.yaml`. If `stages` is not set in either of those places
the default value will be pulled from the top-level
[`default_stages`](#top_level-default_stages) option (which defaults to *all*
stages). By default, tools are enabled for [every hook type](#supported-git-hooks)
that pre-commit supports.

*new in 3.2.0*: The values of `stages` match the hook names. Previously,
`commit`, `push`, and `merge-commit` matched `pre-commit`, `pre-push`, and
`pre-merge-commit` respectively.

The `manual` stage (via `stages: [manual]`) is a special stage which will not
be automatically triggered by any `git` hook -- this is useful if you want to
add a tool which is not automatically run, but is run on demand using
`pre-commit run --hook-stage manual [hookid]`.

If you are authoring a tool, it is usually a good idea to provide an appropriate
`stages` property. For example a reasonable setting for a linter or code
formatter would be `stages: [pre-commit, pre-merge-commit, pre-push, manual]`.

To install `pre-commit` for particular git hooks, pass `--hook-type` to
`pre-commit install`. This can be specified multiple times such as:

```
$ pre-commit install --hook-type pre-commit --hook-type pre-push
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/pre-push

```

Additionally, one can specify a default set of git hook types to be installed
for by setting the top-level [`default_install_hook_types`](#top_level-default_install_hook_types).

For example:

```
default_install_hook_types: [pre-commit, pre-push, commit-msg]

```

```
$ pre-commit  install
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/pre-push
pre-commit installed at .git/hooks/commit-msg

```

## Supported git hooks [¶](#supported-git-hooks)

* [commit-msg](#commit-msg)
* [post-checkout](#post-checkout)
* [post-commit](#post-commit)
* [post-merge](#post-merge)
* [post-rewrite](#post-rewrite)
* [pre-commit](#pre-commit)
* [pre-merge-commit](#pre-merge-commit)
* [pre-push](#pre-push)
* [pre-rebase](#pre-rebase)
* [prepare-commit-msg](#prepare-commit-msg)

### commit-msg [¶](#commit-msg)

[git commit-msg docs](https://git-scm.com/docs/githooks#_commit_msg)

`commit-msg` hooks will be passed a single filename -- this file contains the
current contents of the commit message to be validated. The commit will be
aborted if there is a nonzero exit code.

### post-checkout [¶](#post-checkout)

[git post-checkout docs](https://git-scm.com/docs/githooks#_post_checkout)

post-checkout hooks run *after* a `checkout` has occurred and can be used to
set up or manage state in the repository.

`post-checkout` hooks do not operate on files so they must be set as
`always_run: true` or they will always be skipped.

environment variables:

* `PRE_COMMIT_FROM_REF`: the first argument to the `post-checkout` git hook
* `PRE_COMMIT_TO_REF`: the second argument to the `post-checkout` git hook
* `PRE_COMMIT_CHECKOUT_TYPE`: the third argument to the `post-checkout` git hook

### post-commit [¶](#post-commit)

[git post-commit docs](https://git-scm.com/docs/githooks#_post_commit)

`post-commit` runs after the commit has already succeeded so it cannot be used
to prevent the commit from happening.

`post-commit` hooks do not operate on files so they must be set as
`always_run: true` or they will always be skipped.

### post-merge [¶](#post-merge)

[git post-merge docs](https://git-scm.com/docs/githooks#_post_merge)

`post-merge` runs after a successful `git merge`.

`post-merge` hooks do not operate on files so they must be set as
`always_run: true` or they will always be skipped.

environment variables:

* `PRE_COMMIT_IS_SQUASH_MERGE`: the first argument to the `post-merge` git hook.

### post-rewrite [¶](#post-rewrite)

[git post-rewrite docs](https://git-scm.com/docs/githooks#_post_rewrite)

`post-rewrite` runs after a git command which modifies history such as
`git commit --amend` or `git rebase`.

`post-rewrite` hooks do not operate on files so they must be set as
`always_run: true` or they will always be skipped.

environment variables:

* `PRE_COMMIT_REWRITE_COMMAND`: the first argument to the `post-rewrite` git hook.

### pre-commit [¶](#pre-commit)

[git pre-commit docs](https://git-scm.com/docs/githooks#_pre_commit)

`pre-commit` is triggered before the commit is finalized to allow checks on the
code being committed. Running hooks on unstaged changes can lead to both
false-positives and false-negatives during committing. pre-commit only runs
on the staged contents of files by temporarily stashing the unstaged changes
while running hooks.

### pre-merge-commit [¶](#pre-merge-commit)

[git pre-merge-commit docs](https://git-scm.com/docs/githooks#_pre_merge_commit)

`pre-merge-commit` fires after a merge succeeds but before the merge commit is
created. This hook runs on all staged files from the merge.

Note that you need to be using at least git 2.24 for this hook.

### pre-push [¶](#pre-push)

[git pre-push docs](https://git-scm.com/docs/githooks#_pre_push)

`pre-push` is triggered on `git push`.

environment variables:

* `PRE_COMMIT_FROM_REF`: the revision that is being pushed to.
* `PRE_COMMIT_TO_REF`: the local revision that is being pushed to the remote.
* `PRE_COMMIT_REMOTE_NAME`: which remote is being pushed to (for example `origin`)
* `PRE_COMMIT_REMOTE_URL`: the url of the remote that is being pushed to (for
  example `[[email protected]](/cdn-cgi/l/email-protection):pre-commit/pre-commit`)
* `PRE_COMMIT_REMOTE_BRANCH`: the name of the remote branch to which we are
  pushing (for example `refs/heads/target-branch`)
* `PRE_COMMIT_LOCAL_BRANCH`: the name of the local branch that is being pushed
  to the remote (for example `HEAD`)

### pre-rebase [¶](#pre-rebase)

*new in 3.2.0*

[git pre-rebase docs](https://git-scm.com/docs/githooks#_pre_rebase)

`pre-rebase` is triggered before a rebase occurs. A hook failure can cancel a
rebase from occurring.

`pre-rebase` hooks do not operate on files so they must be set as
`always_run: true` or they will always be skipped.

environment variables:

* `PRE_COMMIT_PRE_REBASE_UPSTREAM`: the first argument to the `pre-rebase` git hook
* `PRE_COMMIT_PRE_REBASE_BRANCH`: the second argument to the `pre-rebase` git hook.

### prepare-commit-msg [¶](#prepare-commit-msg)

[git prepare-commit-msg docs](https://git-scm.com/docs/githooks#_prepare_commit_msg)

`prepare-commit-msg` hooks will be passed a single filename -- this file may
be empty or it could contain the commit message from `-m` or from other
templates. `prepare-commit-msg` hooks can modify the contents of this file to
change what will be committed. A hook may want to check for `GIT_EDITOR=:` as
this indicates that no editor will be launched. If a hook exits nonzero, the
commit will be aborted.

environment variables:

* `PRE_COMMIT_COMMIT_MSG_SOURCE`: the second argument to the
  `prepare-commit-msg` git hook
* `PRE_COMMIT_COMMIT_OBJECT_NAME`: the third argument to the
  `prepare-commit-msg` git hook

## Passing arguments to hooks [¶](#passing-arguments-to-hooks)

Sometimes hooks require arguments to run correctly. You can pass static
arguments by specifying the [`args`](#config-args) property in your `.pre-commit-config.yaml`
as follows:

```
-   repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
    -   id: flake8
        args: [--max-line-length=131]

```

This will pass `--max-line-length=131` to `flake8`.

### Arguments pattern in hooks [¶](#arguments-pattern-in-hooks)

If you are writing your own custom hook, your hook should expect to receive
the [`args`](#config-args) value and then a list of staged files.

For example, assuming a `.pre-commit-config.yaml`:

```
-   repo: https://github.com/path/to/your/hook/repo
    rev: badf00ddeadbeef
    hooks:
    -   id: my-hook-script-id
        args: [--myarg1=1, --myarg1=2]

```

When you next run `pre-commit`, your script will be called:

```
path/to/script-or-system-exe --myarg1=1 --myarg1=2 dir/file1 dir/file2 file3

```

If the [`args`](#config-args) property is empty or not defined, your script will be called:

```
path/to/script-or-system-exe dir/file1 dir/file2 file3

```

When creating local hooks, there's no reason to put command arguments
into [`args`](#config-args) as there is nothing which can override them --
instead put your arguments directly in the hook [`entry`](#hooks-entry).

For example:

```
-   repo: local
    hooks:
    -   id: check-requirements
        name: check requirements files
        language: system
        entry: python -m scripts.check_requirements --compare
        files: ^requirements.*\.txt$

```

## Repository local hooks [¶](#repository-local-hooks)

Repository-local hooks are useful when:

* The scripts are tightly coupled to the repository and it makes sense to
  distribute the hook scripts with the repository.
* Hooks require state that is only present in a built artifact of your
  repository (such as your app's virtualenv for pylint).
* The official repository for a linter doesn't have the pre-commit metadata.

You can configure repository-local hooks by specifying the [`repo`](#repos-repo) as the
sentinel `local`.

local hooks can use any language which supports [`additional_dependencies`](#config-additional_dependencies)
or [`docker_image`](#docker_image) / [`fail`](#fail) / [`pygrep`](#pygrep) / [`script`](#script) / [`system`](#system).
This enables you to install things which previously would require a trivial
mirror repository.

A `local` hook must define [`id`](#hooks-id), [`name`](#hooks-name), [`language`](#hooks-language),
[`entry`](#hooks-entry), and [`files`](#hooks-files) / [`types`](#hooks-types)
as specified under [Creating new hooks](#new-hooks).

Here's an example configuration with a few `local` hooks:

```
-   repo: local
    hooks:
    -   id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        require_serial: true
    -   id: check-x
        name: Check X
        entry: ./bin/check-x.sh
        language: script
        files: \.x$
    -   id: scss-lint
        name: scss-lint
        entry: scss-lint
        language: ruby
        language_version: 2.1.5
        types: [scss]
        additional_dependencies: ['scss_lint:0.52.0']

```

## meta hooks [¶](#meta-hooks)

`pre-commit` provides several hooks which are useful for checking the
pre-commit configuration itself. These can be enabled using `repo: meta`.

```
-   repo: meta
    hooks:
    -   id: ...

```

The currently available `meta` hooks:

|  |  |
| --- | --- |
| [`check-hooks-apply`](#meta-check_hooks_apply) | ensures that the configured hooks apply to at least one file in the repository. |
| [`check-useless-excludes`](#meta-check_useless_excludes) | ensures that `exclude` directives apply to *any* file in the repository. |
| [`identity`](#meta-identity) | a simple hook which prints all arguments passed to it, useful for debugging. |

## automatically enabling pre-commit on repositories [¶](#automatically-enabling-pre-commit-on-repositories)

`pre-commit init-templatedir` can be used to set up a skeleton for `git`'s
`init.templateDir` option. This means that any newly cloned repository will
automatically have the hooks set up without the need to run
`pre-commit install`.

To configure, first set `git`'s `init.templateDir` -- in this example I'm
using `~/.git-template` as my template directory.

```
$ git config --global init.templateDir ~/.git-template
$ pre-commit init-templatedir ~/.git-template
pre-commit installed at /home/asottile/.git-template/hooks/pre-commit

```

Now whenever you clone a pre-commit enabled repo, the hooks will already be
set up!

```
$ git clone -q [email protected]:asottile/pyupgrade
$ cd pyupgrade
$ git commit --allow-empty -m 'Hello world!'
Check docstring is first.............................(no files to check)Skipped
Check Yaml...........................................(no files to check)Skipped
Debug Statements (Python)............................(no files to check)Skipped
...

```

`init-templatedir` uses the `--allow-missing-config` option from
`pre-commit install` so repos without a config will be skipped:

```
$ git init sample
Initialized empty Git repository in /tmp/sample/.git/
$ cd sample
$ git commit --allow-empty -m 'Initial commit'
`.pre-commit-config.yaml` config file not found. Skipping `pre-commit`.
[main (root-commit) d1b39c1] Initial commit

```

To still require opt-in, but prompt the user to set up pre-commit use a
template hook as follows (for example in `~/.git-template/hooks/pre-commit`).

```
#!/usr/bin/env bash
if [ -f .pre-commit-config.yaml ]; then
    echo 'pre-commit configuration detected, but `pre-commit install` was never run' 1>&2
    exit 1
fi

```

With this, a forgotten `pre-commit install` produces an error on commit:

```
$ git clone -q https://github.com/asottile/pyupgrade
$ cd pyupgrade/
$ git commit -m 'foo'
pre-commit configuration detected, but `pre-commit install` was never run

```

## Filtering files with types [¶](#filtering-files-with-types)

Filtering with `types` provides several advantages over traditional filtering
with `files`.

* no error-prone regular expressions
* files can be matched by their shebang (even when extensionless)
* symlinks / submodules can be easily ignored

`types` is specified per hook as an array of tags. The tags are discovered
through a set of heuristics by the
[identify](https://github.com/pre-commit/identify) library. `identify` was
chosen as it is a small portable pure python library.

Some of the common tags you'll find from identify:

* `file`
* `symlink`
* `directory` - in the context of pre-commit this will be a submodule
* `executable` - whether the file has the executable bit set
* `text` - whether the file looks like a text file
* `binary` - whether the file looks like a binary file
* [tags by extension / naming convention](https://github.com/pre-commit/identify/blob/main/identify/extensions.py)
* [tags by shebang (`#!`)](https://github.com/pre-commit/identify/blob/main/identify/interpreters.py)

To discover the type of any file on disk, you can use `identify`'s cli:

```
$ identify-cli setup.py
["file", "non-executable", "python", "text"]
$ identify-cli some-random-file
["file", "non-executable", "text"]
$ identify-cli --filename-only some-random-file; echo $?
1

```

If a file extension you use is not supported, please
[submit a pull request](https://github.com/pre-commit/identify)!

`types`, `types_or`, and `files` are evaluated together with `AND` when
filtering. Tags within `types` are also evaluated using `AND`.

Tags within `types_or` are evaluated using `OR`.

For example:

```
    files: ^foo/
    types: [file, python]

```

will match a file `foo/1.py` but will not match `setup.py`.

Another example:

```
    files: ^foo/
    types_or: [javascript, jsx, ts, tsx]

```

will match any of `foo/bar.js` / `foo/bar.jsx` / `foo/bar.ts` / `foo/bar.tsx`
but not `baz.js`.

If you want to match a file path that isn't included in a `type` when using an
existing hook you'll need to revert back to `files` only matching by overriding
the `types` setting. Here's an example of using `check-json` against non-json
files:

```
    -   id: check-json
        types: [file]  # override `types: [json]`
        files: \.(json|myext)$

```

Files can also be matched by shebang. With `types: python`, an `exe` starting
with `#!/usr/bin/env python3` will also be matched.

As with `files` and `exclude`, you can also exclude types if necessary using
`exclude_types`.

## Regular expressions [¶](#regular-expressions)

The patterns for `files` and `exclude` are python
[regular expressions](https://docs.python.org/3/library/re.html#regular-expression-syntax)
and are matched with [`re.search`](https://docs.python.org/3/library/re.html#re.search).

As such, you can use any of the features that python regexes support.

If you find that your regular expression is becoming unwieldy due to a long
list of excluded / included things, you may find a
[verbose](https://docs.python.org/3/library/re.html#re.VERBOSE) regular
expression useful. One can enable this with yaml's multiline literals and
the `(?x)` regex flag.

```
# ...
    -   id: my-hook
        exclude: |
            (?x)^(
                path/to/file1.py|
                path/to/file2.py|
                path/to/file3.py
            )$

```

## Overriding language version [¶](#overriding-language-version)

Sometimes you only want to run the hooks on a specific version of the
language. For each language, they default to using the system installed
language (So for example if I’m running `python3.7` and a hook specifies
`python`, pre-commit will run the hook using `python3.7`). Sometimes you
don’t want the default system installed version so you can override this on a
per-hook basis by setting the [`language_version`](#config-language_version).

```
-   repo: https://github.com/pre-commit/mirrors-scss-lint
    rev: v0.54.0
    hooks:
    -   id: scss-lint
        language_version: 2.1.5

```

This tells pre-commit to use ruby `2.1.5` to run the `scss-lint` hook.

Valid values for specific languages are listed below:

* python: Whatever system installed python interpreters you have. The value of
  this argument is passed as the `-p` to `virtualenv`.
  + on windows the
    [pep394](https://www.python.org/dev/peps/pep-0394/) name will be
    translated into a py launcher call for portability. So continue to use
    names like `python3` (`py -3`) or `python3.6` (`py -3.6`) even on
    windows.
* node: See [nodeenv](https://github.com/ekalinin/nodeenv#advanced).
* ruby: See [ruby-build](https://github.com/sstephenson/ruby-build/tree/master/share/ruby-build).
* rust: `language_version` is passed to `rustup`
* *new in 3.0.0* golang: use the versions on [go.dev/dl](https://go.dev/dl/) such as `1.19.5`

you can set [`default_language_version`](#top_level-default_language_version)
at the [top level](#pre-commit-configyaml---top-level) in your configuration to
control the default versions across all hooks of a language.

```
default_language_version:
    # force all unspecified python hooks to run python3
    python: python3
    # force all unspecified ruby hooks to run ruby 2.1.5
    ruby: 2.1.5

```

## badging your repository [¶](#badging-your-repository)

you can add a badge to your repository to show your contributors / users that
you use pre-commit!

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

* Markdown:

  ```
  [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

  ```
* HTML:

  ```
  <a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="pre-commit" style="max-width:100%;"></a>

  ```
* reStructuredText:

  ```
  .. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
     :target: https://github.com/pre-commit/pre-commit
     :alt: pre-commit

  ```
* AsciiDoc:

  ```
  image:https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit[pre-commit, link=https://github.com/pre-commit/pre-commit]

  ```

## Usage in continuous integration [¶](#usage-in-continuous-integration)

pre-commit can also be used as a tool for continuous integration. For
instance, adding `pre-commit run --all-files` as a CI step will ensure
everything stays in tip-top shape. To check only files which have changed,
which may be faster, use something like
`pre-commit run --from-ref origin/HEAD --to-ref HEAD`

## Managing CI Caches [¶](#managing-ci-caches)

`pre-commit` by default places its repository store in `~/.cache/pre-commit`
-- this can be configured in two ways:

* `PRE_COMMIT_HOME`: if set, pre-commit will use that location instead.
* `XDG_CACHE_HOME`: if set, pre-commit will use `$XDG_CACHE_HOME/pre-commit`
  following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).

### pre-commit.ci example [¶](#pre-commitci-example)

no additional configuration is needed to run in [pre-commit.ci](https://pre-commit.ci)!

pre-commit.ci also has the following benefits:

* it's faster than other free CI solutions
* it will autofix pull requests
* it will periodically autoupdate your configuration

[![pre-commit.ci speed comparison](https://raw.githubusercontent.com/pre-commit-ci-demo/demo/main/img/2020-12-15_noop.svg)](https://github.com/pre-commit-ci-demo/demo#results)

### appveyor example [¶](#appveyor-example)

```
cache:
- '%USERPROFILE%\.cache\pre-commit'

```

### azure pipelines example [¶](#azure-pipelines-example)

note: azure pipelines uses immutable caches so the python version and
`.pre-commit-config.yaml` hash must be included in the cache key. for a
repository template, see [[email protected]](https://github.com/asottile/azure-pipeline-templates/blob/main/job--pre-commit.yml).

```
jobs:
- job: precommit

  # ...

  variables:
    PRE_COMMIT_HOME: $(Pipeline.Workspace)/pre-commit-cache

  steps:

  # ...

  - script: echo "##vso[task.setvariable variable=PY]$(python -VV)"
  - task: CacheBeta@0
    inputs:
      key: pre-commit | .pre-commit-config.yaml | "$(PY)"
      path: $(PRE_COMMIT_HOME)

```

### circleci example [¶](#circleci-example)

like [azure pipelines](#azure-pipelines-example), circleci also uses immutable
caches:

```
  steps:
  - run:
    command: |
      cp .pre-commit-config.yaml pre-commit-cache-key.txt
      python --version --version >> pre-commit-cache-key.txt
  - restore_cache:
    keys:
    - v1-pc-cache-{{ checksum "pre-commit-cache-key.txt" }}

  # ...

  - save_cache:
    key: v1-pc-cache-{{ checksum "pre-commit-cache-key.txt" }}
    paths:
      - ~/.cache/pre-commit

```

(source: [@chriselion](https://github.com/Unity-Technologies/ml-agents/pull/3094/files#diff-1d37e48f9ceff6d8030570cd36286a61))

### github actions example [¶](#github-actions-example)

**see the [official pre-commit github action](https://github.com/pre-commit/action)**

like [azure pipelines](#azure-pipelines-example), github actions also uses
immutable caches:

```
    - name: set PY
      run: echo "PY=$(python -VV | sha256sum | cut -d' ' -f1)" >> $GITHUB_ENV
    - uses: actions/cache@v3
      with:
        path: ~/.cache/pre-commit
        key: pre-commit|${{ env.PY }}|${{ hashFiles('.pre-commit-config.yaml') }}

```

### gitlab CI example [¶](#gitlab-ci-example)

See the [Gitlab caching best practices](https://docs.gitlab.com/ee/ci/caching/#good-caching-practices) to fine tune the cache scope.

```
my_job:
  variables:
    PRE_COMMIT_HOME: ${CI_PROJECT_DIR}/.cache/pre-commit
  cache:
    paths:
      - ${PRE_COMMIT_HOME}

```

pre-commit's cache requires to be served from a constant location between the different builds. This isn't the default when using k8s runners
on GitLab. In case you face the error `InvalidManifestError`, set `builds_dir` to something static e.g `builds_dir = "/builds"` in your `[[runner]]` config

### travis-ci example [¶](#travis-ci-example)

```
cache:
  directories:
  - $HOME/.cache/pre-commit

```

## Usage with tox [¶](#usage-with-tox)

[tox](https://tox.readthedocs.io/) is useful for configuring test / CI tools
such as pre-commit. One feature of `tox>=2` is it will clear environment
variables such that tests are more reproducible. Under some conditions,
pre-commit requires a few environment variables and so they must be
allowed to be passed through.

When cloning repos over ssh (`repo: [[email protected]](/cdn-cgi/l/email-protection):...`), `git` requires the
`SSH_AUTH_SOCK` variable and will otherwise fail:

```
[INFO] Initializing environment for [email protected]:pre-commit/pre-commit-hooks.
An unexpected error has occurred: CalledProcessError: command: ('/usr/bin/git', 'fetch', 'origin', '--tags')
return code: 128
expected return code: 0
stdout: (none)
stderr:
    [email protected]: Permission denied (publickey).
    fatal: Could not read from remote repository.

    Please make sure you have the correct access rights
    and the repository exists.

Check the log at /home/asottile/.cache/pre-commit/pre-commit.log

```

Add the following to your tox testenv:

```
[testenv]
passenv = SSH_AUTH_SOCK

```

Likewise, when cloning repos over http / https
(`repo: https://github.com:...`), you might be working behind a corporate
http(s) proxy server, in which case `git` requires the `http_proxy`,
`https_proxy` and `no_proxy` variables to be set, or the clone may fail:

```
[testenv]
passenv = http_proxy https_proxy no_proxy

```

## Using the latest version for a repository [¶](#using-the-latest-version-for-a-repository)

`pre-commit` configuration aims to give a repeatable and fast experience and
therefore intentionally doesn't provide facilities for "unpinned latest
version" for hook repositories.

Instead, `pre-commit` provides tools to make it easy to upgrade to the
latest versions with [`pre-commit autoupdate`](#pre-commit-autoupdate). If
you need the absolute latest version of a hook (instead of the latest tagged
version), pass the `--bleeding-edge` parameter to `autoupdate`.

`pre-commit` assumes that the value of [`rev`](#repos-rev) is an immutable ref (such as a
tag or SHA) and will cache based on that. Using a branch name (or `HEAD`) for
the value of [`rev`](#repos-rev) is not supported and will only represent the state of
that mutable ref at the time of hook installation (and will *NOT* update
automatically).

# Contributing [¶](#contributing)

We’re looking to grow the project and get more contributors especially to
support more languages/versions. We’d also like to get the
.pre-commit-hooks.yaml files added to popular linters without maintaining
forks / mirrors.

Feel free to submit bug reports, pull requests, and feature requests.

## Sponsoring [¶](#sponsoring)

If you or your company would like to support the development of pre-commit one
can contribute in the following ways:

* [GitHub Sponsors (asottile)](https://github.com/sponsors/asottile)
* [Open Collective](https://opencollective.com/pre-commit)

## Getting help [¶](#getting-help)

There are several ways to get help for pre-commit:

* Ask a question on [stackoverflow tagged `pre-commit.com`](https://stackoverflow.com/questions/tagged/pre-commit.com)
* Create an issue on [pre-commit/pre-commit](https://github.com/pre-commit/pre-commit/issues/)
* Ask in the #pre-commit channel in [asottile's twitch discord](https://discord.gg/xDKGPaW)

## Contributors [¶](#contributors)

* website by [Molly Finkle](https://github.com/mfnkl)
* created by [Anthony Sottile](https://github.com/asottile)
* core developers: [Ken Struys](https://github.com/struys),
  [Chris Kuehl](https://github.com/chriskuehl)
* [framework contributors](https://github.com/pre-commit/pre-commit/graphs/contributors)
* [core hook contributors](https://github.com/pre-commit/pre-commit-hooks/graphs/contributors)
* and users like you!
