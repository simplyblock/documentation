---
title: "Contributing"
description: "Contributing: Simplyblock's documentation is publicly available, and contributions from the community to improve clarity, fix errors, and enhance it are welcome."
weight: 20600
---

# Contributing to Simplyblock Documentation

## Overview

Simplyblock's documentation is publicly available, and contributions from the community to improve clarity,
fix errors, and enhance its overall quality are welcome. While simplyblock itself is not open source, the
documentation is publicly hosted  [GitHub](https://github.com/simplyblock/documentation){:target="_blank" rel="noopener"}. Feedback,
reported typos, suggested improvements, and fixes for documentation inconsistencies are all appreciated.

## How to Contribute

The simplyblock documentation is built using [MkDocs](https://www.mkdocs.org/){:target="_blank" rel="noopener"}, specifically using the
[mkdocs-material](https://squidfunk.github.io/mkdocs-material/){:target="_blank" rel="noopener"} variant.

Changes to the documentation can be made by changing or adding the necessary Markdown files.

### 1. Provide Feedback or Report Issues

Inaccuracies, typos, missing information, and outdated content can be reported as an issue on the GitHub
repository:

1. Navigate to the [Simplyblock Documentation GitHub Repository](https://github.com/simplyblock/documentation){:target="_blank" rel="noopener"}.
2. Click on the **Issues** tab.
3. Click **New Issue** and provide a clear description of the problem or suggestion.
4. Submit the issue. The simplyblock team reviews it.

### 2. Make Edits and Submit a Pull Request (PR)

Direct changes to the documentation follow these steps:

1. **Fork the Repository**

- Visit [Simplyblock Documentation GitHub](https://github.com/simplyblock/documentation){:target="_blank" rel="noopener"} and click **Fork** to create
  a personal copy of the repository.

2. **Clone the Repository**

- Clone the fork to a local machine:
  ```sh
  git clone https://github.com/YOUR_USERNAME/documentation.git
  cd documentation
  ```

3. **Create a New Branch**

- Always create a new branch for the changes:
  ```sh
  git checkout -b update-docs
  ```

4. **Make Changes**

- Edit the relevant Markdown (`.md`) files using a text editor or IDE. The documentation files can be found in the
  `/docs` directory.
- Ensure that formatting follows existing conventions.

5. **Commit and Push the Changes**

- Commit the changes with a clear message:
  ```sh
  git commit -m "Fix typo in installation guide"
  ```
- Push the changes to the fork:
  ```sh
  git push origin update-docs
  ```

6. **Create a Pull Request (PR)**

- Navigate to the original simplyblock documentation repository.
- Click **New Pull Request** and select the branch.
- Provide a concise description of the changes and submit the PR.
- The simplyblock team reviews and merges accepted contributions.

## Contribution Guidelines

- Ensure all content remains clear, concise, and professional.
- Follow Markdown syntax conventions used throughout the documentation.
- Keep changes focused on documentation improvements (not product functionality).
- Be respectful and constructive in all discussions and contributions.

## Getting in Touch

Questions about contributing can be raised as an issue or through the simplyblock support channels.

