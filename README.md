PS5 Stock Checker

> Let me know when the [Independent's PS5 Live Stock tracker blog](https://www.independent.co.uk/extras/indybest/gadgets-tech/video-games-consoles/ps5-console-uk-restock-news-latest-b2012447.html#post-556368) has a new post, so I can hopefully get a PS5!

## Installation

```sh
poetry install
```

## Usage:

### Configuration

The utility expects a file at `./pushover.conf` that follows the form defined by [Laprice's pushover library](https://github.com/laprice/pushover/blob/master/example.pushover)

### Run

```sh
poetry run check.py
```

I've added it to my crontab:

```
@hourly /<path>/<to>/python /<path>/<to>/ps5-stock/check.py >> /<path>/<to>/ps5-stock/output.log
```
