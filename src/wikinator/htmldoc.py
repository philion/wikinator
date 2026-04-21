import sys
from typing import override

import requests

from bs4 import BeautifulSoup

from markdownify import markdownify as md

import re
from collections import defaultdict
import logging
from datetime import datetime
from abc import ABC, abstractmethod

from urllib.parse import urlsplit

from wikinator.page import Page

log = logging.getLogger(__name__)

def download_html(url):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    cookies = dict(cookies_are='working')
    response = session.get(url, cookies=cookies)

    if response.status_code != 200:
        log.error(f"failed to download {url}, status code: {response.status_code}")
    #    raise Exception(f"failed to download {url}, status code: {response.status_code}")
    return response.text


def make_md_anchor(text, counter):
    text = text.lower()
    text = re.sub(r"[^\w]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")

    count = counter[text]
    counter[text] += 1
    if count > 0:
        text = f"{text}-{count}"
    return f"#{text}"


def dl_to_ul(dl_tag, anchor_map, anchor_counter, text_counter):
    ul = BeautifulSoup("<ul></ul>", "lxml").ul

    for child in dl_tag.children:
        if child.name != "dt":
            continue

        li = BeautifulSoup("<li></li>", "lxml").li
        a_tag = child.find("a")

        if a_tag:
            href = a_tag.get("href", "")
            text = a_tag.get_text(strip=True)
            if href.startswith("#"):
                orig_anchor = href[1:]
                if orig_anchor in anchor_map:
                    md_anchor = anchor_map[orig_anchor]
                else:
                    md_anchor = make_md_anchor(text, text_counter)
                    anchor_map[orig_anchor] = md_anchor
                li.append(f"[{text}]({md_anchor})")
            else:
                li.append(text)
        else:
            text = child.get_text(strip=True)
            md_anchor = make_md_anchor(text, text_counter)
            li.append(f"[{text}]({md_anchor})")

        next_sib = child.next_sibling
        while next_sib and not getattr(next_sib, "name", None):
            next_sib = next_sib.next_sibling

        if next_sib and next_sib.name == "dd":
            inner_dl = next_sib.find("dl")
            if inner_dl:
                li.append(dl_to_ul(inner_dl, anchor_map, anchor_counter, text_counter))

        ul.append(li)

    return ul


def preprocess_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    anchor_map = {}
    text_counter = defaultdict(int)

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for header in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
        a_tag = header.find("a", attrs={"name": True})
        header_text = header.get_text(strip=True)

        if a_tag:
            orig_anchor = a_tag["name"]
            md_anchor = make_md_anchor(header_text, text_counter)
            anchor_map[orig_anchor] = md_anchor
            a_tag.decompose()

    for dl in list(soup.find_all("dl")):
        dl.replace_with(dl_to_ul(dl, anchor_map, text_counter, text_counter))

    return soup.prettify()


def get_title_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('title')[0].get_text()


def html_to_markdown(html):
    return md(
        html,
        heading_style="ATX",
        bullets="*"
    )


def convert_to_markdown(url):
    # TODO Download URL, get mimetype from response or file contents, process based on that
    # Seperate download from processing
    # download should include filetype
    html = download_html(url)
    html = preprocess_html(html)
    markdown = html_to_markdown(html)
    markdown = markdown.replace("\u00A0", " ")
    return markdown


# document - the specific page. maps to page eventually
# has: url, type, content (maybe other metadata)
# request document:
# 1. download - special library (google)
# 2. check mimetype - select converter
# 3. convert and save based on metadata and config
# - /Documents/server.name/server/path/doc-name.md
# MD metadata with:
# - original URL
# - download date

def get_url(url:str):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    cookies = dict(cookies_are='working')
    response = session.get(url, cookies=cookies)

    if response.status_code != 200:
        log.error(f"failed to download {url}, status code: {response.status_code}")
    #    raise Exception(f"failed to download {url}, status code: {response.status_code}")

    return response


def path_from_url(full_url:str):
    # server/
    url = urlsplit(full_url)
    return f"{url.hostname}/{url.path}"


class Document:
    def __init__(self, url:str, type:str, content:bytes, title:str=None):
        self.url = url
        self.created = datetime.now()
        self.type = type
        self.title = title
        self.content = content


def get_document(url:str) -> Document:
    response = get_url(url)
    content_type_header = requests.utils._parse_content_type_header(response.headers['Content-Type'])
    content_type = content_type_header[0] # ('text/html', {'charset': 'UTF-8'})
    return Document(response.url, content_type, response.content)


class DocumentConverter(ABC):
    @abstractmethod
    def convert(self, doc:Document) -> Page:
        pass


class HtmlConverter(DocumentConverter):
    @override
    def convert(self, doc:Document) -> Page:
        title = get_title_from_html(doc.content)
        path = path_from_url(doc.url)

        content = preprocess_html(doc.content)
        markdown = html_to_markdown(content)
        markdown = markdown.replace("\u00A0", " ")

        return Page.load({
            'content': markdown,
            'path': path,
            'title': title,
        })


class PassthruConverter(DocumentConverter):
    @override
    def convert(self, doc:Document) -> Page:
        return Page.load({
            'content': doc.content,
            'path': path_from_url(doc.url),
            'title': doc.title,
        })


class DocxConverter(DocumentConverter):
    @override
    def convert(self, doc:Document) -> Page:
        # TODO use Docxit
        pass


class FolderConverter(DocumentConverter):
    @override
    def convert(self, doc:Document) -> Page:
        ## What? how many pages -> 1?
        # always return array? images, etc? PageSet?
        pass


default_converter = PassthruConverter()

converters = {
    'text/html': HtmlConverter(),
    'text/markdown': default_converter,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DocxConverter(),
    'application/vnd.google-apps.document': DocxConverter(),
    'application/vnd.google-apps.folder': FolderConverter(),
    # PDF - extract text and ocr, render page images?
    # CSV - MD tables? keep both
}


def get_page(url:str) -> Page:
    doc = get_document(url)
    converter = converters.get(doc.type, default_converter)
    log.warning(f"selected {type(converter)} for {doc.type}")
    return converter.convert(doc)


def main():
    logging.basicConfig(level=logging.DEBUG)

    url = sys.argv[1]
    #markdown = convert_to_markdown(url)
    #doc = get_document(url)
    doc = get_page(url)
    print(doc.title, doc.path)
    #print(doc.content)


if __name__ == "__main__":
    main()