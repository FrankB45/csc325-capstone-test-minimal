# Git Gallery minimal fixture — North Pier Books

A public, self-contained static website with **20 linear commits** and **three pages at HEAD**.
It deliberately fits Git Gallery's current passive HTML/CSS/PNG dependency checker.

Repository: https://github.com/FrankB45/csc325-capstone-test-minimal

## Start testing

1. Start MongoDB, Django, and the worker in your capstone checkout.
2. Import **Git-Gallery-Minimal.postman_collection.json** into Postman.
3. Run **01 — Fetch commits and prepare selections** first. It records the actual full SHAs from your API.
4. Run **02 — Check compatibility**. Expect HTTP 200, overall_status accepted, and setup_available true.
5. Run **03 — Capture the homepage**. Expect HTTP 202 and total_captures 10.
6. The worker should eventually mark that job complete and save ten PNGs.

The collection defaults to http://127.0.0.1:8000. Change its base_url variable if needed.
A 202 response only confirms queueing. It does not confirm screenshot completion.
The current application does not yet expose the planned job-polling/image endpoints.
Use the returned job_id to inspect Job in Django's shell and check backend/screenshots/<job_id>/.

Run the worker from the capstone backend with:
~~~
python manage.py run_worker
~~~

A read-only job inspection in the Django shell:
~~~python
from git_gallery_app.models import Job
job = Job.objects.get(pk="PASTE_JOB_ID")
print(job.status)
for capture in job.captures:
    print(capture.position, capture.status, capture.error_message, capture.screenshot_path)
~~~

## Expected scenarios

Commit numbers below mean oldest-first positions, starting at 1.

| Scenario | Page | Selected commit numbers | Expected final result |
|---|---|---|---|
| Default selection | index.html | 1, 3, 5, 7, 9, 12, 14, 16, 18, 20 | complete; 10 successes |
| Mixed About history | about.html | 1, 6, 12, 14, 20 | partially_complete; 3 successes, 2 missing-page failures |
| All selected About versions missing | about.html | 1, 2, 3, 4, 5 | failed; 5 missing-page failures |
| Mixed Events history | events.html | 1, 9, 10, 18, 20 | partially_complete; 3 successes, 2 missing-page failures |
| Layout regression and repair | index.html | 11, 12, 13, 14 | complete; visibly cramped cards at 13 |
| Documentation-only pair | index.html | 7, 8 | complete; expected identical screenshots |
| Too many selected commits | index.html | first 11 | HTTP 400; no job should be created |
| Duplicate selection | index.html | 1, 1 | HTTP 400; no job should be created |
| Unknown SHA | index.html | forty zeroes | HTTP 400; no job should be created |

index.html exists in **all 20** commits.
about.html exists at **6–11 and 14–20**; it is absent at **1–5 and 12–13**.
events.html exists at **10–20**.

Missing-page tests work because each selected page exists in the current snapshot even though it is absent at particular older SHAs.

## Commit guide

| # | Change |
|---|---|
| 1 | Bare homepage |
| 2 | Ink-and-paper identity with local stylesheet |
| 3 | Three staff selections |
| 4 | Flexible bookshelf columns |
| 5 | Opening hours and location |
| 6 | About page and navigation |
| 7 | Original local PNG illustration |
| 8 | README only; no page changes |
| 9 | Terracotta accent palette |
| 10 | Events page |
| 11 | Sunday reading-circle announcement |
| 12 | About page temporarily removed; its navigation link is removed too |
| 13 | Deliberately cramped bookshelf layout |
| 14 | About page and comfortable layout restored |
| 15 | CSS comments only; no visual changes |
| 16 | Community noticeboard |
| 17 | Larger headline and stronger text contrast |
| 18 | Events page updated; homepage appearance unchanged |
| 19 | Local PNG favicon; page screenshot appearance unchanged |
| 20 | Test instructions, Postman collection, verifier, and ignore rules |

Expected identical homepage pairs under the same browser and viewport:
**7/8, 11/14, 14/15, 17/18, 18/19, and 19/20**.
These are fixture expectations, not a guarantee of byte-identical PNG encoding across different environments.
Commits 11/14 deliberately restore the earlier presentation. Commit 13 is the intentional visual regression.

## Compatibility constraints

The site contains:
- A regular root index.html at every commit.
- Native HTML and simple flat CSS declarations.
- System fonts and two original, deterministic PNG assets.
- All resources in the same repository, using relative paths.

It has no JavaScript, SVG, data URLs, web fonts, CSS variables, CSS functions, media queries, build step, external service, or runtime backend.
The Python verifier and Postman test scripts are tooling; the website never executes them.

## Verify the fixture locally

The basic history/link check uses only Python's standard library:
~~~
python3 tools/verify_fixture.py
~~~

For the actual Git Gallery dependency checker, use your capstone virtualenv Python:
~~~
/path/to/csc325-capstone/backend/.venv/bin/python tools/verify_fixture.py --backend /path/to/csc325-capstone/backend
~~~

This reads committed Git objects and substitutes local Git data for GitHub HTTP responses.
It checks all 20 revisions and every available HTML page against the current dependency checker.
It makes no database writes and does not claim to run the browser or queue worker.

Preview the latest site with:
~~~
python3 -m http.server 8001
~~~
Open http://127.0.0.1:8001/index.html.

The initial publication was checked against the capstone's unchanged dependency checker.
Treat the browser capture and final Job statuses as separate live acceptance checks.
Avoid adding commits casually: the numbered scenarios and 20-commit selection expectations depend on this controlled history.

All names, books, events, and addresses are fictional.

