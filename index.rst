..
    TODO: explain relaxed constraints

.. lsif documentation master file, created by
   sphinx-quickstart on Mon Oct 18 12:13:31 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. highlight:: none

.. role:: js_keyword
.. role:: js_string

.. raw:: html

   <script src="_static/sourcegraph.js"></script>

Language Server Index Format
================================

This document outlines the data structures and relationships of the Language Server Index Format.

.. sourcegraph_note::

   Whenever you see a section denoted like this, it will give Sourcegraph specific information.

   This is generally to let the reader know what Sourcegraph expects to ingest.

This format is based off of v0.5.0 of Microsoft's `LSIF specification`_ and
includes several backwards-compatible extensions (noted specifically below).
Periodically, we will refresh our specification to include changes in
Microsoft's specification in order to maintain the following design invariant:

.. sourcegraph_note::

   An LSIF indexer built following Microsoft's specification should be ingestible
   by Sourcegraph, though it may be missing data required to power certain
   Sourcegraph-specific features, such as generation of API documentation.

Data model
----------

An LSIF index encodes a directed graph of vertices connected by edges. :ref:`Vertices <vertices>`
encode objects and facts about objects within a project (such as source text
locations and diagnostics). :ref:`Edges <edges>` encode relationships between these objects
(such as linking references of a symbol to its definition).

Every vertex and edge within an index are enveloped by the following type.

.. _element:

.. parsed-literal::

   export interface Element {
       :js:attr:`id <Element.id>`: :ref:`ID <element-id>`
       :js:attr:`type <Element.type>`: 'vertex' | 'edge'
       :js:attr:`label <Element.label>`: string
   }

.. _element-id:

.. js:attribute:: Element.id

    .. parsed-literal::

        type ID = string | int


    The `ID` field uniquely defines an element within an index and is used by edges
    to refer to its incident vertices.

    An element identifier can be either a string or an integer.
    It is not recommended to mix types within the same index.

.. js:attribute:: Element.type

   Identifies an element as either a vertex or an edge.

   Only valid values are ``"vertex"`` or ``"edge"``


.. js:attribute:: Element.label

   Further identifies an element as a particular subtype of a vertex or an
   edge. Subtypes of vertices and edges may define additional fields. Thus, an
   element is in practice a tagged union and the value of the ``label`` field
   determines how to interpret the element payload.


.. _edges:

Edges
-----

.. _inv:
.. _outv:

Edges can be classified into two distinct groups: single-target and
multi-target edges. For an edge ``x -> y``, we refer to ``x`` as the ``OutV``
and ``y`` as the ``InV``.

.. _invs:

Single-target edges (1-to-1 edges) will have a single ``InV``
value, and multiple-target edges (1-to-n edges) will have one or more ``InVs``
values. 


Edges are encoded by the following type. Some edges may contain additional
fields, depending on the label type. Certain subtypes of 1-to-n edges may also
attribute meaning to the order of their `InVs` list.


.. _edge-1:

.. parsed-literal::

    interface Edge1to1 extends Element {
        :js:attr:`type <Element.type>`: 'edge'
        :ref:`outV <outV>`: :ref:`ID <element-id>`
        :ref:`inV <inV>`: :ref:`ID <element-id>`
    }


.. _edge-n:

.. parsed-literal::

    interface Edge1toN extends Element {
        :js:attr:`type <Element.type>`: 'edge'
        :ref:`outV <outV>`: :ref:`ID <element-id>`
        :ref:`inVs <inVs>`: :ref:`ID[] <element-id>`
    }


.. _vertices:

Vertices
--------

Unlike edges, there are no additional fields common to all vertex types. Thus, vertices are enveloped by the following type.

.. _vertex:
.. parsed-literal::

    interface Vertex extends :ref:`Element <element>` {
        :js:attr:`type <Element.type>`: 'vertex'
    }

Specific subtypes of vertices and edges are detailed in the following.

.. _vertex-metadata:

Vertex: Metadata
^^^^^^^^^^^^^^^^

Every index must emit a single metadata vertex that is unattached to any other
element in the index. This vertex is used for bookkeeping information
bookkeeping information such as protocol version and the root URI of all
documents within the index.

Because this vertex dictates how the rest of the index is interpreted, it must
be able to be extracted without reading the entire index. See the
:ref:`Data Schemas <data-schemas>` section below for specific constraints as this is
a format dependent concern.

The metadata vertex is encoded by the following type.

.. _metadata:
.. parsed-literal::

    interface MetaData extends :ref:`Vertex <vertex>` {
        :js:attr:`label <Element.label>`: 'metaData'
        :js:attr:`version <Metadata.version>`: string
        :js:attr:`projectRoot <Metadata.projectRoot>`: string
        :js:attr:`toolInfo <Metadata.toolInfo>`?: :ref:`ToolInfo <ToolInfo>`
    }

.. js:attribute:: Metadata.version

    Indicates the version of the protocol used to generate the index.

.. js:attribute:: Metadata.projectRoot

    Indicates the absolute path of the file tree being indexed as a URI (e.g.
    ``file:///home/user/dev/repo/subproject``). This value is used only to
    determine paths for text documents relative to the project root and the
    shared path prefix is not used in any meaningful way once uploaded.

.. js:attribute:: Metadata.toolInfo

    .. _toolinfo:
    .. parsed-literal::

        interface ToolInfo {
            name: string
            version?: string
            args?: string[]
        }


    Details the invocation of the program that created the index (binary name,
    version of the binary, and command line arguments). This field is optional
    but encouraged as Sourcegraph will need to extract the name of the indexer
    on upload. If this field is absent, the name of the indexer must be
    explicitly supplied to src-cli on upload.

    For example:

    .. code-block:: bash

        $ src lsif upload -name="my-indexer"

.. _vertex-project:

Vertex: Project
---------------

.. _project:
.. parsed-literal::

    interface Project extends :ref:`Vertex <Vertex>` {
        :js:attr:`label <Element.label>`: 'project'
        :js:attr:`kind <Project.kind>`: string
        :js:attr:`contents <Project.contents>`?: string
    }


.. js:attribute:: Project.kind

    TODO: kind

.. js:attribute:: Project.contents

    TODO: contents


Usually language servers operate in some sort of project context. In
TypeScript, a project is defined using a ``tsconfig.json`` file. C# and C++ have
their own means. The project file usually contains information about compile
options and other parameters. Having these in the dump can be valuable. The
LSIF therefore defines a project vertex. In addition, all documents that belong
to that project are connected to the project using a ``contains`` edge. If there
was a ``tsconfig.json`` in the previous examples, the first emitted edges and
vertices would look like this:

.. code-block:: typescript

    { id: 1, type: "vertex", label: "project", resource: "file:///Users/dirkb/tsconfig.json", kind: "typescript"}
    { id: 2, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }
    { id: 3, type: "edge", label: "contains", outV: 1, inVs: [2] }

.. _vertex-document:

Vertex: Document
----------------

.. parsed-literal::
    interface Document extends Vertex {
        :js:attr:`label <Element.label>`: 'document'
        :js:attr:`uri <Document.uri>`: string
        :js:attr:`contents <Document.contents>`?: string
    }

TODO - add languageId field

TODO - add project contains

.. js:attribute:: Document.uri

    Indicates absolute the path to the text document. The relative path to this
    text document, within the file tree bounds of the containing index, is
    determined from the metadata project root. Thus, it is invalid for these
    URIs to not share a common prefix.

.. js:attribute:: Document.contents

    If the `Contents` field has a defined value, it is expected to be the
    base64-encoded representation of the entire document. As with LSP, only text
    documents whose contents can be represented as a string are supported. There
    is currently no support for binary documents.


.. _vertex-range:

Verex: Range
-------------

Range vertices denote areas within a text that are sensitive to user
interaction, such as a user request for the hover text associated with the
identifier defined at a particular text document position. The text over which
a range refers is determined by the elements adjacent to the range and is
discussed in more detail below.

A position within text is expressed as a zero-based line and character offset
where the offsets are based on the UTF-16 string representation of the text. A
range within text is expressed as an inclusive start position and an exclusive
end position. To specify a range containing a line ending character, use an end
position denoting the start of the next line (e.g., `[5:12) - [6:0)`).

.. _range:

.. parsed-literal::

    interface Range extends :ref:`Vertex <vertex>`, :ref:`RangeData <range-data>` {
        :js:attr:`label <Element.label>`: 'range'
        :js:attr:`tag <Range.tag>`?: RangeTag
    }

.. js:attribute:: Range.tag

    TODO: Range.tag

.. _range-tag:

.. parsed-literal::

    interface RangeTag {
        Type: string
        Text: string
        Kind: int
        FullRange?: RangeData
        Detail: string
        Tags: int[]
    }

.. _range-data:
.. _position:

.. parsed-literal::

    interface RangeData {
        Start: Position
        End: Position
    }


    interface Position {
        Line: int
        Character: int
    }

TODO: Explain range tags.

In order to determine the text to which a range refers, we look for the vertex
incident to the range via the contains relation. Containment is a 1-to-n
relationship encoded by the following type.

.. parsed-literal::

    interface ContainsEdge extends :ref:`Edge1toN <edge-n>` {
        :js:attr:`label <Element.label>`: 'contains'
    }

The `OutV` field indicates the parent side of the relationship and the `InVs`
specifies the set of elements contained by the parent. Ranges may be contained
by any element that represents a piece of text (e.g., a text document, a
documentation string).

For range elements, the following constraints apply:

1. A range must be contained by exactly one parent
2. Two ranges contained by the same parent must not be equal
3. Two ranges contained by the same parent must not overlap unless one range completely encloses the other

QUESTION: Is this Sourcegraph specific or spec specific?

If a range completely encloses another, the inner-most range (i.e., the one
with the smallest extents) should be used to resolve a user request. If the
inner-most range does not define the target relationship used to fulfill the
user request, then the next inner-most range should be used instead (and so
on).


.. _vertex-resultrange:

Vertex: Result Range
--------------------

Result range vertices denote ranges used as part of a response to a user
request. Result ranges are a variant of range objects encoded by the following
type.

.. _result-range:

.. parsed-literal::

    interface ResultRange extends :ref:`Vertex <vertex>`, :ref:`RangeData <range-data>` {
        :js:attr:`label <Element.label>`: 'resultRange'
    }


.. _vertex-resultset:

Vertex: Result Set
------------------

.. _result-set:

.. parsed-literal::

    interface ResultSet extends :ref:`Vertex <vertex>` {
        :js:attr:`label <Element.label>`: 'resultSet'
    }

TODO

.. _edge-next:

.. parsed-literal::

    interface EdgeNext extends :ref:`Edge1to1 <edge-1>` {
        :js:attr:`label <Element.label>`: 'next'
    }


![foo](./diagrams/result_sets.svg)

TODO

Usually the hover result is the same whether you hover over a definition of a
function or over a reference of that function. The same is actually true for
many LSP requests like ``textDocument/definition``, ``textDocument/references`` or
``textDocument/typeDefinition``. In a naïve model, each range would have outgoing
edges for all these LSP requests and would point to the corresponding results.
To optimize this and to make the graph easier to understand, the concept of a
``ResultSet`` is introduced. A result set acts as a hub to be able to store
information common to a lot of ranges. The ``ResultSet`` itself doesn't carry any
information. So it looks like this:

Result sets are linked to ranges using a ``next`` edge. A results set can also
forward information to another result set by linking to it using a ``next`` edge.

The pattern of storing the result with the ``ResultSet`` will be used for other
requests as well. The lookup algorithm is therefore as follows for a request
[document, position, method]:

.. parsed-literal::

    1. find all ranges for [document, position]. If none exist, return `null` as the result
    1. sort the ranges by containment the innermost first
    1. for range in ranges do
       1. assign range to out
       1. while out !== `null`
          1. check if out has an outgoing edge `textDocument/${method}`. if yes, use it and return the corresponding result
          1. check if out has an outgoing `next` edge. If yes, set out to the target vertex. Else set out to `null`
       1. end
    1. end
    1. otherwise return `null`

### Monikers

TODO

.. parsed-literal::

    interface Moniker extends Vertex {
        Label: 'moniker'
        Kind: string
        Scheme: string
        Identifier: string
    }

TODO

moniker kind:
    - import
    - export

    - sourcegraph: implementation

.. parsed-literal::

    interface PackageInformation extends Vertex {
        Label: 'packageInformation'
        Name: string
        Version: string
    }

TODO


.. parsed-literal::

    interface MonikerEdge extends Edge1to1 {
        Label: 'moniker'
    }

.. parsed-literal::

    interface PackageInformationEdge extends Edge1to1 {
        Label: 'packageInformation'
    }

TODO

.. parsed-literal::

    interface NextMonikerEdge extends Edge1to1 {
        Label: 'nextMoniker'
    }

TODO

One use case of the LSIF is to create dumps for released versions of a product,
either a library or a program. If a project **A** references a library **B**,
it would also be useful if the information in these two dumps could be related.
To make this possible, the LSIF introduces optional monikers which can be
linked to ranges using a corresponding edge. The monikers can be used to
describe what a project exports and what it imports. Let's first look at the
export case.

This describes the exported declaration inside `index.ts` with a moniker (e.g.
a handle in string format) that is bound to the corresponding range
declaration. The generated moniker must be position independent and stable so
that it can be used to identify the symbol in other projects or documents. It
should be sufficiently unique so as to avoid matching other monikers in other
projects unless they actually refer to the same symbol. A moniker therefore has
two properties: a `scheme` to indicate how the `identifiers` is to be
interpreted. And the `identifier` to actually identify the symbol. It structure
is opaque to the scheme owner. In the above example the monikers are created by
the TypeScript compiler tsc and can only be compared to monikers also having
the scheme `tsc`.

How these exported elements are visible in other projects in most programming
languages depends on how many files are packaged into a library or program. In
TypeScript, the standard package manager is npm.


Things to observe:

- a special ``packageInformation`` vertex got emitted to point to the corresponding npm package information.
- the npm moniker refer to the package name.
- since the file `index.ts` is the npm main file the moniker identifier as no file path. The is comparable to importing this module into TypeScript or JavaScript were only the module name and no file path is used (e.g. `import * as lsif from 'lsif-ts-sample'`).
- the `nextMoniker` edge points from the tsc moniker vertex to the npm moniker vertex.

For tools processing the dump and importing it into a database it is sometime useful to know whether a result is local to a file or not (for example function arguments can only be navigated inside the file). To help postprocessing tools to decide this LSIF generation tools should generate a moniker for locals as well. The corresponding kind to use is `local`. The identifier should still be unique inside the document.

In addition to this moniker schemes starting with `$` are reserved and shouldn't be used by a LSIF tool.

Language Features
=================


Feature: Hover 
-------------------

This is analogous to ``textDocument/hover``.

In the LSP, the hover is defined as follows:

.. code-block:: typescript

    export interface Hover {
      /**
       * The hover's content
       */
      contents: MarkupContent | MarkedString | MarkedString[];

      /**
       * An optional range
       */
      range?: Range;
    }

where the optional range is the name range of the word hovered over.

For LSIF... TODO

.. parsed-literal::

    interface HoverResult extends Vertex {
      Label: 'hoverResult'
        Result: HoverContents
    }

    interface HoverContents {
        Contents: HoverPar[]
    }

    type HoverPart =
        | { Value: string, Language: string }
        | { Value: string, Kind: string }
        | string



> **Side Note**: This is a pattern used for other LSP requests as well, where the result contains the word range of the word the position parameter pointed to.

This makes the hover different for every location so we can't really store it
with the result set. But wait, the range is the range of one of the `bar`
references we already emitted and used to start to compute the result. To make
the hover still reusable, we ask the index server to fill in the starting range
if no range is defined in the result. So for a hover request executed on range
`{ line: 4, character: 2 }, end: { line: 4, character: 5 }` the hover result
will be:

.. code-block:: typescript

    { id: 6, type: "vertex", label: "hoverResult", result: { contents: [ { language: "typescript", value: "function bar(): void" } ], range: { line: 4, character: 2 }, end: { line: 4, character: 5 } } }

Feature: Definition
--------------------

Things to cover:

- document node
- ranges
- "next" edges
- resultset
- definitionResult
- textDocument/definition edge
- item edge

TODO

REFERENCE
The same pattern of connecting a range, result set, or a document with a request edge to a method result is used for other requests as well. Let's next look at the `textDocument/definition` request using the following TypeScript sample:

.. code-block:: typescript

    function bar() {
    }

    function foo() {
      bar();
    }

This will emit the following vertices and edges to model the `textDocument/definition` request:

.. code-block:: typescript

    // The document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }

    // The bar declaration
    { id: 6, type: "vertex", label: "resultSet" }
    { id: 9, type: "vertex", label: "range", start: { line: 0, character: 9 }, end: { line: 0, character: 12 } }
    { id: 10, type: "edge", label: "next", outV: 9, inV: 6 }


    // The bar reference
    { id: 20, type: "vertex", label: "range", start: { line: 4, character: 2 }, end: { line: 4, character: 5 } }
    { id: 21, type: "edge", label: "next", outV: 20, inV: 6}

    // The definition result linked to the bar result set
    { id: 22, type: "vertex", label: "definitionResult" }
    { id: 23, type: "edge", label: "textDocument/definition", outV: 6, inV: 22 }
    { id: 24, type: "edge", label: "item", outV: 22, inVs: [9], document: 4 }

<img src="../img/definitionResult.png" alt="Definition Result" style="max-width: 50%; max-height: 50%"/>

The definition result above has only one value (the range with id '9') and we could have emitted it directly. However, we introduced the definition result vertex for two reasons:

- To have consistency with all other requests that point to a result.
- To have support for languages where a definition can be spread over multiple ranges or even multiple documents. To support multiple documents ranges are added to a definition result using an 1:N `item` edge. Conceptionally a definition result is an array to which the `item` edge adds items.

Consider the following TypeScript example:

.. code-block:: typescript

    interface X {
      foo();
    }
    interface X {
      bar();
    }
    let x: X;

Running **Go to Definition** on `X` in `let x: X` will show a dialog which lets the user select between the two definitions of the `interface X`. The emitted JSON in this case looks like this:

.. code-block:: typescript

    { id : 38, type: "vertex", label: "definitionResult" }
    { id : 40, type: "edge", label: "item", outV: 38, inVs: [9, 13], document: 4 }

The `item` edge as an additional property document which indicate in which document these declaration are. We added this information to still make it easy to emit the data but also make it easy to process the data to store it in a database. Without that information we would either need to specific an order in which data needs to be emitted (e.g. a item edge and only refer to a range that got already added to a document using a `containes` edge) or we force processing tools to keep a lot of vertices and edges in memory. The approach of having this `document` property looks like a fair balance.

Feature: Declaration
--------------------

There are programming languages that have the concept of declarations and
definitions (like C/C++). If this is the case, the dump can contain a
corresponding `declarationResult` vertex and a `textDocument/declaration` edge
to store the information. They are handled analogously to the entities emitted
for the `textDocument/definition` request.

.. warning::

   Sourcegraph does not support this.

#### References

TODO

REFERENCE
Storing references will be done in the same way as storing a hover or go to definition ranges. It uses a reference result vertex and `item` edges to add ranges to the result.

Look at the following example:

.. code-block:: typescript

    function bar() {
    }

    function foo() {
      bar();
    }

The relevant JSON output looks like this:

.. code-block:: typescript

    // The document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }

    // The bar declaration
    { id: 6, type: "vertex", label: "resultSet" }
    { id: 9, type: "vertex", label: "range", start: { line: 0, character: 9 }, end: { line: 0, character: 12 } }
    { id: 10, type: "edge", label: "next", outV: 9, inV: 6 }

    // The bar reference range
    { id: 20, type: "vertex", label: "range", start: { line: 4, character: 2 }, end: { line: 4, character: 5 } }
    { id: 21, type: "edge", label: "next", outV: 20, inV: 6 }

    // The reference result
    { id : 25, type: "vertex", label: "referenceResult" }
    // Link it to the result set
    { id : 26, type: "edge", label: "textDocument/references",  outV: 6, inV: 25 }

    // Add the bar definition as a reference to the reference result
    { id: 27, type: "edge", label: "item", outV: 25, inVs: [9], document: 4, property : "definitions" }

    // Add the bar reference as a reference to the reference result
    { id: 28, type: "edge", label: "item", outV: 25, inVs: [20], document:4, property: "references" }

<img src="../img/referenceResult.png" alt="References Result"  style="max-width: 50%; max-height: 50%"/>

We tag the `item` edge with id 27 as a definition since the reference result distinguishes between definitions, declarations, and references. This is done since the `textDocument/references` request takes an additional input parameter `includeDeclarations` controlling whether declarations and definitions are included in the result as well. Having three distinct properties allows the server to compute the result accordingly.

The item edge also support linking reference results to other reference results. This is useful when computing references to methods overridden in a type hierarchy.

Take the following example:

.. code-block:: typescript

    interface I {
      foo(): void;
    }

    class A implements I {
      foo(): void {
      }
    }

    class B implements I {
      foo(): void {
      }
    }

    let i: I;
    i.foo();

    let b: B;
    b.foo();

The reference result for the method `foo` in TypeScript contains all three declarations and both references. While parsing the document, one reference result is created and then shared between all result sets.

The output looks like this:

.. code-block:: typescript

    // The document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }

    // The declaration of I#foo
    { id: 13, type: "vertex", label: "resultSet" }
    { id: 16, type: "vertex", label: "range", start: { line: 1, character: 2 }, end: { line: 1, character: 5 } }
    { id: 17, type: "edge", label: "next", outV: 16, inV: 13 }
    // The reference result for I#foo
    { id: 30, type: "vertex", label: "referenceResult" }
    { id: 31, type: "edge", label: "textDocument/references", outV: 13, inV: 30 }

    // The declaration of A#foo
    { id: 29, type: "vertex", label: "resultSet" }
    { id: 34, type: "vertex", label: "range", start: { line: 5, character: 2 }, end: { line: 5, character: 5 } }
    { id: 35, type: "edge", label: "next", outV: 34, inV: 29 }

    // The declaration of B#foo
    { id: 47, type: "vertex", label: "resultSet" }
    { id: 50, type: "vertex", label: "range", start: { line: 10, character: 2 }, end: { line: 10, character: 5 } }
    { id: 51, type: "edge", label: "next", outV: 50, inV: 47 }

    // The reference i.foo()
    { id: 65, type: "vertex", label: "range", start: { line: 15, character: 2 }, end: { line: 15, character: 5 } }

    // The reference b.foo()
    { id: 78, type: "vertex", label: "range", start: { line: 18, character: 2 }, end: { line: 18, character: 5 } }

    // The insertion of the ranges into the shared reference result
    { id: 90, type: "edge", label: "item", outV: 30, inVs: [16,34,50], document: 4, property: definitions }
    { id: 91, type: "edge", label: "item", outV: 30, inVs: [65,78], document: 4, property: references }

    // Linking A#foo to I#foo
    { id: 101, type: "vertex", label: "referenceResult" }
    { id: 102, type: "edge", label: "textDocument/references", outV: 29, inV: 101 }
    { id: 103, type: "edge", label: "item", outV: 101, inVs: [30], document: 4, property: referenceResults }

    // Linking B#foo to I#foo
    { id: 114, type: "vertex", label: "referenceResult" }
    { id: 115, type: "edge", label: "textDocument/references", outV: 47, inV: 114 }
    { id: 116, type: "edge", label: "item", outV: 114, inVs: [30], document: 4, property: referenceResults }

One goal of the language server index format is that the information can be emitted as soon as possible without caching too much information in memory. With languages that support overriding methods defined in more than one interface, this can be more complicated since the whole inheritance tree might only be known after parsing all documents.

Take the following TypeScript example:

.. code-block:: typescript

    interface I {
      foo(): void;
    }

    interface II {
      foo(): void;
    }

    class B implements I, II {
      foo(): void {
      }
    }

    let i: I;
    i.foo();

    let b: B;
    b.foo();

Searching for `I#foo()` finds 4 references, searching for `II#foo()` finds 3
reference, and searching on `B#foo()` finds 5 results. The interesting part
here is when the declaration of `class B` gets processed which implements `I`
and `II`, neither the reference result bound to `I#foo()` nor the one bound to
`II#foo()` can be reused. So we need to create a new one. To still be able to
profit from the results generated for `I#foo` and `II#foo`, the LSIF supports
nested references results. This way the one referenced from `B#foo` will reuse
the one from `I#foo` and `II#foo`. Depending on how these declarations are
parsed, the two reference results might contain the same references. When a
language server interprets reference results consisting of other reference
results, the server is responsible to de-dup the final ranges.

In the above example, there will be three reference results

.. code-block:: typescript

    // The document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }

    // Declaration of I#foo
    { id: 13, type: "vertex", label: "resultSet" }
    { id: 16, type: "vertex", label: "range", start: { line: 1, character: 2 }, end: { line: 1, character: 5 } }
    { id: 17, type: "edge", label: "next", outV: 16, inV: 13 }

    // Declaration of II#foo
    { id: 27, type: "vertex", label: "resultSet" }
    { id: 30, type: "vertex", label: "range", start: { line: 5, character: 2 }, end: { line: 5, character: 5 } }
    { id: 31, type: "edge", label: "next", outV: 30, inV: 27 }

    // Declaration of B#foo
    { id: 45, type: "vertex", label: "resultSet" }
    { id: 52, type: "vertex", label: "range", start: { line: 9, character: 2 }, end: { line: 9, character: 5 } }
    { id: 53, type: "edge", label: "next", outV: 52, inV: 45 }

    // Reference result for I#foo
    { id: 46, type: "vertex", label: "referenceResult" }
    { id: 47, type: "edge", label: "textDocument/references", outV: 13, inV: 46 }

    // Reference result for II#foo
    { id: 48, type: "vertex", label: "referenceResult" }
    { id: 49, type: "edge", label: "textDocument/references", outV: 27, inV: 48 }

    // Reference result for B#foo
    { id: 116 "typ" :"vertex", label: "referenceResult" }
    { id: 117 "typ" :"edge", label: "textDocument/references", outV: 45, inV: 116 }

    // Link B#foo reference result to I#foo and II#foo
    { id: 118 "typ" :"edge", label: "item", outV: 116, inVs: [46,48], document: 4, property: "referenceResults" }

For Typescript, method references are recorded at their most abstract declaration and if methods are merged (`B#foo`), they are combined using a reference result pointing to other results.

Feature: Implemenation
----------------------

Request: ``textDocument/implementation``

Supporting a ``textDocument/implementation`` request is done reusing what we implemented for a `textDocument/references` request. In most cases, the `textDocument/implementation` returns the declaration values of the reference result that a symbol declaration points to. For cases where the result differs, the LSIF provides an `ImplementationResult`. To nest implementation results the `item` edge supports a `property` value `"implementationResults"`.

The corresponding `ImplementationResult` looks like this:

.. code-block:: typescript

    interface ImplementationResult {
      label: `implementationResult`
    }

Feature: TypeDefinition
-----------------------

Request: textDocument/typeDefinition

Supporting ``textDocument/typeDefinition`` is straightforward. The edge is either recorded at the range or at the ``ResultSet``.

The corresponding ``TypeDefinitionResult`` looks like this:

.. code-block:: typescript

    interface TypeDefinitionResult {
        label: `typeDefinitionResult`
    }

For the following TypeScript example:

.. code-block:: typescript

    interface I {
      foo(): void;
    }

    let i: I;

The relevant emitted vertices and edges looks like this:

.. code-block:: typescript

    // The document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }

    // The declaration of I
    { id: 6, type: "vertex", label: "resultSet" }
    { id: 9, type: "vertex", label: "range", start: { line: 0, character: 10 }, end: { line: 0, character: 11 } }
    { id: 10, type: "edge", label: "next", outV: 9, inV: 6 }

    // The declaration of i
    { id: 26, type: "vertex", label: "resultSet" }
    // The type definition result
    { id: 37, type: "vertex", label: "typeDefinitionResult" }
    // Hook the result to the declaration
    { id: 38, type: "edge", label: "textDocument/typeDefinition", outV: 26, inV:37 }
    // Add the declaration of I as a target range.
    { id: 51, type: "edge", label: "item", outV: 37, inVs: [9], document: 4 }

As with other results ranges get added using a `item` edge. In this case without a `property` since there is only on kind of range.

Document requests
=================

The Language Server Protocol also supports requests for documents only (without
any position information). These requests are `textDocument/foldingRange`,
`textDocument/documentLink`, and `textDocument/documentSymbol`. We follow the
same pattern as before to model these, the difference being that the result is
linked to the document instead of to a range.


Feature: Folding Range
----------------------

### Request: `textDocument/foldingRange`

For the folding range result this looks like this:

.. code-block:: typescript

    function hello() {
      console.log('Hello');
    }

    function world() {
      console.log('world');
    }

    function space() {
      console.log(' ');
    }
    hello();space();world();

.. code-block:: typescript

    { id: 2, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }
    { id: 112, type: "vertex", label: "foldingRangeResult", result: [
        { startLine: 0, startCharacter: 16, endLine: 2, endCharacter: 1 },
        { startLine: 4, startCharacter: 16, endLine: 6, endCharacter: 1 },
        { startLine: 8, startCharacter: 16, endLine: 10, endCharacter: 1 }
    ] }
    { id: 113, type: "edge", label: "textDocument/foldingRange", outV: 2, inV: 112 }

The corresponding `FoldingRangeResult` is defined as follows:

.. code-block:: typescript

    export interface FoldingRangeResult {
      label: 'foldingRangeResult';
      result: lsp.FoldingRange[];
    }

Feature: Diagnostics
--------------------

.. code-block:: typescript

    interface Diagnostic extends Vertex {
        Type: 'diagnosticResult'
        Severity: int
        Code: string
        Message: string
        Source: string
        Range: RangeData
    }

REFERENCE

The only information missing that is useful in a dump are the diagnostics associated with documents. Diagnostics in the LSP are modeled as a push notifications sent from the server to the client. This doesn't work well with a dump modeled on request method names. However, the push notification can be emulated as a request where the request's result is the value sent during the push as a parameter.

In the dump, we model diagnostics as follows:

- We introduce a pseudo request `textDocument/diagnostic`.
- We introduce a diagnostic result which contains the diagnostics associated with a document.

The result looks like this:

.. code-block:: typescript

    export interface DiagnosticResult {
      label: 'diagnosticResult';
      result: lsp.Diagnostic[];
    }

The given TypeScript example:

.. code-block:: typescript

    function foo() {
      let x: string = 10;
    }

Produces the following output:

.. code-block:: typescript

    { id: 2, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript" }
    { id: 18, type: "vertex", label: "diagnosticResult", result: [{ severity: 1, code: 2322, message: "Type '10' is not assignable to type 'string'.", range: { start : { line: 1, character: 5 }, end: { line: 1, character: 6 } } } ] }
    { id: 19, type: "edge", label: "textDocument/diagnostic", outV: 2, inV: 18 }

Since diagnostics are not very common in dumps, no effort has been made to reuse ranges in diagnostics.

Events
------

To ease the processing of an LSIF dump to for example import it into a database the dump emits begin and end events for documents and projects. After the end event of a document has been emitted the dump must not contain any further data referencing that document. For example no ranges from that document can be referenced in `item` edges. Nor can result sets or other vertices linked to the ranges in that document. The document can however be reference in a `contains` edge adding the document to a project. The begin / end events for documents look like this:

.. code-block:: typescript

    // The actual document
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript", contents: "..." }
    // The begin event
    { id: 5, type: "vertex", label: "$event", kind: "begin", scope: "document" , data: 4 }
    // The end event
    { id: 53, type: "vertex", label: "$event", kind: "end", scope: "document" , data: 4 }

Between the document vertex `4` and the document begin event `5` no information specific to document `4` can be emitted. Please note that more than one document can be open at a given point in time meaning that there have been n different document begin events without corresponding document end events.

The events for projects looks similar:

.. code-block:: typescript

    { id: 2, type: "vertex", label: "project", kind: "typescript" }
    { id: 4, type: "vertex", label: "document", uri: "file:///Users/dirkb/sample.ts", languageId: "typescript", contents: "..." }
    { id: 5, type: "vertex", label: "$event", kind: "begin", scope: "document" , data: 4 }
    { id: 3, type: "vertex", label: "$event", kind: "begin", scope: "project", data: 2 }
    { id: 53, type: "vertex", label: "$event", kind: "end", scope: "document", data: 4 }
    { id: 54, type: "edge", label: "contains", outV: 2, inVs: [4] }
    { id: 55, type: "vertex", label: "$event", kind: "end", scope: "project", data: 2 }


.. _data-schemas:

Data schemas
============


NDJSON
------

New line json things. Berry nice.

So you want to write an indexer?
================================

Emitting Constraints
--------------------

The following emitting constraints (some of which have already mean mentioned in the document) exists:

- a vertex needs to be emitted before it can be referenced in an edge.
- a ``range`` and ``resultRange`` can only be contained in one document.
- a ``resultRange`` can not be used as a target in a ``contains`` edge.
- after a document end event has been emitted only result sets, reference or implementation results emitted through that document can be referenced in edges. It is for example not allowed to reference ranges or result ranges from that document. This also includes adding monikers to ranges or result sets. The document data so to speak can not be altered anymore.
- if ranges point to result sets and monikers are emitted, they must be emitted on the result set and can't be emitted on individual ranges.

.. _Lsif Specification: https://microsoft.github.io/language-server-protocol/specifications/lsif/0.5.0/specification/
