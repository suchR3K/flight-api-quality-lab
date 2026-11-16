from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8000"


def open_app(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("#status")).to_have_text(
        "Search completed.",
        timeout=20_000,
    )
    expect(page.locator("#search-button")).to_be_enabled()


def click_and_wait(page: Page, button):
    with page.expect_response(
        lambda response: (
            "/flights?" in response.url
            and response.request.method == "GET"
        )
    ) as response_info:
        button.click()

    assert response_info.value.status == 200
    expect(page.locator("#search-button")).to_be_enabled(
        timeout=20_000
    )


def search_known_flights(page: Page):
    page.locator('[name="origin"]').fill("JFK")
    page.locator('[name="destination"]').fill("LAX")
    page.locator('[name="flight_date"]').fill("2025-06-01")
    page.locator('[name="carrier_code"]').fill("AA")

    click_and_wait(page, page.locator("#search-button"))

    expect(page.locator("#status")).to_have_text(
        "Search completed."
    )


def test_search_filters(page: Page):
    open_app(page)
    search_known_flights(page)

    rows = page.locator("#results tr")
    assert rows.count() > 0

    for row in rows.all():
        cells = row.locator("td")
        expect(cells).to_have_count(7)
        expect(cells.nth(1)).to_have_text("2025-06-01")
        expect(cells.nth(2)).to_have_text("AA")
        expect(cells.nth(4)).to_have_text("JFK")
        expect(cells.nth(5)).to_have_text("LAX")


def test_flight_details(page: Page):
    open_app(page)
    search_known_flights(page)

    row = page.locator("#results tr").first
    cells = row.locator("td")
    expected_values = [
        cells.nth(index).inner_text()
        for index in range(6)
    ]

    row.get_by_role("button").click()

    dialog = page.locator("#details-dialog")
    expect(dialog).to_be_visible()

    values = page.locator("#details-content dd")
    expect(values).to_have_text(
        expected_values,
        timeout=20_000,
    )

    dialog.get_by_role("button", name="Close", exact=True).click()
    expect(dialog).not_to_be_visible()


def test_empty_search(page: Page):
    open_app(page)

    page.locator('[name="flight_date"]').fill("2000-01-01")
    click_and_wait(page, page.locator("#search-button"))

    expect(page.locator("#status")).to_have_text(
        "No records match the selected filters."
    )
    expect(page.locator("#results")).to_contain_text(
        "No flights found."
    )
    expect(page.locator("#previous")).to_be_disabled()
    expect(page.locator("#next")).to_be_disabled()


def test_pagination(page: Page):
    open_app(page)

    page.locator('[name="limit"]').select_option("10")
    click_and_wait(page, page.locator("#search-button"))

    rows = page.locator("#results tr")
    expect(rows).to_have_count(10)
    expect(page.locator("#previous")).to_be_disabled()

    first_page_ids = rows.locator("td:first-child").all_text_contents()

    click_and_wait(page, page.locator("#next"))

    expect(rows).to_have_count(10)
    expect(page.locator("#previous")).to_be_enabled()

    second_page_ids = rows.locator("td:first-child").all_text_contents()
    assert set(first_page_ids).isdisjoint(second_page_ids)

    click_and_wait(page, page.locator("#previous"))

    expect(rows.locator("td:first-child")).to_have_text(first_page_ids)
    expect(page.locator("#previous")).to_be_disabled()
