# Simplyblock Documentation

Simplyblock is a high-performance, ultra-low-latency storage solution. It enables enterprise-grade, NVMe/TCP-powered block
storage directly inside Proxmox, offering high performance, scalability, and resilience without the need for specialized
hardware or vendor lock-in.

With simplyblock, you can seamlessly integrate **software-defined storage (SDS)** into your Proxmox environment, enabling support for advanced features like:

- ⚡ **Ultra-low latency**: Unlock performance with NVMe-over-TCP
- 🧩 **Native Proxmox integration**: Manage volumes directly in Proxmox
- 🛡️ **Enterprise data services**: Snapshots, clones, erasure coding, multi-tenancy
- 🔒 **Secure & robust**: Cluster authentication and Quality of Service (QoS)
- ☁️ **Cloud & on-prem flexibility**: Deploy anywhere Proxmox runs

👉 The deployed documentation is available at [https://docs.simplyblock.io](https://docs.simplyblock.io/latest/).

![](assets/simplyblock-logo.svg)

## How To Extend The Documentation

This repository contains the [simplyblock documentation](https://docs.simpylblock.io). It is built using
[mkdocs](https://www.mkdocs.org/) and uses a provided shell script `doc-builder` to ease the process of working with it.

- [Simplyblock Documentation](#simplyblock-documentation)
    * [How To Extends The Documentation](#how-to-extend-the-documentation)
    * [Docs Builder](#-docs-builder)
        + [Serving Content Locally](#serving-content-locally)
        + [Building a Static Version of the Documentation](#building-a-static-version-of-the-documentation)
        + [Preparing the Deployment of a New Version](#preparing-the-deployment-of-a-new-version)
    * [Structure of the Documentation](#-structure-of-the-documentation)
        + [Folder Structure](#folder-structure)
        + [Writing a Documentation Page](#writing-a-documentation-page)
        + [Documentation Features](#documentation-features)
            - [Links](#links)
            - [Admonitions](#admonitions)
                * [Notes](#notes)
                * [Recommendations](#recommendations)
                * [Infos](#infos)
                * [Warnings](#warnings)
                * [Dangers](#dangers)
            - [Code Blocks](#code-blocks)
            - [Content Tabs](#content-tabs)
            - [Tables](#tables)
            - [Diagrams](#diagrams)
            - [Footnotes](#footnotes)
            - [Icons and Emojis](#icons-and-emojis)
  * [Contributing](#-contributing)
  * [Release Process](#-release-process)

## 🛠️ Docs Builder

The `doc-builder` tool uses Docker and a customized mkdocs Docker image to serve and build the documentation. The
image contains all required plugins.

When using `doc-builder` for the first time (and ideally after an update of the Git repository), the Docker image
needs to be built using:

```bash
./doc-builder build-image
```

In addition, external repositories have to be checked out, to generate the necessary documentation pages. The
`doc-builder` simplifies this process with a specific command which either creates an initial checkout or updates the
repositories to the latest commit.

```bash
./doc-builder update-repositories
```

The command can be run at any time to update the external repositories to the latest commit.

### Serving Content Locally

When building or updating the documentation, it is useful to have a local builder with live updating. Mkdocs supports
this, as does the `doc-builder`. To simplify the process of working with mkdocs, there is a command to start the
local builder:

```bash
./doc-builder serve
```

### Building a Static Version of the Documentation

To test a fully built, static version of the current documentation, the docs can be built into the `./site` directory.
This version can be used independently and deployed by dropping it into any webserver that is able to serve static
content.

To build the static version, use the following command:

```bash
./doc-builder build
```

### Preparing the Deployment of a New Version

Since the documentation system supports the deployment and management of multiple versions, previous and current
versions are collected in the `./deployment/` folder. The symlinks are automatically updated according to the newest
version, as is the `versions.json` file.

To simplify the process of a new version deployment of the documentation, the `doc-builder` provides the necessary
command.

```bash
./doc-builder deploy {version-name}
```

The given _version-name_ will be used as a directory name and name of the version in the dropdown selector. Hence, it
is recommended that it only contains lowercase letters, numbers, and underscores or dashes.

## 📚 Structure of the Documentation

The simplyblock documentation uses [mkdocs](https://www.mkdocs.org/) as the underlying framework. As the theme, the
simplyblock documentation uses [mkdocs-material](https://squidfunk.github.io/mkdocs-material/).

### Folder Structure

The simplyblock documentation uses the following basic folder structure:

```plain
 documentation root
 ├─ deployment/                            (1)
 |  ├─ .htaccess                           (2)
 |  ├─ versions.json (symlink)             (3)
 |  ├─ latest/ (symlink)                   (4)
 |  ├─ ... version folders/                (5)
 ├─ docs/                                  (6)
 |  ├─ index.md                            (7)
 |  ├─ assets/                             (8)
 |  |  ├─ javascripts/                     (9)
 |  |  |  └─ ... .js files                 (10)
 |  |  ├─ stylesheets/                     (11)
 |  |  |  └─ extra.css                     (12)
 |  |  └─ ... .svg / .png / .jpg files     (13)
 |  ├─ ... folders/                        (14)
 |  |  ├─ index.md                         (15)
 |  |  └─ ... .md files                    (16)
 ├─ snippets/                              (17)
 |  └─ ... .md files                       (18)
 ├─ templates/                             (19)
 ├─ doc-builder                            (20)
 ├─ Dockerfile                             (21)
 ├─ mkdocs.yml                             (22)
 └─ README.md                              (23)
```

1. The `deployment` folder contains all currently built and deployed versions of the documentation.
2. The `.htaccess` file contains the necessary redirect rules to automatically redirect to the latest version.
3. The `versions.json` symlink links to `latest/versions.json`.
4. The `latest` symlink links to the latest deployed version of the documentation.
5. The versions folders are subfolders representing the different versions of the documentation.
6. The `docs` folder contains the documentation source files.
7. The `index.md` contains the initial index page of the documentation.
8. The `assets` folder contains additional assets such as images, stylesheets, and javascript files.
9. The `javascripts` folder contains additional javascript files.
10. The additional javascript files.
11. The `stylesheets` folder contains the extra.css file which defines additional stylesheets.
12. The `extra.css` file defines additional stylesheets.
13. The additional image files.
14. The folders contain the substructure of the documentation. A folder represents a subsection of the documentation.
15. The `index.md` file is the index page of the subsection.
16. The other markdown files add additional pages to the subsection.
17. The `snippets` folder contains reusable and injectable documentation snippets.
18. The markdown files contain snippets to be injected.
19. The `templates` folder contains template overrides and adjustments.
20. The `doc-builder` file is the helper script to test and build the documentation.
21. The `Dockerfile` file contains the necessary build instructions for the Docker container used by `doc-builder`.
22. The `mkdocs.yml` file contains the mkdocs configuration.
23. The `README.md` file is this file.

### Writing a Documentation Page

To add a new documentation pages, a markdown file have to be created. This markdown file consists of two sections, a
section called front matter which is a YAML section defining the position of the new file in the subsections hierarchy
and title, as well as the actual markdown part, representing the content of the file.

```markdown
---
title: "My Page Title"  # Page Title
weight: 123             # Page Position 
---

Introduction text

## Markdown Header

Markdown content
```

- A markdown documentation page always starts with a short introduction text without its own heading.
- Markdown headings in documentation pages only use H2 (##), H3 (###), H4 (####), and H5 (#####). H1 (#) is never used directly.
- The documentation page title must not be longer than two lines in the documentation navigation. Keep it short and precise.
- The weight should use larger steps in the tens or hundreds to ease injection of additional pages without changing all following weights. 

### Documentation Features

The documentation system supports a number of styling and admonitions.

#### Links

The documentation uses standard markdown link syntax. However, links to external pages should be marked with an
additional marker to open those links in a new browser tab.

In addition, internal links must use relative paths to the linked content file. If the internal link links to a heading
on the same page, the hash sign (#) can be used directly. It is also possible to link to headings in other pages by
following up the relative link the hash sign (#) and the heading id.

```markdown
[Internal Link](../internal/url.md)
[Internal Link To Heading](../internal/url.md#heading-id)
[Heading Link](#heading-id)

[External Link](https://some-external.url){:target="_blank" rel="noopener"}
```

The required heading ids are automatically generated as a full lowercase version of the heading with whitespaces and
special characters transformed into dashes (-).

#### Admonitions

Admonitions have specific meanings and should be used to emphasize certain parts of the documentation, warn users about
dangerous options, and send people to additional information.

Admonitions are normally started with three exclamation marks (!!!). In this case the admonition is fully visible at all
times. If started with three question marks (???) instead, the admonition is collapsed by default and can be manually
opened by the interested user with clicking the title. In this case, it is important to provide a title with the
admonition definition.

```markdown
??? note "This is the admonition title"
    The text goes here
```

##### Notes

Notes include additional information which may be interesting but not crucial.

```markdown
!!! note
    The text goes here
```

##### Recommendations

Recommendations include best practices and recommendations.

```markdown
!!! recommendation
    The text goes here
```

##### Infos

Information boxes include background and links to additional information.

```markdown
!!! info
    The text goes here
```

##### Warnings

Warnings contain crucial information that contain crucial information be considered before proceeding.

```markdown
!!! warning
    The text goes here
```

##### Dangers

Dangers contain crucial information that can lead to harmful consequences, such as data loss and irreversible damage.

```markdown
!!! danger
    The text goes here
```

#### Code Blocks

The documentation heavily uses code blocks for command description and example output. Code blocks should always use
the additional title attribute.

````markdown
```bash title="Some example title"
... code goes here
```
````

#### Content Tabs

Content tabs can be used to provide the same content (such as API call) in multiple programming languages. Content tabs
use three equal signs to define the different tabs and four spaces of indentation to define the tabs content.

```markdown
=== "curl"
    ```plain
    curl -L ...
    ```
    
=== "PHP"
    ```php
    $foo = file_get_contents(...);
    ```
```

#### Tables

The documentation uses "standard" extended markdown tables.

```markdown
| Title first Column  | Title second Column  | ... |
| ------------------- | -------------------- | --- |
| Content first row   | Content first row    | ... |
| Content second row  | Content second row   | ... |
| ...                 | ...                  | ... |
```
| Title first Column  | Title second Column  | ... |
| ------------------- | -------------------- | --- |
| Content first row   | Content first row    | ... |
| Content second row  | Content second row   | ... |
| ...                 | ...                  | ... |


To force left or right alignment of columns, colons (:) can be used.

```markdown
| Title first Column  | Title second Column  | ... |
| :------------------ | -------------------: | --- |
| Content first row   | Content first row    | ... |
| Content second row  | Content second row   | ... |
| ...                 | ...                  | ... |
```
| Title first Column  | Title second Column  | ... |
| :------------------ | -------------------: | --- |
| Content first row   | Content first row    | ... |
| Content second row  | Content second row   | ... |
| ...                 | ...                  | ... |

#### Diagrams

The documentation supports diagrams using mermaid. Please see the
[mkdocs-material documentation](https://squidfunk.github.io/mkdocs-material/reference/diagrams/) for more information.

````markdown
``` mermaid
graph LR
  A[Start] --> B{Error?};
  B -->|Yes| C[Hmm...];
  C --> D[Debug];
  D --> B;
  B ---->|No| E[Yay!];
```````

#### Footnotes

Footnotes can be used to add links to additional documentation.

```markdown
Here goes the text[^1] which uses the inline footnote identifier.

[^1]: The footnote which will be added to the end of the page.
```

#### Icons and Emojis

The documentation system provides three sets of icons and emojis which can be used throughout the documentation. Icons
are inserted using a colon (:) at the start and end of the icon name. The latter is a combination of collection name,
the name of the icon, and potentially additional parameters, such as the icon size.

```markdown
:fontawesome-brands-youtube:
:octicons-heart-fill-24:
:material-book-open-page-variant:
```

The icon names can be looked up in the corresponding collection's search feature:

- Fontawesome: [https://fontawesome.com/search](https://fontawesome.com/search)
- Octicons: [https://primer.style/foundations/icons](https://primer.style/foundations/icons)
- Material: [https://pictogrammers.com/library/mdi/](https://pictogrammers.com/library/mdi/)

Be aware that some of the collections have premium icons which are not included with the documentation builder. Only
free icons are available.

## 🤝 Contributing

If you find issues, typos, or have an enhancement request, please file and
[issue](https://github.com/simplyblock-io/documentation/issues) or create a
[pull request](https://github.com/simplyblock-io/documentation/pulls).

Pull requests are automatically built to check that there is no issues in the documentation changes, such as broken
links. After the pull request is successfully built, it will be reviewed and feedback provided or merged.

Any help with the documentation is highly appreciated!

## ⚙️ Release Process

The `main` branch is rebuild on any push and automatically deployed to the live documentation as the
[_development_ branch](https://docstest.simplyblock.io/dev/).

To create a new full version of the documentation, create a new branch from `main` or a previously tagged version (like
25.5.1) and the naming pattern `release/{version-number}`. The _version-number_ will be used as the folder name and title of
the version and as the tag name to lock the `sbcli` repository against. It is required to only use lowercase letters,
number, underscores, and dashes.

If your `sbcli` tag is named as `25.5.1`, the branch name MUST be named `release/25.5.1`.

In the branch, the following changes have to be performed:

- `docs/release-notes`
  - Create a new release notes file (best to duplicate the previous one).
  - Update the release version number in the frontmatter and the introduction sentence.
  - Decrement the weight in the frontmatter.
- Commit the changes to the release branch.
- Push the release branch and ensure the name is according to the pattern: `release/{version-number}` (e.g., `release/25.5.1`).

After pushing the new release branch, the GitHub action builder kicks in, builds the version, deploys it to the live
website and updates the latest symlink, creates the necessary tag for history reasons, and merges the built
documentation back into the `main` branch (folder `deployment`) using an auto-generated and auto-merged pull request. 

No further action is required.
