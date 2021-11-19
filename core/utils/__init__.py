from prosemirror.model import Schema

P_DOM = ["p", 0]
BLOCKQUOTE_DOM = ["blockquote", 0]
BR_DOM = ["br"]
OL_DOM = ["ol", 0]
UL_DOM = ["ul", 0]
LI_DOM = ["li", 0]

nodes = {
    "doc": {"content": "block+"},
    "paragraph": {
        "content": "inline*",
        "group": "block",
        "parseDOM": [{"tag": "p"}],
        "toDOM": lambda _: P_DOM,
    },
    "blockquote": {
        "content": "block+",
        "group": "block",
        "defining": True,
        "parseDOM": [{"tag": "blockquote"}],
        "toDOM": lambda _: BLOCKQUOTE_DOM,
    },
    "heading": {
        "attrs": {"level": {"default": 2}},
        "content": "inline*",
        "group": "block",
        "defining": True,
        "parseDOM": [
            {"tag": "h1", "attrs": {"level": 2}},
            {"tag": "h2", "attrs": {"level": 2}},
            {"tag": "h3", "attrs": {"level": 3}},
            {"tag": "h4", "attrs": {"level": 4}},
            {"tag": "h5", "attrs": {"level": 5}},
            {"tag": "h6", "attrs": {"level": 5}},
        ],
        "toDOM": lambda node: [f"h{node.attrs['level']}", 0],
    },
    "text": {"group": "inline"},
    "image": {
        "inline": True,
        "attrs": {
            "src": {},
            "alt": {"default": None},
            "title": {"default": None},
            "size": {"default": None},
            "caption": {"default": None}
        },
        "group": "inline",
        "draggable": True,
        "parseDOM": [{"tag": "img[src]"}],
        "toDOM": lambda node: [
            "img",
            {
                "src": node.attrs["src"],
                "alt": node.attrs["alt"],
                "title": node.attrs["title"],
            },
        ],
    },
    "figure": {
        "inline": False,
        "attrs": {
            "src": {},
            "alt": {"default": None},
            "title": {"default": None},
            "size": {"default": None},
            "caption": {"default": None}
        },
        "group": "block",
        "draggable": False,
        "parseDOM": [{"tag": "figure"}],
        "toDOM": lambda node: [
            # TODO: build figure view
            "img",
            {
                "src": node.attrs["src"],
                "alt": node.attrs["alt"],
                "title": node.attrs["title"],
            },
        ],
    },
    "file": {
        "inline": False,
        "attrs": {
            "url": {"default": None},
            "mimeType": {"default": None},
            "name": {"default": None},
            "size": {"default": None}
        },
        "group": "block",
        "draggable": False,
        "parseDOM": [],
        "toDOM": lambda node: [
            # TODO: build file view
            "a",
            {
                "href": node.attrs["url"],
                "alt": node.attrs["alt"],
                "title": node.attrs["title"],
            },
            0
        ],
    },
    "video": {
        "inline": False,
        "attrs": {
            "guid": {"default": None},
            "platform": {"default": None},
            "title": {"default": None}
        },
        "group": "block",
        "draggable": False,
        "parseDOM": [{"tag", "iframe"}],
        "toDOM": lambda node: [
            # TODO: build video view
            "iframe",
            {
                "src": node.attrs["platform"],
            }
        ],
    },
    "hardBreak": {
        "inline": True,
        "group": "inline",
        "selectable": False,
        "parseDOM": [{"tag": "br"}],
        "toDOM": lambda _: BR_DOM,
    },
    "bulletList": {
        "group": "block",
        "content": "listItem+",
        "parseDom": [{"tag": "ul"}],
        "toDOM": lambda _: UL_DOM
    },
    "orderedList": {
        "attrs": {"order": {"default": 1}},
        "group": "block",
        "content": "listItem+",
        "parseDom": [{"tag": "ol"}],
        "toDOM": lambda node: (
            OL_DOM if node.attrs.get("order") == 1 else ["ol", {"start": node.attrs["order"]}, 0]
        ),
    },
    "listItem": {
        "parseDOM": [{"tag": "li"}],
        "defining": True,
        "content": "paragraph block*",
        "toDOM": lambda _: LI_DOM
    },
}

ITALIC_DOM = ["em", 0]
BOLD_DOM = ["strong", 0]
UNDERLINE_DOM = ["u", 0]

marks = {
    "link": {
        "attrs": {"href": {}, "title": {"default": None}, "target": {"default": None}},
        "inclusive": False,
        "parseDOM": [{"tag": "a[href]"}],
        "toDOM": lambda node, _: [
            "a",
            {"href": node.attrs["href"], "title": node.attrs["title"], "target": node.attrs["target"]},
            0,
        ],
    },
    "italic": {
        "parseDOM": [{"tag": "i"}, {"tag": "em"}],
        "toDOM": lambda _, __: ITALIC_DOM,
    },
    "bold": {
        "parseDOM": [{"tag": "strong"}, {"tag": "b"}],
        "toDOM": lambda _, __: BOLD_DOM,
    },
    "underline": {"parseDOM": [{"tag": "u"}], "toDOM": lambda _, __: UNDERLINE_DOM},
}


tiptap_schema = Schema({"nodes": nodes, "marks": marks})