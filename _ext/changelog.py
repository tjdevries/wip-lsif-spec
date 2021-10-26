from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx import addnodes


class Changelog(Directive):
    has_content = True
    required_arguments = 1

    def run(self):
        paragraph_node = nodes.paragraph(text="Hello World!" + str(self.content))
        return [
            paragraph_node,
            addnodes.literal_emphasis(text=self.content[0]),
            addnodes.literal_strong(text=self.arguments[0]),
        ]


def setup(app):
    app.add_directive("changelog", Changelog)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
