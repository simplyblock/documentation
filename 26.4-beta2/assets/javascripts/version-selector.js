// Version selector in the header, built from the versions.json at the site root.
//
// The two newest release lines (26.4.x, 26.3.x, ...) get a dropdown each, and
// every other version is listed in one "Other" dropdown: the development build
// pinned to the top, then the older versions grouped by release line. The
// dropdown holding the version being read shows that version as its label. On
// narrow screens, a single dropdown holds all groups, with the development
// build pinned to its top. Each entry opens the same page in the other
// version and falls back to that version's start page if the page does not
// exist there.
(function () {
  "use strict";

  const FEATURED_LINES = 2;
  const DEV_VERSION = "dev";
  const DEV_LABEL = "Development";
  const DEV_DESCRIPTION = "Documentation of the version in development";

  const topic = document.querySelector(".md-header__topic");
  const configElement = document.getElementById("__config");
  if (!topic || !configElement) {
    return;
  }

  // config.base is the relative path from the current page to the root of its
  // version, so it resolves to e.g. https://docs.simplyblock.io/26.4-beta2/.
  const versionRoot = new URL(JSON.parse(configElement.textContent).base + "/", location.href);
  const currentDir = versionRoot.pathname.split("/").filter(Boolean).pop();
  const pagePath = location.href.startsWith(versionRoot.href)
    ? location.href.slice(versionRoot.href.length)
    : "";

  fetch(new URL("../versions.json", versionRoot))
    .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
    .then(render)
    .catch(() => {
      // Without versions.json (a local "mkdocs serve", for example), the header
      // stays without a version selector.
    });

  // "26.4-beta2", "26.3.0", and "26.2-PRE" belong to the lines 26.4, 26.3, and
  // 26.2. A name without a major.minor prefix has no line.
  function lineOf(version) {
    const match = /^(\d+)\.(\d+)/.exec(version);
    return match ? { key: `${match[1]}.${match[2]}`, major: +match[1], minor: +match[2] } : null;
  }

  function render(versions) {
    const current = versions.find(
      (v) => v.version === currentDir || (v.aliases || []).includes(currentDir)
    );

    // versions.json lists the newest deployment first, so every line keeps that
    // order and its first entry is the newest version of the line.
    const lines = new Map();
    const unversioned = [];
    let dev = null;
    for (const v of versions) {
      if (v.version === DEV_VERSION) {
        dev = v;
        continue;
      }
      const line = lineOf(v.version);
      if (!line) {
        unversioned.push(v);
        continue;
      }
      if (!lines.has(line.key)) {
        lines.set(line.key, { ...line, versions: [] });
      }
      lines.get(line.key).versions.push(v);
    }

    const ordered = [...lines.values()].sort((a, b) => b.major - a.major || b.minor - a.minor);
    const featured = ordered.slice(0, FEATURED_LINES);
    const older = ordered.slice(FEATURED_LINES);

    const lineGroup = (l) => ({ heading: `${l.key}.x`, versions: l.versions });
    const pinned = dev ? [{ pinned: true, versions: [dev] }] : [];
    const olderGroups = older.map(lineGroup);
    if (unversioned.length) {
      olderGroups.push({ heading: "Unversioned", versions: unversioned });
    }

    const container = document.createElement("div");
    container.className = "sb-versions";

    for (const line of featured) {
      container.appendChild(
        dropdown(`${line.key}.x`, [{ versions: line.versions }], current, "sb-versions__wide")
      );
    }
    if (pinned.length || olderGroups.length) {
      container.appendChild(
        dropdown("Other", [...pinned, ...olderGroups], current, "sb-versions__wide")
      );
    }

    // One dropdown for narrow screens, with every release line as a heading.
    container.appendChild(
      dropdown("Version", [...pinned, ...featured.map(lineGroup), ...olderGroups], current, "sb-versions__narrow")
    );

    topic.appendChild(container);
  }

  function dropdown(label, groups, current, modifier) {
    const containsCurrent = groups.some((g) => g.versions.includes(current));

    const root = document.createElement("div");
    root.className = `md-version sb-versions__group ${modifier}`;
    if (containsCurrent) {
      root.classList.add("sb-versions__group--current");
    }
    if (groups.some((g) => g.heading)) {
      root.classList.add("sb-versions__group--grouped");
    }

    const button = document.createElement("button");
    button.className = "md-version__current";
    button.type = "button";
    button.setAttribute("aria-label", label === "Version" ? "Select a version" : `Select a version from ${label}`);
    button.textContent = containsCurrent ? titleOf(current) : label;
    root.appendChild(button);

    const list = document.createElement("ul");
    list.className = "md-version__list";
    for (const group of groups) {
      if (group.heading) {
        const heading = document.createElement("li");
        heading.className = "md-version__item sb-versions__heading";
        heading.textContent = group.heading;
        list.appendChild(heading);
      }
      for (const v of group.versions) {
        const item = document.createElement("li");
        item.className = group.pinned ? "md-version__item sb-versions__pinned" : "md-version__item";
        item.appendChild(versionLink(v, current, "md-version__link"));
        list.appendChild(item);
      }
    }
    root.appendChild(list);
    return root;
  }

  // versions.json titles the development build in lower case.
  function titleOf(v) {
    return v.version === DEV_VERSION ? DEV_LABEL : v.title;
  }

  function versionLink(v, current, className) {
    const target = new URL(`../${v.version}/`, versionRoot);
    const link = document.createElement("a");
    link.className = className;
    link.href = new URL(pagePath, target).href;
    link.textContent = titleOf(v);
    if (v.version === DEV_VERSION) {
      link.title = DEV_DESCRIPTION;
    }
    if (v === current) {
      link.setAttribute("aria-current", "page");
    }
    link.addEventListener("click", (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }
      event.preventDefault();
      // Pages move between versions, so a page missing in the target version
      // opens that version's start page instead of a 404.
      fetch(link.href, { method: "HEAD" })
        .then((response) => {
          location.href = response.ok ? link.href : target.href;
        })
        .catch(() => {
          location.href = target.href;
        });
    });
    return link;
  }
})();
