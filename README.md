# shakeitup.uwo.ca → Western Cascade template

Everything needed to rebuild Project Shake-It-Up in Western's new Cascade 2025 template. It keeps all the content, removes dead links, and improves accessibility, as Dr. Block asked.

| Folder or file | What it's for |
|---|---|
| `content/` | One file per page, matching the old site's structure (29 pages). Open a page in Cascade, switch the editor to **Source / HTML**, and paste the matching file in. |
| `files/` | All 21 images and PDFs. Upload them to the site's `files` folder in Cascade; the pages already link to them there. |
| `LINK-REPORT.md` | Every link that was removed, updated, or kept, and why. |
| `preview/` | A local preview of the migrated content. To view it, run `python3 -m http.server 8090 -d preview` and open http://localhost:8090. |

Order of steps: Dr. Block requests the new template through the link Diana sent. Then submit an SSTS ticket asking for edit access to the old and new sites, and build the pages above.

To regenerate everything from the live site, run `build_migration.py` and then `make_preview.py`.
