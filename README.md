# Website Broken-Link Checker

**CMPSC 462 — Data Structures | Honors Option**


This project builds a command-line website auditing tool around student-written data structures.

## 1. Abstract

Broken hyperlinks interrupt navigation and leave website maintainers with an incomplete picture of what needs repair. Checking a destination is only part of the problem: a useful checker must also identify the pages that contain the link, avoid repeatedly checking the same destination, and distinguish a missing page from a temporary or restricted response.

The proposed system will discover hyperlinks, check their HTTP outcomes, and produce a report connecting each problematic destination to its source pages. A custom linked queue will manage traversal, a custom hash map and hash set will manage lookup and deduplication, and a directed graph will retain link relationships, min-heap will schedule delayed retries. HTTP and HTML libraries will provide networking and parsing.

Evaluation will examine correctness, execution time, and Python memory allocations using controlled websites and repeatable synthetic workloads. The intended outcome is a usable utility and an explanation of the tradeoffs behind its design.

## 2. Problem Statement

A flat collection of URLs can answer whether particular destinations respond. It does not, by itself, preserve every location where a destination appears.

For example, both an About page and a Products page may link to the same missing Contact page. The destination should have one primary check job, while the report should identify both source pages. A website may also contain cycles, repeated navigation links, redirects, and URLs that differ only in their fragment.

The project addresses four practical problems:

1. Avoid duplicate primary check jobs and repeated traversal through cycles.
2. Preserve all discovered source-to-destination relationships.
3. Classify observed outcomes accurately instead of calling every unsuccessful request a broken link.
4. Bound the crawl and explain which parts of the site were checked, skipped, or left unresolved.

## 3. Objectives and Research Questions

### Objectives

- Build a working checker that accepts a starting URL and explicit crawl limits.
- Implement the queue, hash map, hash set, and graph representation in student code.
- Report problematic URLs with their source pages and observed evidence.
- Export reusable CSV and JSON results.
- Demonstrate the program and explain its data structures in a report and presentation.

### Research questions

1. How does hash-based deduplication compare with searching a list as the number of discovered links grows?
2. How does storing incoming graph edges affect the cost of finding every source of a broken link?
3. What time and memory costs arise from retaining both outgoing and incoming links?
4. If retries are implemented, how does a min-heap compare with repeatedly searching a list for the next due retry?

These are questions to investigate. The project does not assume the custom implementations will outperform Python's built-in containers.

## 4. Proposed Solution

The user supplies a starting URL. The checker processes reachable pages within the selected scope and records what it discovers.

The workflow is:

1. Validate the configuration and starting URL.
2. Resolve each extracted hyperlink against the document's effective URL and HTML base URL, if present.
3. Record its source relationship even if the destination was discovered earlier.
4. Admit eligible, previously unseen destinations into the queue.
5. Request each admitted destination and record its HTTP or network outcome.
6. Extract links from eligible HTML responses.
7. Continue until the work is exhausted or a configured limit is reached.
8. Generate a report from the final graph and result records.

A destination is scheduled once for its primary job. Redirect requests, permitted retries, and optional browser rendering can create additional network requests; these are counted separately.

### Why retain a graph?

The graph is a directed record of hyperlinks. Vertices represent normalized URLs, and edges represent links found in pages. Incoming edges answer, "Which checked pages contain this destination?"

The graph can be implemented as outgoing and incoming adjacency maps. A separate graph class provides a clear interface, but the useful information is the adjacency data itself. The graph is not required merely to send HTTP requests.

For example, if /about and /products both link to /contact, the incoming neighbors of /contact contain both source URLs. The report can therefore identify both places that need attention.

## 5. Scope

### Required baseline

- Command-line execution.
- Public HTTP and HTTPS URLs.
- A finite crawl of hyperlinks in HTML anchor elements.
- Internal traversal within the canonical starting origin.
- Relative URL resolution and conservative normalization.
- Custom queue, hash map, hash set, and directed graph.
- HTTP outcome classification, bounded redirects, and timeouts.
- Robots policy checks and request pacing.
- Source attribution for every retained hyperlink.
- CSV and JSON reports, correctness tests, and controlled benchmarks.

The canonical starting origin is the scheme, host, and effective port of the seed's permitted final destination. Subsequent redirects may be checked, but HTML from another origin is not expanded into a new crawl.

### Planned extensions, after the baseline works

- Checking external destinations without recursively crawling external websites.
- Delayed retries using a custom min-heap.
- Bounded concurrent requests.
- An optional Playwright mode for JavaScript-generated links.

### Outside the initial scope

Authentication, form submission, automatic website repair, distributed crawling, a hosted dashboard, database persistence, SEO scoring, image/script asset auditing, and fragment-target validation are outside the initial scope. The initial checker also does not infer "soft 404" pages from their text.

A trie, a tree, or other additional structure should be introduced only with a concrete feature or experiment. The project does not require every structure covered in the course.

## 6. Data Structures and Responsibilities

| Structure | Student implementation | Responsibility |
|---|---|---|
| Singly linked list | Nodes plus head and tail references | Underlying storage for the FIFO queue. |
| Queue | Enqueue, dequeue, size, and empty checks | Manage URLs waiting for their primary job. |
| Hash map | Bucket array, separate chaining, lookup, insertion/update, deletion, and resizing | Store URL records, check results, and adjacency indexes. |
| Hash set | A wrapper over the custom hash map | Track discovered URLs and unique neighbors. |
| Directed graph | Custom maps of custom neighbor sets | Store incoming and outgoing hyperlink relationships. |
| Min-heap, extension | Array-backed heap with sift-up and sift-down | Select the earliest scheduled retry. |

Lists may be used as backing arrays, and Python's hash function may compute hashes. Python dictionaries, sets, deque, heapq, or a graph library must not replace the custom structures in the project operations being evaluated. They may be used by dependencies, for ordinary configuration/serialization, and as reference implementations in tests or benchmarks.

The graph adds a relationship before the discovery check decides whether another fetch is necessary. Finding a new source for an already-checked URL must still update the graph.

## 7. Technology Stack

| Tool | Purpose |
|---|---|
| Python | Application logic and custom structures. Select a supported Python version and record the tested version. |
| HTTPX | HTTP requests, response inspection, connection reuse, and the later asynchronous transport. [1][2] |
| Beautiful Soup | HTML parsing and hyperlink extraction. Start with Python's built-in HTML parser. [3] |
| Typer | Command-line options and help. [4] |
| Rich | Terminal progress and readable result summaries. [5] |
| pytest | Structure, component, and integration tests. [6] |
| pytest-asyncio | Tests for the later asynchronous implementation. [7] |
| Playwright, optional | Render JavaScript-generated page content in a browser. [8] |
| Python standard library | URL parsing, robots parsing, records, logging, CSV/JSON export, timing, and allocation measurements. [9][10] |

The student's queue and indexes manage the crawl. HTTPX and Playwright perform network/browser work; Beautiful Soup supplies the parsed HTML tree. Library-owned internal structures are not claimed as student implementations.

## 10. Reports and User Interaction

The planned CLI will expose the starting URL, crawl limits, pacing, output location, and optional extension modes. Exact executable names and setup commands must be documented after implementation and verified from a clean environment.

The terminal summary should show:

- Retained unique URLs, completed primary jobs, and actual network requests.
- Counts by final outcome.
- Recorded hyperlink edges and elapsed time.
- Whether the scan ended normally, hit a limit, or was interrupted.

The JSON report should include configuration, coverage, per-URL results, redirect evidence, and source relationships. The CSV report should use one row per problematic-destination/source pair so maintainers can identify all affected pages. A problem at the seed itself must remain visible even when it has no source page.

The source list must be assembled after crawling, because additional source pages may be discovered after a destination's check is complete.

## 11. Complexity Analysis

Let V be retained URLs, E be retained unique hyperlink edges, and R be pending retries. The following bounds assume average hash behavior and treat key comparison/hashing costs separately.

| Operation | Expected time |
|---|---|
| Queue enqueue or dequeue | O(1) |
| Hash lookup / set membership | O(1) expected; O(V) worst case |
| Hash insertion | O(1) amortized expected; resizing costs O(V) for that resize |
| Add a graph edge | O(1) expected amortized |
| Enumerate sources of one URL | O(in-degree of that URL) |
| Traverse the retained graph | O(V + E), excluding networking and parsing |
| Heap insertion or removal | O(log R) |
| Inspect next retry | O(1) |

Graph and indexing storage is O(V + E), plus retry storage O(R) and bounded response buffers. Storing incoming and outgoing adjacency retains two representations of each edge without changing the asymptotic bound.

Real runtime also includes URL-string hashing, HTML parsing, network waits, redirects, and rendering. An O(V + E) traversal claim is not a claim that an entire web scan has that wall-clock complexity.

## 14. Academic Deliverables

The student will produce:

1. Working source code and custom data-structure implementations.
2. Correctness tests and reproducible benchmark scripts.
3. Example CSV/JSON reports from a controlled demonstration.
4. A written report covering the problem, design, complexity, experiments, results, and limitations.
5. Program execution and a presentation in class or through a video recording.


## 15. References

1. [HTTPX QuickStart](https://www.python-httpx.org/quickstart/)
2. [HTTPX asynchronous support](https://www.python-httpx.org/async/)
3. [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
4. [Typer documentation](https://typer.tiangolo.com/)
5. [Rich documentation](https://rich.readthedocs.io/en/stable/introduction.html)
6. [pytest documentation](https://docs.pytest.org/en/stable/)
7. [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/en/stable/)
8. [Playwright Python library](https://playwright.dev/python/docs/library)
9. [Python URL parsing](https://docs.python.org/3/library/urllib.parse.html)
10. [Python robots.txt parser](https://docs.python.org/3/library/urllib.robotparser.html)
11. [RFC 9309: Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html)
