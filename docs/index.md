# BadaBoom

Library that parse and retrieve the 'Asteroids - NeoWs' database and fireballs database from NASA.
It also provides simple programs to compute figures and statistical information.
Database are provided by NASA, more information is available [here](https://api.nasa.gov/).

In this work, the focus is to better understand/visualize the events from out of the earth.

## Installation

The following repository use poetry to handle its dependencies, to install badaboom you can type the following:

```bash
poetry install
```

### Dev

This project uses precommits, to enable them:

```bash
poetry run pre-commit install
```

## Usage and example

Examples are available with `compute_*_statistics` python scripts. Theses examples compute some plots and statistics. If you need help with it, you can type:

```bash
python compute_asteroids_statistics.py --help
python compute_fireballs_statistics.py --help
```

More explanations are available on my Blog:

- [surrounding asteroids.](https://website.vincent-roger.fr/blog/dataviz/2021/09/12/badaboom.html)
- [fireballs.](https://website.vincent-roger.fr/blog/dataviz/2021/12/15/badaboom_fireball.html)
