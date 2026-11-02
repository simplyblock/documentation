/*
 * Video gallery of the Tutorials section (rendered by scripts/hooks/videos.py).
 *
 * - category filter buttons, mirrored into the URL as #category=<id>
 * - player dialog for Google Drive, YouTube, and local MP4 videos,
 *   mirrored into the URL as #video=<id> (the link target of the pick bar
 *   in templates/main.html)
 */
(function () {
  "use strict";

  function hashParams() {
    var out = {};
    location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      var i = kv.indexOf("=");
      if (i > 0) out[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1));
    });
    return out;
  }

  function setHash(params) {
    var parts = Object.keys(params)
      .filter(function (k) { return params[k]; })
      .map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); });
    var url = location.pathname + location.search + (parts.length ? "#" + parts.join("&") : "");
    history.replaceState(null, "", url);
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function init(root) {
    var buttons = Array.prototype.slice.call(root.querySelectorAll("[data-sb-filter]"));
    var tiles = Array.prototype.slice.call(root.querySelectorAll("[data-sb-video]"));
    var current = { category: "", video: "" };

    /* Filter */
    function filter(category) {
      if (!buttons.some(function (b) { return b.dataset.sbFilter === category; })) category = "all";
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.sbFilter === category));
      });
      tiles.forEach(function (t) {
        t.hidden = category !== "all" && t.dataset.sbCategory !== category;
      });
      current.category = category === "all" ? "" : category;
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        filter(b.dataset.sbFilter);
        setHash(current);
      });
    });

    /* Player dialog */
    var dialog = el("dialog", "sb-player");
    dialog.setAttribute("aria-label", "Video player");
    var head = el("div", "sb-player__head");
    var title = el("h2", "sb-player__title");
    var close = el("button", "sb-player__close md-icon");
    close.type = "button";
    close.setAttribute("aria-label", "Close");
    close.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>';
    head.appendChild(title);
    head.appendChild(close);
    var frame = el("div", "sb-player__frame");
    var foot = el("div", "sb-player__foot");
    dialog.appendChild(head);
    dialog.appendChild(frame);
    dialog.appendChild(foot);
    document.body.appendChild(dialog);

    function open(tile) {
      var a = tile.querySelector("a");
      var d = a.dataset;
      title.textContent = d.sbTitle;
      dialog.dataset.sbCategory = tile.dataset.sbCategory;
      frame.textContent = "";
      foot.textContent = "";
      if (d.sbKind === "file") {
        var video = el("video");
        video.controls = true;
        video.autoplay = true;
        video.preload = "metadata";
        if (d.sbPoster) video.poster = d.sbPoster;
        var source = el("source");
        source.src = d.sbSrc;
        source.type = "video/mp4";
        video.appendChild(source);
        frame.appendChild(video);
      } else {
        var iframe = el("iframe");
        iframe.src = d.sbEmbed;
        iframe.title = d.sbTitle;
        iframe.allow = "autoplay; fullscreen; encrypted-media; picture-in-picture";
        iframe.allowFullscreen = true;
        iframe.referrerPolicy = "strict-origin-when-cross-origin";
        frame.appendChild(iframe);
      }
      var category = tile.querySelector(".sb-video__category");
      if (category) foot.appendChild(el("span", "sb-player__category", category.textContent));
      if (d.sbPage) {
        var more = el("a", "sb-player__more", "Read the tutorial");
        more.href = d.sbPage;
        foot.appendChild(more);
      }
      var ext = el("a", "sb-player__external", d.sbKind === "file" ? "Download" : "Open in a new tab");
      ext.href = a.getAttribute("href");
      ext.target = "_blank";
      ext.rel = "noopener";
      foot.appendChild(ext);

      current.video = tile.dataset.sbVideo;
      setHash(current);
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }

    function shut() {
      if (dialog.open) dialog.close();
    }
    dialog.addEventListener("close", function () {
      frame.textContent = ""; /* stops playback */
      current.video = "";
      setHash(current);
    });
    close.addEventListener("click", shut);
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) shut(); /* click on the backdrop */
    });

    tiles.forEach(function (t) {
      t.querySelector("a").addEventListener("click", function (e) {
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        open(t);
      });
    });

    function byId(id) {
      for (var i = 0; i < tiles.length; i++) if (tiles[i].dataset.sbVideo === id) return tiles[i];
      return null;
    }

    /* Deep links */
    function fromHash() {
      var p = hashParams();
      filter(p.category || "all");
      var tile = p.video && byId(p.video);
      if (tile && !dialog.open) {
        tile.hidden = false;
        open(tile);
      }
    }
    fromHash();
    window.addEventListener("hashchange", fromHash);
  }

  function boot() {
    var root = document.querySelector("[data-sb-videos]");
    if (root) init(root);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
