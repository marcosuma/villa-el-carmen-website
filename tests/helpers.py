from html.parser import HTMLParser


class PageParser(HTMLParser):
    """Collects the bits of a rendered page that the SEO tests care about."""

    def __init__(self) -> None:
        super().__init__()
        self.html_lang = None
        self.title = ""
        self.meta: dict[str, str] = {}
        self.links: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self.assets: list[str] = []
        self.h1_count = 0
        self.json_ld: list[str] = []
        self._in_title = False
        self._in_json_ld = False

    def handle_starttag(self, tag, attrs):
        attributes = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = attributes.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attributes.get("name") or attributes.get("property")
            if key:
                self.meta[key] = attributes.get("content", "")
        elif tag == "link":
            self.links.append(attributes)
            if attributes.get("rel") in ("stylesheet", "icon", "preload", "apple-touch-icon"):
                self.assets.append(attributes["href"])
        elif tag == "a":
            self.anchors.append(attributes)
        elif tag == "h1":
            self.h1_count += 1
        elif tag in ("img", "source", "script", "video"):
            for key in ("src", "poster"):
                if attributes.get(key):
                    self.assets.append(attributes[key])
            for candidate in attributes.get("srcset", "").split(","):
                if candidate.strip():
                    self.assets.append(candidate.strip().split(" ")[0])
            if attributes.get("data-full"):
                self.assets.append(attributes["data-full"])
            if tag == "script" and attributes.get("type") == "application/ld+json":
                self._in_json_ld = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_json_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_json_ld:
            self.json_ld.append(data)


def parse(html: str) -> PageParser:
    parser = PageParser()
    parser.feed(html)
    return parser
