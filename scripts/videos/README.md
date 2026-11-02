# Tutorial videos

The explainer videos on the Tutorials page (tile gallery with category filter)
and the "Did you know?" pick of the day on top of every page are generated from
one catalog: `docs/tutorials/videos.yml`.

| Piece                                     | Role                                                             |
|-------------------------------------------|------------------------------------------------------------------|
| `docs/tutorials/videos.yml`               | Catalog: categories, videos, titles, teasers                     |
| `scripts/videos/sync-drive.py`            | Syncs the catalog with the Google Drive folder                   |
| `scripts/hooks/videos.py`                 | Renders the gallery where `<!-- sb:video-gallery -->` is placed  |
| `templates/main.html` (`announce` block)  | Pick-of-the-day bar, one video per calendar day                  |
| `docs/assets/javascripts/videos.js`       | Filter, player dialog, deep links                                |
| `docs/assets/stylesheets/videos.css`      | Styles                                                           |

## Uploading a video

The videos live in the shared Google Drive folder
<https://drive.google.com/drive/folders/1J0fuJrTZMu-HWLxYIfRN2ttCAE2zZp8G>, one
subfolder per category (`Core`, `File and Object`, `DR`, `Edge Clusters`).

1. Upload the MP4 into the category subfolder, named
   `<Category> <NN> - <Title>.mp4`, for example `Core 06 - Snapshots.mp4`.
   The number is the video's identity: uploading a new cut with the same
   number replaces the old one on the site (the newest file wins), and the
   old file can stay in the folder or be deleted.
2. Sync, either
   * in GitHub: *Actions → Sync Tutorial Videos → Run workflow*, which opens a
     pull request with the catalog changes, or
   * locally: `python3 scripts/videos/sync-drive.py` and commit the result.
3. Optionally polish the new entry in `videos.yml`: the title (taken from the
   file name), a `teaser` for the "Did you know?" bar, a `description` for the
   tile, and a `page` with the matching documentation.

Files must be shared "anyone with the link can view", which the folder
already passes on to new uploads.

## Tile design

Tiles do not use a frame of the video. Every tile is drawn the same way from
the category's color and icon, the number of the video, and its title. A new
category is added to `categories:` in `videos.yml` (with its Drive subfolder
name and a Material `icon`) and gets a color in `videos.css`
(`--sb-cat-<id>`, one value for light and one for dark mode).

## Other sources

An entry can use `youtube: <video id>` or a self-hosted `src:
assets/videos/<file>.mp4` instead of `drive_id`; the sync never touches those
entries. Self-hosted files are copied into every published version of the
documentation, so large or frequently changing videos are better kept on
Drive or YouTube.

## Notes

* Drive is a file share, not a video CDN: playback goes through the Drive
  preview player, and Google may throttle a file with heavy traffic. For the
  most-watched videos, an unlisted YouTube upload (`youtube:`) is the more
  robust source.
* The pick of the day is chosen in the browser from the local date, so it
  rotates daily without a rebuild. `pick: false` keeps a video out of it.
* Deep links: `tutorials/#video=<id>` opens a video, `tutorials/#category=<id>`
  pre-selects a filter.
