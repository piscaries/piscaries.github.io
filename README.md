# piscaries.github.io

Personal blog of Haifeng Zhao, served by GitHub Pages from `docs/`.

- Write posts in `src/posts/YYYY-MM-DD-slug.md` (front matter: `title`, `description`, optional `original`, `repo`, `image`); images go in `src/images/<slug>/`.
- Build with `python3 build.py` (needs pandoc). It regenerates `docs/`.
- Preview with `python3 -m http.server --directory docs`.
