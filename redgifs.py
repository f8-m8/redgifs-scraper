import asyncio
import argparse
from tqdm.asyncio import tqdm_asyncio
import logging
import os
from typing import Literal

from aiohttp import BaseConnector, ClientSession

HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"101\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "x-customheader": "https://www.redgifs.com/browse",
    "referrer": "https://www.redgifs.com/",
    "referrerPolicy": "strict-origin-when-cross-origin",
}


class RedGifs:
    urls: set[str]
    client: ClientSession
    dir_name: str
    sem: asyncio.Semaphore
    logger: logging.Logger
    
    def __init__(self, client: ClientSession,
                       parallel_connections: int,
                       *, dir_name: str = '.'
                       ) -> None:
        self.sem = asyncio.Semaphore(parallel_connections)
        self.client = client
        self.dir_name = dir_name

        self.logger = logging.getLogger('redgifs')
        os.makedirs(dir_name, exist_ok=True)
        self.urls = set()

    async def get_links(self,
            category: str,
            order: Literal['trending', 'top7', 'top28', 'best', 'latest', 'oldest'] = 'trending',
            count: int = 80):
        """
        Collects urls to be downloaded
        """
        url = 'https://api.redgifs.com/v2/gifs/search'
        params = {
            'search_text': category,
            'order': order,
            'count': count
        }

        async with self.client.get(url, params=params, headers=HEADERS) as resp:
            data = await resp.json()

        new_urls = [gif['urls']['hd'] for gif in data['gifs']]
        self.urls.update(new_urls)
        self.logger.info(f'Got {len(new_urls)} urls for category: {category}. Total[{len(self.urls)}]')

    async def download_clip(self, url: str):
        filename = url.split('/')[-1]
        path = os.path.join(self.dir_name, filename)

        if os.path.exists(path):
            return

        async with (self.sem, self.client.get(url, headers=HEADERS) as resp):
            with open(path, 'wb') as f:
                f.write(await resp.read())
    
    async def download_links(self) -> None:
        await tqdm_asyncio.gather(
            *[self.download_clip(url) for url in self.urls],
            total=len(self.urls)
        )


async def download_gifs(
        category: str,
        count: int = 50,
        order: Literal['trending', 'top7', 'top28', 'best', 'latest', 'oldest'] = 'trending',
        dir_name: str = '.',
        parallel_cons: int = 15) -> None:
    async with ClientSession() as client:
        rg = RedGifs(client, parallel_cons, dir_name=dir_name)
        await rg.get_links(category=category, count=count, order=order)
        await rg.download_links()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser('redgifs.py')
    parser.add_argument('category')
    parser.add_argument(
        '--count', type=int,
        help="number of gifs to download",
        default=50)
    parser.add_argument(
        '--order', type=str,
        help="'trending', 'top7', 'top28', 'best', 'latest', 'oldest'",
        default='trending')
    parser.add_argument(
        '--parallel', type=int,
        help="number of parallel downloads",
        default=15)
    parser.add_argument(
        '--dir', type=str,
        help="directory to download to",
        default='.')
    args = parser.parse_args()

    if args.order not in ['trending', 'top7', 'top28', 'best', 'latest', 'oldest']:
        raise ValueError('Invalid category')

    asyncio.run(
        download_gifs(
            args.category, args.count,
            args.order, args.dir, args.parallel
        )
    )