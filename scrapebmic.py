#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import attr
import csv
import sys
import argparse

DEFAULT_URL = 'https://www.nlm.nih.gov/NIHbmic/nih_data_sharing_repositories.html'

COLUMN_NAMES = [
    'ico',
    'name',
    'desc',
    'submissions',
    'access',
    'current_nih_funding',
    'open_data_access',
    'open_time_frame',
    'sustained_support',
]

COLUMN_NAME_LINK = {
    'name': 'link',
    'submissions': 'submissions_link',
    'access': 'access_link',
}


@attr.s(frozen=True)
class Repository(object):
    ico = attr.ib()
    name = attr.ib()
    desc = attr.ib(repr=False)
    submissions = attr.ib(repr=False)
    access = attr.ib(repr=False)
    current_nih_funding = attr.ib(repr=False)
    open_data_access = attr.ib(repr=False)
    open_time_frame = attr.ib(repr=False)
    sustained_support = attr.ib(repr=False)

    link = attr.ib(repr=False, default=None)
    access_link = attr.ib(repr=False, default=None)
    submissions_link = attr.ib(repr=False, default=None)

    @classmethod
    def fields(cls):
        return list(attr.name for attr in cls.__attrs_attrs__)


def row_to_repo(row):
    cols = row.select('td')
    assert len(cols) >= 10

    repo_kwargs = {}
    for col_name, col_element in zip(COLUMN_NAMES, cols[:10]):
        links = col_element.select('a')
        link_name = COLUMN_NAME_LINK.get(col_name, None)
        if link_name and len(links) > 0:
            link = links[0]
            repo_kwargs[col_name] = link.text.strip()
            repo_kwargs[link_name] = link.attrs['href']
        else:
            repo_kwargs[col_name] = col_element.text.strip()
    return Repository(**repo_kwargs)


def scrape_bmic(url=DEFAULT_URL, session=None):
    if session is None:
        session = requests.Session()
    r = session.get(url)

    content_type_parts = [elem.strip() for elem in r.headers['Content-Type'].split(';')]
    content_type = content_type_parts[0]
    content_type_hints = dict(v.split('=', 2) for v in content_type_parts[1:])

    # Get the encoding from the content_type
    encoding = content_type_hints.get('charset', 'utf-8')

    assert content_type == 'text/html'

    soup = BeautifulSoup(r.content, 'lxml', from_encoding=encoding)
    rows = soup.select('table#example tr')
    repos = [row_to_repo(row) for row in rows[1:]]
    return repos


def output_repos(repos, fp=None):
    if not fp:
        fp = sys.stdout
    writer = csv.writer(fp, dialect='unix', quoting=csv.QUOTE_MINIMAL)
    repo_fields = Repository.fields()
    writer.writerow(repo_fields)
    for repo in repos:
        row = [getattr(repo, field, '') for field in repo_fields]
        writer.writerow(row)


def parse_args(prog, args):
    parser = argparse.ArgumentParser(prog=prog, description='Basic scraper for NIH Data Sharing Repositories')
    parser.add_argument('--output', metavar='PATH', default=None,
                        help='Specify where to save the results')
    parser.add_argument('--url', metavar='URL', default=DEFAULT_URL,
                        help='Which url to crawl')
    return parser.parse_args(args)


def main():
    opts = parse_args(sys.argv[0], sys.argv[1:])
    repos = scrape_bmic(opts.url)
    if opts.output:
        with open(opts.output, 'w', encoding='utf-8') as fp:
            output_repos(repos, fp)
    else:
        output_repos(repos, sys.stdout)


if __name__ == '__main__':
    main()
