from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # The app is running on port 5003
    page.goto("http://localhost:5003/auth/login")
    expect(page).to_have_title("Tradier Dashboard - Login")
    print(page.content())
    page.get_by_label("Email").fill("test@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click(force=True)
    page.wait_for_url("http://localhost:5003/dashboard", timeout=60000)


    # Check if login was successful
    if "login" in page.url:
        # Login failed, so register
        page.goto("http://localhost:5003/auth/register")
        expect(page).to_have_title("Tradier Dashboard - Register")

        # Register a new user
        page.get_by_label("Username").fill("testuser")
        page.get_by_label("Email").fill("test@example.com")
        page.get_by_label("Password").first.fill("password")
        page.get_by_label("Confirm Password").fill("password")
        page.get_by_role("button", name="Sign Up").click(force=True)
        page.wait_for_url("http://localhost:5003/auth/login", timeout=60000)


        # Login again
        page.goto("http://localhost:5003/auth/login")
        expect(page).to_have_title("Tradier Dashboard - Login")
        page.get_by_label("Email").fill("test@example.com")
        page.get_by_label("Password").fill("password")
        page.get_by_role("button", name="Login").click(force=True)
        page.wait_for_url("http://localhost:5003/dashboard", timeout=60000)


    # Go to the research page
    page.goto("http://localhost:5003/research")
    expect(page).to_have_title("Tradier Dashboard - Research")


    # Fill in the form
    page.get_by_label("Symbol").fill("AAPL")
    page.get_by_label("Period").select_option("365")
    page.get_by_role("button", name="Submit").click()

    # Wait for the chart to be rendered
    expect(page.locator("#plotly-chart")).to_be_visible(timeout=60000)

    # Take a screenshot
    page.screenshot(path="jules-scratch/verification/verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
