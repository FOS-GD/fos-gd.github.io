# fos-gd.github.io

A small static website built from Markdown with a single Python script (`build.py`), using [pixi](https://pixi.sh) to manage the dependencies.

## Usage

```sh
pixi run serve   # preview at http://localhost:8000, rebuilds automatically when files change
pixi run build   # build the site into site/
```

## Editing content

- Pages live in `docs/` as `.md` files. Each file becomes a page and gets a menu entry automatically.
- Subfolders work too: `docs/projects/foo.md` becomes `/projects/foo.html`.
- Link to other pages by their `.md` filename (`[About](about.md)`). The build rewrites these links to `.html`.
- Images and other files placed in `docs/` are copied to the site as-is.
- Optional front matter at the top of a page:

  ```yaml
  ---
  title: About        # menu/page title (defaults to the file name)
  nav_order: 10       # menu position (lower comes first; Home is 0)
  hidden: true        # leave the page out of the menu
  description: ...    # <meta name="description">
  ---
  ```

- Site name and description are in `config.yml`, the layout is in `templates/base.html`, and the styling is in `static/style.css`.

## Deployment

Every push to `main` builds the site and deploys it via `.github/workflows/pages.yml`.
Pull requests are only built, as a check.
One-time setup: in the repository on GitHub, go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions**.

## Credits

- Pixel art components: [NES.css](https://nostalgic-css.github.io/NES.css/) v2.3.0 by B.C.Rikko and contributors, MIT License (stored in `static/vendor/nes.css/` with its license).
  `build.py` adds the NES.css classes to the generated HTML, and `static/style.css` recolors it to the site palette.
- Fonts: [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) by CodeMan38 and [VT323](https://fonts.google.com/specimen/VT323) by Peter Hull, both under the SIL Open Font License 1.1 (license texts in `static/fonts/`).
  They are hosted in this repository, so visitors don't connect to Google Fonts.
- Built with [Python-Markdown](https://github.com/Python-Markdown/markdown), [Jinja2](https://github.com/pallets/jinja) and [PyYAML](https://github.com/yaml/pyyaml).

## AI assistance

The site setup (`build.py`, the template, the stylesheet, the pixi configuration and the GitHub Actions workflow) was written with help from [Claude Code](https://claude.com/claude-code), Anthropic's AI coding assistant, and reviewed by the maintainers.
The website content in `docs/` is written by the maintainers.
