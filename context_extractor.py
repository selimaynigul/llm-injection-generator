import requests
from bs4 import BeautifulSoup

def extract_context_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
    except Exception as e:
        return f"[!] Failed to fetch the URL: {e}"

    soup = BeautifulSoup(html, "html.parser")

    forms = soup.find_all("form")
    inputs = soup.find_all("input")
    scripts = soup.find_all("script")
    iframes = soup.find_all("iframe")
    objects = soup.find_all("object")

    input_types = list({inp.get("type", "text") for inp in inputs})
    action_paths = [form.get("action", "N/A") for form in forms]

    context_parts = [
        f"[+] URL: {url}",
        f"[+] Number of forms: {len(forms)}",
        f"[+] Form actions: {action_paths}",
        f"[+] Input types: {input_types}",
        f"[+] Inline scripts: {len([s for s in scripts if not s.get('src')])}",
        f"[+] External scripts: {len([s for s in scripts if s.get('src')])}",
        f"[+] iframe count: {len(iframes)}",
        f"[+] object count: {len(objects)}"
    ]

    return "\n".join(context_parts)
