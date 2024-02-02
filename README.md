tooi
====

tooi is a text-based user interfaces for Mastodon, Pleroma and friends. The name
is a portmantou of [toot](https://toot.bezdomni.net/) and
[TUI](https://en.wikipedia.org/wiki/Text-based_user_interface).

It uses the [Textual framework](https://textual.textualize.io/).

* Source code: https://github.com/ihabunek/tooi
* Python package: https://pypi.org/project/toot-tooi/
* IRC chat: #toot channel on libera.chat

NB: Coud not get `tooi` as Python project name, if someone knows python people
ask them kindly to approve
[this request](https://github.com/pypi/support/issues/3097).

## Project status

**This project is in its early days and things _will_ change without notice.**

While we aim to keep the project usable at all times, expect that things may
break before we hit version 1.0.

## Installation

Currently tooi requires [toot](https://github.com/ihabunek/toot/) for logging
into instances.

The recommended method of installation is using [pipx](https://pipx.pypa.io/stable/) which installs python projects into their own virtual environments.

1. Follow the [pipx installation guide](https://pipx.pypa.io/stable/installation/)
   to set it up.

2. Install toot and tooi by running:
   ```
   pipx install toot
   pipx install toot-tooi
   ```

Alternatively, if you know what you're doing, install both projects from pypi
using your favourite method.

## Usage

Before first use, run `toot login` to log into your mastodon instance.

Tooi will authenticate as the currently active `toot` user. You can check who
you're logged in as by running `toot whoami`, and switch accounts using `toot
activate`.

Launch the program by running `tooi`.

Run `tooi --help` to see the available commandline options.

## Key bindings

Generic bindings:

* Arrow keys or `h`/`j`/`k`/`l` - move up/down/left/right
* `Tab` and `Shift+Tab` - move between focusable components
* `Space` or `Enter` - activate buttons and menu items

Managing tabs:

* `.` - refresh timeline
* `/` - open search tab
* `1` - `9` - switch between open tabs
* `Ctrl+d` - close current tab
* `g` - open new tab ("goto")

Status bindings:

* `a` - show account
* `b` - boost status
* `d` - delete status
* `e` - edit status
* `f` - favourite status
* `m` - show media
* `r` - reply to status
* `s` - reveal sensitive
* `t` - show thread
* `u` - show toot source

## Setting up a dev environment

Check out tooi and install in a virtual environment:

```
git clone https://github.com/ihabunek/tooi.git
cd tooi
python3 -m venv _env
source _env/bin/activate
pip install --editable ".[dev]"
```

Run the app by invoking `tooi`.

To use the
[Textual console](https://textual.textualize.io/guide/devtools/#console), run
it in a separate terminal window:

```
textual console
```

Then run tooi like this:

```
textual run --dev tooi.cli:main
```

## Code style and linting

Rule of thumb: look at existing code, try to keep it similar in style.

Please run `make lint` to check formatting before sending a patch. This runs
flake8 which checks for some basic code style rules. It shouldn't be too
aggressive, and if you're bothered by a rule, let me know.

Lines can be upto 100 characters wide, wrap them if they go over that.

### Wrapping style

Wrapping style is not enforced by the linter, but this is the preferred style
most of the time:

```python
# NO: Do not wrap after opening paren

very_long_package_name.even_longer_long_function_call(first_argument,
                                                      second_argument,
                                                      third_argument)

# YES: Align arguments on next tab

very_long_package_name.even_longer_long_function_call(
    first_argument,
    second_argument,
    third_argument
)
```

## Type checking

You're encouraged to specify types in your code. While they can be a bit of a
pain in Python, I have found them to be useful in locating errors and
eliminating potential bugs.

This project is configured to use
[pyright](https://github.com/microsoft/pyright) for type checking, and I
recommend that you install the pyright language server if it's available for
your editor. Currently it returns errors in some places, some of which are
caused by the way textual is implemented. So it's not required to have zero
errors before submitting patches, but it will indicate problems in new code.
