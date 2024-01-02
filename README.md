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
