"""Browser E2E for the board's full-view result navigation (view only).

Starts its OWN scratch server on a free port over a scratch corpus whose
group sizes are known, drives the full view in headless Chrome and checks:
sort by group size over the WHOLE result, reverse, one bounded page at a
time (no accumulation), verbose groups collapsed by default and opened step
by step, keyboard use and focus. Never touches a running server.

    uv run --no-project --with playwright \
        python scripts/e2e_board_navigation.py [shots_dir]

Needs Google Chrome (``channel="chrome"``) and ``uv`` on PATH.
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

REPO = Path(__file__).resolve().parent.parent
QUERY = "run(field(kind, retry)){3,} |> during(1m)"
# bursts of "retry" events become one group each: 130 groups, sizes 3..7
# except these (index -> size). 150 sits on page 2 of the stored order.
SPECIAL = {7: 40, 29: 25, 77: 150, 100: 12}
GROUPS = 130
TOP_BY_SIZE = 78  # group number (1-based, stored position) of the 150-event burst


def build_corpus(path: Path) -> None:
    docs, t, i = [], 1_700_000_000, 0
    for b in range(GROUPS):
        for k in range(SPECIAL.get(b, 3 + b % 5)):
            i, t = i + 1, t + 20
            docs.append(
                {
                    "id": i,
                    "agent": f"agent{b % 5}",
                    "kind": "retry",
                    "timestamp": t,
                    "text": f"burst {b} retry {k}",
                }
            )
        i, t = i + 1, t + 7200
        docs.append(
            {
                "id": i,
                "agent": "sys",
                "kind": "idle",
                "timestamp": t,
                "text": f"quiet after burst {b}",
            }
        )
    path.write_text("\n".join(json.dumps(d) for d in docs))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def http(url: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(  # noqa: S310 - http to the scratch server
        url,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            "X-PrismQL-Client": "e2e-board-nav",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        return json.loads(r.read())


def check(cond: bool, what: str) -> None:
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        raise SystemExit(f"E2E failed: {what}")


def focus_key(page: Page) -> str | None:
    return page.evaluate(
        "document.activeElement && document.activeElement.dataset.fkey || null"
    )


def first_group(page: Page) -> str:
    return page.locator("#full .gnav .gitem").first.locator("b").first.inner_text()


def run(page: Page, base: str, shots: Path) -> None:
    requests: list[str] = []
    errors: list[str] = []
    page.on(
        "request", lambda r: requests.append(r.url) if "/results/" in r.url else None
    )
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(
        "**/*",
        lambda route: (
            route.continue_() if route.request.url.startswith(base) else route.abort()
        ),
    )
    http(f"{base}/evaluate", {"query": QUERY})  # an older entry for ←/→ to reach
    res = http(f"{base}/evaluate", {"query": QUERY})
    rid = res["result_id"]
    page.goto(f"{base}/board/")
    row = page.locator("#journal-list .row").first
    row.wait_for()
    row.dblclick()
    full = page.locator("#full")
    expect(full).to_be_visible()
    expect(full.locator(".gnav .gitem").first).to_be_visible()

    # --- controls and the default view
    check(full.locator("select[data-fkey=sort]").count() == 1, "sort select is there")
    check(
        full.locator("button[data-fkey=reverse]").count() == 1,
        "reverse button is there",
    )
    check(
        full.locator("button[data-fkey=prev]").is_disabled(), "Prev disabled on page 1"
    )
    check(
        full.locator(".fpage").inner_text() == "Page 1 of 3",
        "page indicator reads Page 1 of 3",
    )
    check(
        "1–50 of 130" in full.locator(".fnote").inner_text(),
        "note names the range of the whole result",
    )
    check(first_group(page) == "group 1", "default order is the stored order")
    check(
        full.locator("input[type=search]").get_attribute("placeholder")
        == "Filter this page",
        "the filter says it reaches this page",
    )
    check(
        full.locator(".gnav .gitem").count() == 50,
        "one page of 50 groups, not the result",
    )
    page.screenshot(path=str(shots / "01-default.png"))

    # --- keyboard: the controls keep their own arrows
    counter = full.locator(".fhead").get_by_text(re.compile(r"^\d+ of \d+$"))
    check(counter.inner_text() == "1 of 2", "two journal entries, the newest open")
    sort = full.locator("select[data-fkey=sort]")
    sort.focus()
    page.keyboard.press("ArrowDown")  # timeline view: used to move the group nav
    check(
        full.locator(".gnav .gitem.on b").inner_text() == "group 1",
        "ArrowDown on the Sort select does not move the group selection",
    )
    page.keyboard.press("ArrowRight")
    check(counter.inner_text() == "1 of 2", "ArrowRight on the Sort select stays put")
    sort.press("L")  # typeahead: "Largest groups first"
    expect(full.locator(".fpage")).to_have_text("Page 1 of 3")
    check(sort.input_value() == "size", "the Sort select is operable from the keyboard")
    check(focus_key(page) == "sort", "focus stays on the Sort select after it changes")
    sort.press("O")  # back to "Original order"
    check(sort.input_value() == "position", "and back by keyboard")
    expect(full.locator(".gnav .gitem").first).to_contain_text("group 1")
    nxt = full.locator("button[data-fkey=next]")
    nxt.focus()
    page.keyboard.press("ArrowRight")
    check(
        counter.inner_text() == "1 of 2", "ArrowRight on Next does not leave the result"
    )
    check(
        full.locator(".fpage").inner_text() == "Page 1 of 3", "and does not page either"
    )
    nxt.press("ArrowLeft")
    check(counter.inner_text() == "1 of 2", "ArrowLeft on a pager button stays put")

    # --- a verbose group is collapsed by default, opens step by step, folds back
    full.locator(".gnav .gitem", has_text="group 8").first.click()
    check(
        full.locator(".gdetail .tev").count() == 3,
        "verbose group (40 events) starts as a 3-event preview",
    )
    toggle = full.locator("button[data-fkey='grp-more-top:7']")
    check(toggle.inner_text() == "Show all 40 events", "toggle names what it will show")
    check(
        toggle.get_attribute("aria-expanded") == "false",
        "toggle is aria-expanded=false",
    )
    toggle.focus()
    page.keyboard.press("Enter")
    check(
        full.locator(".gdetail .tev").count() == 40,
        "Enter on the toggle opens all 40 events",
    )
    check(
        focus_key(page) is not None and focus_key(page).startswith("grp-"),
        "focus stays on a group control",
    )
    full.locator("button[data-fkey='grp-close-top:7']").click()
    check(
        full.locator(".gdetail .tev").count() == 3, "collapse goes back to the preview"
    )
    page.screenshot(path=str(shots / "02-collapsed-group.png"))
    full.locator(".gnav .gitem", has_text="group 78").count()  # not on this page: no-op

    # --- next page replaces, never accumulates
    nxt.focus()
    page.keyboard.press("Enter")
    expect(full.locator(".fpage")).to_have_text("Page 2 of 3")
    expect(full.locator(".gnav .gitem").first).to_be_visible()  # the page has loaded
    check(first_group(page) == "group 51", "page 2 starts at group 51")
    check(
        full.locator(".gnav .gitem").count() == 50,
        "still 50 groups in the DOM after paging",
    )
    check(focus_key(page) == "next", "keyboard focus stays on Next across the rebuild")
    check(
        "51–100 of 130" in full.locator(".fnote").inner_text(), "note follows the page"
    )
    check(
        any("offset=50" in u for u in requests),
        "page 2 was a single request at offset 50",
    )
    check(
        not any("limit=100" in u or "limit=150" in u for u in requests),
        "no growing-limit request",
    )
    page.screenshot(path=str(shots / "03-page-2.png"))

    # --- jump, and the ends
    jump = full.locator("input[data-fkey=jump]")
    jump.fill("3")
    jump.press("Enter")
    expect(full.locator(".fpage")).to_have_text("Page 3 of 3")
    expect(full.locator(".gnav .gitem")).to_have_count(30)
    check(
        full.locator(".gnav .gitem").count() == 30, "last page holds the last 30 groups"
    )
    check(
        full.locator("button[data-fkey=next]").is_disabled(),
        "Next disabled on the last page",
    )
    full.locator("button[data-fkey=prev]").click()
    expect(full.locator(".fpage")).to_have_text("Page 2 of 3")
    expect(full.locator(".gnav .gitem")).to_have_count(50)

    # --- sort by size covers the WHOLE result, not the loaded page
    full.locator("select[data-fkey=sort]").select_option("size")
    expect(full.locator(".fpage")).to_have_text("Page 1 of 3")
    expect(full.locator(".gnav .gitem").first).to_contain_text("150 events")
    check(
        first_group(page) == f"group {TOP_BY_SIZE}",
        "largest group (stored position 78, past the first stored page) comes first",
    )
    check(
        "150 events" in full.locator(".gnav .gitem").first.inner_text(),
        "its size shows in the nav",
    )
    api = http(f"{base}/results/{rid}?order=size&limit=50&hydrate=false")
    shown = [
        int(t.split()[-1]) for t in full.locator(".gnav .gitem b").all_inner_texts()
    ]
    check(
        shown == [i + 1 for i in api["indices"]],
        "UI order equals the server's whole-result size order",
    )
    check(
        shown[:2] == [78, 8] and shown[2] == 30,
        "sizes 150, 40, 25 lead (group numbers stay the stored ones)",
    )
    page.screenshot(path=str(shots / "04-sorted-by-size.png"))

    # --- reverse flips whichever order is shown
    full.locator("button[data-fkey=reverse]").click()
    expect(full.locator("button[data-fkey=reverse]")).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(full.locator(".gnav .gitem").first).to_contain_text("3 events")
    api = http(f"{base}/results/{rid}?order=size&reverse=true&limit=50&hydrate=false")
    shown = [
        int(t.split()[-1]) for t in full.locator(".gnav .gitem b").all_inner_texts()
    ]
    check(
        shown == [i + 1 for i in api["indices"]],
        "reversed UI order equals the server's",
    )
    check(
        "3 events" in full.locator(".gnav .gitem").first.inner_text(),
        "smallest groups first when reversed",
    )
    full.locator("button[data-fkey=reverse]").click()
    full.locator("select[data-fkey=sort]").select_option("position")
    expect(full.locator(".gnav .gitem").first).to_contain_text("group 1")
    check(first_group(page) == "group 1", "back to the stored order")

    # --- table: verbose groups collapsed by default, bounded DOM
    full.get_by_role("button", name="Table").click()
    rows = full.locator(".tbl .tr:not(.th)")
    collapsed = rows.count()
    check(
        full.locator(".tbl .tr.tmore").count() >= 2, "verbose groups carry a toggle row"
    )
    check(collapsed < 400, f"table page is bounded ({collapsed} rows for 50 groups)")
    full.locator("button[data-fkey=all-open]").click()
    opened = full.locator(".tbl .tr:not(.th)").count()
    check(
        opened > collapsed,
        f"Expand all opens the verbose groups ({collapsed} -> {opened} rows)",
    )
    full.locator("button[data-fkey=all-close]").click()
    check(
        full.locator(".tbl .tr:not(.th)").count() == collapsed,
        "Collapse all folds them back",
    )
    page.screenshot(path=str(shots / "05-table.png"))

    # --- raw lines are numbered by their place in the result, not the page
    full.get_by_role("button", name="Raw JSON").click()
    full.locator("button[data-fkey=next]").click()
    expect(full.locator(".fpage")).to_have_text("Page 2 of 3")
    expect(full.locator(".raw .ln")).to_have_count(50)
    check(
        full.locator(".raw .ln .no").first.inner_text() == "51",
        "raw line numbers continue across pages",
    )
    check(full.locator(".raw .ln").count() == 50, "raw shows one page")

    # --- the filter reaches the page shown, and says so
    full.get_by_role("button", name="Timeline").click()
    full.locator("input[type=search]").fill("burst 60 ")
    check(
        "on this page match" in full.locator(".fnote").inner_text(),
        "filter note says it covers this page",
    )
    full.locator("input[type=search]").fill("")

    # --- a whole-DOM bound, and no script errors
    nodes = page.evaluate("document.querySelectorAll('#full *').length")
    check(nodes < 4000, f"full view DOM stays bounded ({nodes} elements)")
    check(not errors, f"no page errors {errors}")
    page.screenshot(path=str(shots / "06-final.png"))


def main() -> None:
    shots = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else tempfile.mkdtemp(prefix="prismql-e2e-nav-")
    )
    shots.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="prismql-e2e-nav-srv-"))
    build_corpus(work / "events.jsonl")
    port = free_port()
    (work / "prismql.toml").write_text(
        "\n".join(
            [
                "[server]",
                'host = "127.0.0.1"',
                f"port = {port}",
                "max_results = 50",
                "rate_limit_per_minute = 100000",
                f'results_dir = "{work}/out"',
                'default_corpus = "e2e"',
                "",
                "[corpora.e2e]",
                'data = "events.jsonl"',
                "",
                "[corpora.e2e.board]",
                'kind = "kind"',
                'actor = "agent"',
                "",
            ]
        )
    )
    server = subprocess.Popen(  # noqa: S603 - fixed argv, scratch config
        ["uv", "run", "prismql-server", "--config", str(work / "prismql.toml")],  # noqa: S607
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                http(f"{base}/health")
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise SystemExit("scratch server did not come up")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": 1500, "height": 900})
            try:
                run(page, base, shots)
            finally:
                browser.close()
        print(f"all checks passed; screenshots in {shots}")
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    main()
