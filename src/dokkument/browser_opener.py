"""
BrowserOpener - Manages opening URLs in the default browser
Supports Windows, Linux, and macOS with appropriate error handling
"""

import webbrowser
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
import platform


class BrowserOpener:
    """Manages opening URLs in the default system browser"""

    def __init__(self):
        self.platform = platform.system().lower()
        self._preferred_browsers = self._get_system_browsers()

    def _get_system_browsers(self) -> List[str]:
        """Returns a list of available browsers for the current system"""
        browsers = []

        if self.platform == "windows":
            # Windows - check common browsers
            browsers = ["firefox", "chrome", "msedge", "iexplore"]
        elif self.platform == "darwin":  # macOS
            # macOS - check common browsers
            browsers = ["safari", "firefox", "chrome", "opera"]
        else:  # Linux and other Unix
            # Linux - check common browsers
            browsers = ["firefox", "google-chrome", "chromium-browser", "opera"]

        # Filter only actually available browsers
        available_browsers = []
        for browser in browsers:
            if shutil.which(browser) or self._browser_exists(browser):
                available_browsers.append(browser)

        return available_browsers

    def _browser_exists(self, browser_name: str) -> bool:
        """Checks if a specific browser exists on the system"""
        try:
            if self.platform == "darwin":
                # On macOS check in Applications
                app_paths = [
                    f"/Applications/{browser_name.title()}.app",
                    "/Applications/Google Chrome.app"
                    if browser_name == "chrome"
                    else None,
                    "/Applications/Microsoft Edge.app"
                    if browser_name == "msedge"
                    else None,
                ]
                return any(Path(path).exists() for path in app_paths if path)

            if self.platform == "windows":
                # On Windows check common registry or known paths
                common_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    if browser_name == "chrome"
                    else None,
                    r"C:\Program Files\Mozilla Firefox\firefox.exe"
                    if browser_name == "firefox"
                    else None,
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                    if browser_name == "msedge"
                    else None,
                ]
                return any(Path(path).exists() for path in common_paths if path)

            # On Linux use which
            return shutil.which(browser_name) is not None

        except Exception:  # pylint: disable=broad-except
            return False


    def open_url(self, url: str, browser_name: Optional[str] = None) -> bool:
        """
        Opens a URL in the specified or default browser

        Args:
            url: URL to open
            browser_name: Specific browser name (optional)

        Returns:
            bool: True if the opening was successful, False otherwise
        """
        if not self._is_valid_url(url):
            print(f"Error: Invalid URL: {url}")
            return False

        try:
            if browser_name:
                return self._open_with_specific_browser(url, browser_name)
            return self._open_with_default_browser(url)

        except Exception as open_error:  # pylint: disable=broad-except
            print(f"Error opening URL {url}: {open_error}")
            return False

    def _is_valid_url(self, url: str) -> bool:
        """Checks if the URL is well-formed"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]
        except Exception:  # pylint: disable=broad-except
            return False

    def _open_with_default_browser(self, url: str) -> bool:
        """Opens the URL with the system's default browser"""
        try:
            # First attempt: use webbrowser (works in most cases)
            webbrowser.open(url)
            return True

        except Exception as webbrowser_error:  # pylint: disable=broad-except
            print(f"Error with webbrowser.open: {webbrowser_error}")

            # Second attempt: use system-specific commands
            try:
                if self.platform == "windows":
                    subprocess.run(["start", url], shell=True, check=True)
                elif self.platform == "darwin":
                    subprocess.run(["open", url], check=True)
                else:  # Linux and other Unix
                    subprocess.run(["xdg-open", url], check=True)

                return True

            except Exception as system_error:  # pylint: disable=broad-except
                print(f"Error with system command: {system_error}")
                return False

    def _open_with_specific_browser(self, url: str, browser_name: str) -> bool:
        """Opens the URL with a specific browser"""
        try:
            # First attempt: use webbrowser with the specified browser
            if self._try_webbrowser_open(browser_name, url):
                return True

            # Second attempt: use platform-specific commands
            return self._try_platform_specific_browser(browser_name, url)

        except Exception as browser_error:  # pylint: disable=broad-except
            print(f"Error opening with specific browser {browser_name}: {browser_error}")
            return False

    def _try_webbrowser_open(self, browser_name: str, url: str) -> bool:
        """Try to open URL using webbrowser module"""
        try:
            browser = webbrowser.get(browser_name)
            browser.open(url)
            return True
        except webbrowser.Error:
            return False

    def _try_platform_specific_browser(self, browser_name: str, url: str) -> bool:
        """Try to open URL using platform-specific browser commands"""
        browser_lower = browser_name.lower()
        if self.platform == "windows":
            return self._open_windows_browser(browser_lower, url)
        if self.platform == "darwin":
            return self._open_macos_browser(browser_lower, url)
        # Linux
        subprocess.run([browser_name, url], check=True)
        return True

    def _open_windows_browser(self, browser_name: str, url: str) -> bool:
        """Open browser on Windows"""
        windows_browsers = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "google-chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "msedge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        }
        browser_path = windows_browsers.get(browser_name)
        if browser_path:
            subprocess.run([browser_path, url], check=True)
            return True
        return False

    def _open_macos_browser(self, browser_name: str, url: str) -> bool:
        """Open browser on macOS"""
        macos_browsers = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "google-chrome": "Google Chrome",
            "firefox": "Firefox",
            "opera": "Opera",
        }
        app_name = macos_browsers.get(browser_name)
        if app_name:
            subprocess.run(["open", "-a", app_name, url], check=True)
            return True
        return False

    def open_multiple_urls(
        self,
        urls: List[str],
        browser_name: Optional[str] = None,
        delay_seconds: float = 0.5,
    ) -> List[bool]:
        """
        Opens multiple URLs

        Args:
            urls: List of URLs to open
            browser_name: Specific browser name (optional)
            delay_seconds: Delay between openings to avoid issues

        Returns:
            List[bool]: List of results for each URL
        """
        import time  # pylint: disable=import-outside-toplevel

        results = []
        for i, url in enumerate(urls):
            if i > 0 and delay_seconds > 0:
                time.sleep(delay_seconds)

            result = self.open_url(url, browser_name)
            results.append(result)

            if result:
                print(f"✔ Opened: {url}")
            else:
                print(f"✘ Failed: {url}")

        return results

    def get_available_browsers(self) -> List[str]:
        """Returns the list of available browsers on the system"""
        return self._preferred_browsers.copy()

    def test_browser_availability(self) -> dict:
        """
        Tests the availability of common browsers on the system

        Returns:
            dict: Dictionary with browsers as keys and availability as values
        """
        common_browsers = {
            "default": "Default system browser",
            "firefox": "Mozilla Firefox",
            "chrome": "Google Chrome",
            "safari": "Safari (only macOS)",
            "msedge": "Microsoft Edge",
            "opera": "Opera",
        }

        results = {}

        for browser_key, browser_name in common_browsers.items():
            if browser_key == "default":
                # Test the default browser
                test_result = self._test_default_browser()
                results[browser_name] = test_result
            else:
                # Test specific browsers
                if browser_key == "safari" and self.platform != "darwin":
                    results[browser_name] = False  # Safari only on macOS
                else:
                    results[browser_name] = browser_key in self._preferred_browsers

        return results

    def _test_default_browser(self) -> bool:
        """Tests if the default browser is available"""
        try:
            # Simple test without actually opening anything
            webbrowser.get()
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    def print_browser_info(self):
        """Prints information about available browsers"""
        print(f"Operating System: {platform.system()} {platform.release()}")
        print("Available browsers:")

        availability = self.test_browser_availability()
        for browser, available in availability.items():
            status = "✔ Available" if available else "✘ Not available"
            print(f"  {browser}: {status}")

        if self._preferred_browsers:
            print(
                f"\nPreferred browsers detected: {', '.join(self._preferred_browsers)}"
            )
        else:
            print(
                "\nNo specific browser detected, the system default will be used"
            )
