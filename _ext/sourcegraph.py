from os import environ

from docutils import nodes
from docutils.parsers.rst import Directive


def should_emit() -> bool:
    return environ.get("EMIT_SOURCEGRAPH") != "false"


class SourcegraphImplementation(Directive):
    has_content = True

    def run(self):
        if not should_emit():
            return []

        return [
            nodes.paragraph(text="SourcegraphImplementation:"),
            nodes.paragraph(text=self.content),
            # More?
        ]


class SourcegraphNote(Directive):
    has_content = True

    def run(self):
        if not should_emit():
            return []

        return [
            nodes.paragraph(text="SourcegraphNote:"),
            nodes.paragraph(text=self.content),
            # More?
        ]


def setup(app):
    app.add_directive("sourcegraph_implementation", SourcegraphImplementation)
    app.add_directive("sourcegraph_note", SourcegraphNote)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
