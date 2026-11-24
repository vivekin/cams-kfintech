from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://www.camsonline.com/Distributors/Service-Requests/Distributor-Mailback-Services/Request-Mailback"
EMAIL = ""  # <-- change this
MAX_ATTEMPTS = 3

POPUP_CLOSE = "mat-dialog-container .close-icon"
EMAIL_INPUT = "#mat-input-0"
SUBMIT_BTN = "input.check-now-btn"
SESSION_CLICK_HERE = "h4.clicksession a.clickhere"  # "session is still active... click here"
LOGOUT_ICON = "mat-icon.logout"


def close_popup_if_present(page):
    try:
        page.wait_for_selector(POPUP_CLOSE, state="visible", timeout=8000)
        page.click(POPUP_CLOSE)
        page.wait_for_selector(POPUP_CLOSE, state="detached", timeout=5000)
        print("Popup banner closed")
    except PlaywrightTimeoutError:
        print("No popup banner found, continuing")
 
 
def try_login(page):
    """Fill email and submit. Returns True if logged in, False if an old session blocked it."""
    page.wait_for_selector(EMAIL_INPUT, state="visible", timeout=30000)
    page.fill(EMAIL_INPUT, EMAIL)
    print(f"Filled email: {EMAIL}")
 
    page.click(SUBMIT_BTN)
    print("Clicked submit")
 
    # Wait for whichever appears first: the logout icon (success) or the "click here" session link
    page.locator(f"{LOGOUT_ICON}, {SESSION_CLICK_HERE}").first.wait_for(
        state="visible", timeout=60000
    )
 
    if page.locator(SESSION_CLICK_HERE).is_visible():
        print("Previous session still active, ending it")
        page.click(SESSION_CLICK_HERE)
        return False
    return True
 
 
def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
 
        page.goto(URL, wait_until="domcontentloaded")
        close_popup_if_present(page)
 
        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"Login attempt {attempt}/{MAX_ATTEMPTS}")
            if try_login(page):
                break
        else:
            raise RuntimeError("Could not log in after ending the previous session")
 
        page.wait_for_timeout(3000)
        # Click logout
        page.click(LOGOUT_ICON)
        print("Clicked logout")
 
        # Brief pause to see the result (remove when running headless)
        page.wait_for_timeout(3000)
 
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
