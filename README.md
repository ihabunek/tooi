tooi
====

tooi is a text-based user interfaces for Mastodon, Pleroma and friends. The name
is a portmantou of [toot](https://toot.bezdomni.net/) and
[TUI](https://en.wikipedia.org/wiki/Text-based_user_interface).

It uses the [Textual framework](https://textual.textualize.io/).

This project is in its early days and not feature complete.

* Source code: https://git.sr.ht/~ihabunek/tooi
* Mailing list: https://lists.sr.ht/~ihabunek/toot-discuss
* IRC chat: #toot channel on libera.chat

## Setting up a dev environment

Check out tooi and install in a virtual environment:

```
git clone https://git.sr.ht/~ihabunek/tooi
cd toot
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
