# Redgifs Scraper

Downloads gifs from redgifs, using python asyncio

## Usage

```
usage: redgifs.py [-h] [--count COUNT] [--order ORDER] [--parallel PARALLEL] [--dir DIR] category

positional arguments:
  category

options:
  -h, --help           show this help message and exit
  --count COUNT        number of gifs to download
  --order ORDER        'trending', 'top7', 'top28', 'best', 'latest', 'oldest'
  --parallel PARALLEL  number of parallel downloads
  --dir DIR            directory to download to
```

## Dependencies


```
pip install tqdm aiohttp
```
