/*
 * Command Assistant (docs/assistant/index.md).
 *
 * Sends the request to the assistant API (assistant/ in this repository),
 * shows its progress from the Server-Sent Events stream, and renders the
 * answer: numbered steps with commands, copy buttons, and source links.
 * The question is mirrored into the URL as ?ask=... (?q= belongs to the site search), so answers can be linked.
 */
(function () {
  "use strict";

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  // Docs version from the site root (mike deploys to /<version>/).
  function docsVersion() {
    try {
      var scope = window.__md_scope ? window.__md_scope.pathname : "/";
      var seg = scope.replace(/^\/|\/$/g, "").split("/").pop();
      return seg || "latest";
    } catch (e) { return "latest"; }
  }

  function copyButton(code) {
    var b = el("button", "sb-assistant__copy md-icon", "Copy");
    b.type = "button";
    b.title = "Copy to clipboard";
    b.addEventListener("click", function () {
      navigator.clipboard.writeText(code).then(function () {
        b.textContent = "Copied";
        setTimeout(function () { b.textContent = "Copy"; }, 1500);
      });
    });
    return b;
  }

  function sourceLink(src, label) {
    if (!src || !src.url) return null;
    var a = el("a", "sb-assistant__source");
    a.href = src.url;
    a.textContent = (label || "Source") + ": " + (src.title || src.page) + (src.section ? " › " + src.section : "");
    return a;
  }

  function renderCommand(cmd) {
    var wrap = el("div", "sb-assistant__cmd");
    var head = el("div", "sb-assistant__cmd-head");
    var badge = el("span", "sb-assistant__badge " + (cmd.verified ? "is-verified" : "is-adapted"),
      cmd.verified ? "from the docs" : "adapted");
    badge.title = cmd.verified
      ? "Every line of this command appears verbatim in the documentation."
      : "This command is not a literal copy from the documentation. Check it against the linked page.";
    head.appendChild(el("span", "sb-assistant__lang", cmd.language || ""));
    head.appendChild(badge);
    head.appendChild(copyButton(cmd.code));
    var pre = el("pre");
    pre.appendChild(el("code", null, cmd.code));
    wrap.appendChild(head);
    wrap.appendChild(pre);
    return wrap;
  }

  function renderAnswer(box, data, ctx) {
    var a = data.answer || {};
    box.textContent = "";
    var article = el("div", "sb-assistant__answer md-typeset");
    if (a.title) article.appendChild(el("h2", null, a.title));
    if (a.summary) article.appendChild(el("p", "sb-assistant__summary", a.summary));

    if (a.status === "clarify" && a.question) {
      var q = el("div", "admonition question");
      q.appendChild(el("p", "admonition-title", "One question first"));
      q.appendChild(el("p", null, a.question));
      article.appendChild(q);
    }
    if (a.status === "not_covered") {
      var n = el("div", "admonition info");
      n.appendChild(el("p", "admonition-title", "Not covered by the documentation"));
      n.appendChild(el("p", null, "The documentation has no procedure for this request. The pages below are the closest match."));
      article.appendChild(n);
    }
    if (a.assumptions && a.assumptions.length) {
      var as = el("div", "sb-assistant__assumptions");
      as.appendChild(el("strong", null, "Assumptions: "));
      as.appendChild(document.createTextNode(a.assumptions.join(" · ")));
      article.appendChild(as);
    }
    if (a.prerequisites && a.prerequisites.length) {
      article.appendChild(el("h3", null, "Before you start"));
      var ul = el("ul");
      a.prerequisites.forEach(function (p) {
        var li = el("li", null, p.text + " ");
        var s = sourceLink(p.source, "See");
        if (s) li.appendChild(s);
        ul.appendChild(li);
      });
      article.appendChild(ul);
    }
    if (a.steps && a.steps.length) {
      var ol = el("ol", "sb-assistant__steps");
      a.steps.forEach(function (s) {
        var li = el("li", "sb-assistant__step");
        li.appendChild(el("h3", "sb-assistant__step-title", s.title));
        if (s.explanation) li.appendChild(el("p", null, s.explanation));
        (s.commands || []).forEach(function (c) { li.appendChild(renderCommand(c)); });
        if (s.note) li.appendChild(el("p", "sb-assistant__note", s.note));
        var src = sourceLink(s.source);
        if (src) li.appendChild(src);
        ol.appendChild(li);
      });
      article.appendChild(ol);
    }
    if (a.related && a.related.length) {
      article.appendChild(el("h3", null, "Related pages"));
      var rl = el("ul");
      a.related.forEach(function (r) {
        var li = el("li");
        var link = el("a", null, r.title);
        link.href = r.url;
        li.appendChild(link);
        rl.appendChild(li);
      });
      article.appendChild(rl);
    }
    article.appendChild(feedback(ctx));
    box.appendChild(article);
  }

  function feedback(ctx) {
    var f = el("div", "sb-assistant__feedback");
    f.appendChild(el("span", null, "Was this helpful?"));
    [["Yes", true], ["No", false]].forEach(function (opt) {
      var b = el("button", "md-button", opt[0]);
      b.type = "button";
      b.addEventListener("click", function () {
        fetch(ctx.api + "/feedback", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ question: ctx.question, version: ctx.version, helpful: opt[1], comment: "" }),
        }).catch(function () {});
        f.textContent = "Thanks for the feedback.";
      });
      f.appendChild(b);
    });
    return f;
  }

  function showError(box, message) {
    box.textContent = "";
    var e = el("div", "admonition failure md-typeset");
    e.appendChild(el("p", "admonition-title", "No answer"));
    e.appendChild(el("p", null, message));
    box.appendChild(e);
  }

  // Minimal SSE parser over a fetch() body (EventSource cannot POST).
  function readEvents(response, onEvent) {
    var reader = response.body.getReader();
    var decoder = new TextDecoder();
    var buf = "";
    function pump() {
      return reader.read().then(function (r) {
        if (r.done) return;
        buf += decoder.decode(r.value, { stream: true });
        var idx;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          var chunk = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          var data = chunk.split("\n").filter(function (l) { return l.indexOf("data:") === 0; })
            .map(function (l) { return l.slice(5).trim(); }).join("\n");
          if (data) {
            try { onEvent(JSON.parse(data)); } catch (e) {}
          }
        }
        return pump();
      });
    }
    return pump();
  }

  function init(root) {
    if (root.dataset.sbReady) return;
    root.dataset.sbReady = "1";
    var api = (root.dataset.api || "/api/assistant").replace(/\/$/, "");
    var form = root.querySelector("[data-sb-assistant-form]");
    var input = form.querySelector("input");
    var submit = form.querySelector("button[type=submit]");
    var progress = root.querySelector("[data-sb-assistant-progress]");
    var result = root.querySelector("[data-sb-assistant-result]");
    var sitekey = root.dataset.turnstile;
    var turnstileToken = "";
    var busy = false;

    if (sitekey) {
      window.sbAssistantTurnstile = function () {
        window.turnstile.render(root.querySelector("[data-sb-assistant-turnstile]"), {
          sitekey: sitekey, size: "flexible", appearance: "interaction-only",
          callback: function (t) { turnstileToken = t; },
          "expired-callback": function () { turnstileToken = ""; },
        });
      };
      var s = document.createElement("script");
      s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=sbAssistantTurnstile&render=explicit";
      s.async = true;
      document.head.appendChild(s);
    }

    root.querySelectorAll("[data-sb-assistant-examples] button").forEach(function (b) {
      b.addEventListener("click", function () { input.value = b.textContent; ask(); });
    });
    form.addEventListener("submit", function (e) { e.preventDefault(); ask(); });

    function ask() {
      var question = input.value.trim();
      if (!question || busy) return;
      busy = true;
      submit.disabled = true;
      var url = new URL(location.href);
      url.searchParams.set("ask", question);
      history.replaceState(null, "", url);
      var ctx = { api: api, question: question, version: docsVersion() };
      result.textContent = "";
      progress.textContent = "";
      progress.hidden = false;
      var steps = el("ul", "sb-assistant__progress-list");
      progress.appendChild(steps);
      function status(text) {
        var prev = steps.querySelector(".is-active");
        if (prev) prev.classList.remove("is-active");
        steps.appendChild(el("li", "is-active", text));
      }
      status("Sending your request");
      var answered = false;
      fetch(api + "/ask", {
        method: "POST",
        headers: { "content-type": "application/json", accept: "text/event-stream" },
        body: JSON.stringify({ question: question, version: ctx.version, turnstile: turnstileToken }),
      }).then(function (resp) {
        if (!resp.ok) {
          return resp.json().catch(function () { return {}; }).then(function (j) {
            throw new Error(j.error || "The assistant is not available right now.");
          });
        }
        return readEvents(resp, function (ev) {
          if (ev.type === "status") status(ev.text);
          else if (ev.type === "answer") { answered = true; renderAnswer(result, ev, ctx); }
          else if (ev.type === "error") { answered = true; showError(result, ev.message); }
        });
      }).then(function () {
        if (!answered) showError(result, "The connection ended before an answer arrived. Please try again.");
      }).catch(function (err) {
        showError(result, err.message || String(err));
      }).then(function () {
        busy = false;
        submit.disabled = false;
        progress.hidden = true;
        if (window.turnstile && sitekey) { try { window.turnstile.reset(); } catch (e) {} turnstileToken = ""; }
      });
    }

    var q = new URL(location.href).searchParams.get("ask");
    if (q) { input.value = q; ask(); }
  }

  function boot() {
    document.querySelectorAll("[data-sb-assistant]").forEach(init);
  }
  if (window.document$ && window.document$.subscribe) window.document$.subscribe(boot);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
