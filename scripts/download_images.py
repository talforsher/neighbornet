#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import pathlib
import argparse
import mimetypes
from urllib.parse import unquote, urlparse
import subprocess

try:
    import requests
except Exception as e:
    print("This script requires the 'requests' package. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets" / "images"

IMG_TAG_RE = re.compile(r"<img[^>]+src=\"([^\"]+)\"", re.IGNORECASE)


def page_dir_for_url(html_path: pathlib.Path) -> pathlib.Path:
    # For a page like foo/index.html, save under foo/images/
    # For root index.html, save under assets/root/images/
    if html_path.name == "index.html" and html_path.parent != ROOT:
        return html_path.parent / "images"
    if html_path == ROOT / "index.html":
        return ROOT / "assets" / "root" / "images"
    # Fallback
    return html_path.parent / "images"


def iter_html_files():
    for p in ROOT.rglob("*.html"):
        yield p


def split_candidates(src: str):
    # Normalize encoded pipes to real pipes, then split
    s = src.replace("%7C", "|")
    parts = [x.strip() for x in s.split("|") if x.strip()]
    return parts if parts else [src]


def is_http_url(u: str) -> bool:
    return u.startswith("http://") or u.startswith("https://")


def sanitize_filename_from_url(u: str) -> str:
    parsed = urlparse(u)
    name = os.path.basename(parsed.path)
    name = unquote(name)
    if not name:
        # fallback to hash if no basename
        h = hashlib.sha256(u.encode("utf-8")).hexdigest()[:16]
        return f"img-{h}"
    return name


def ensure_ext(filename: str, content_type: str) -> str:
    # Keep existing ext if present; otherwise infer from content-type
    base, ext = os.path.splitext(filename)
    if ext:
        return filename
    ext_guess = mimetypes.guess_extension(content_type or "") or ""
    if ext_guess:
        return base + ext_guess
    return filename


def collect_image_urls():
    urls = []
    for html_path in iter_html_files():
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        for m in IMG_TAG_RE.finditer(text):
            src = m.group(1)
            for candidate in split_candidates(src):
                if is_http_url(candidate):
                    urls.append(candidate)
    # Dedupe preserving order
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def replace_host(url: str, prefer_host: str | None) -> str:
    if not prefer_host:
        return url
    try:
        p = urlparse(url)
        # Only rewrite typical WordPress uploads, otherwise keep original
        if p.path.startswith("/wp-content/uploads/"):
            p = p._replace(netloc=prefer_host)
            return p.geturl()
    except Exception:
        return url
    return url


def download_with_curl(url: str, host: str, ip: str, follow_redirects: bool = False) -> bytes | None:
    # Use curl to connect to the IP while sending SNI/Host for the domain
    # If follow_redirects is False, we try to detect 30x; but for image fetch, we need 200
    cmd = [
        "curl", "-sS", "--fail", "--show-error",
        "--user-agent", "Mozilla/5.0 (compatible; ImageFetcher/1.0)",
        "--resolve", f"{host}:443:{ip}",
        url,
    ]
    if follow_redirects:
        cmd.insert(3, "-L")
    try:
        data = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=20)
        return data
    except subprocess.CalledProcessError:
        return None
    except Exception:
        return None


def download_one(session: requests.Session, url: str, prefer_host: str | None, curl_host: str | None, curl_ip: str | None, out_dir: pathlib.Path | None = None) -> tuple[str, str] | None:
    # We will follow redirects (307/301/etc.) to successfully download.
    # Bypassing the redirect at the origin host is not generally possible if the server enforces it.
    try:
        preferred_url = replace_host(url, prefer_host)
        # Try requests first with redirects (most reliable)
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ImageFetcher/1.0)"}
        r = session.get(preferred_url, timeout=20, allow_redirects=True, headers=headers)
        if r.status_code == 200 and r.content:
            filename = sanitize_filename_from_url(url)
            filename = ensure_ext(filename, r.headers.get("Content-Type", ""))
            target_dir = out_dir or ASSETS_DIR
            target_dir.mkdir(parents=True, exist_ok=True)
            out_path = target_dir / filename
            with open(out_path, "wb") as f:
                f.write(r.content)
            return url, str(out_path.relative_to(ROOT))

        # If failed and curl host/ip provided, try curl with --resolve
        if curl_host and curl_ip:
            blob = download_with_curl(preferred_url, curl_host, curl_ip, follow_redirects=False)
            if not blob:
                # last attempt with -L
                blob = download_with_curl(preferred_url, curl_host, curl_ip, follow_redirects=True)
            if blob:
                filename = sanitize_filename_from_url(url)
                filename = ensure_ext(filename, r.headers.get("Content-Type", "")) if 'r' in locals() else filename
                target_dir = out_dir or ASSETS_DIR
                target_dir.mkdir(parents=True, exist_ok=True)
                out_path = target_dir / filename
                with open(out_path, "wb") as f:
                    f.write(blob)
                return url, str(out_path.relative_to(ROOT))
        return None
    except Exception:
        return None


def rewrite_html(mapping: dict[str, str]):
    # Replace occurrences of each remote URL (and its encoded form) with local path
    for html_path in iter_html_files():
        original = html_path.read_text(encoding="utf-8", errors="ignore")
        updated = original
        for remote, local in mapping.items():
            enc = remote.replace("|", "%7C")
            updated = updated.replace(remote, "/" + local)
            updated = updated.replace(enc, "/" + local)
        if updated != original:
            html_path.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Download and rewrite image URLs to local assets.")
    parser.add_argument("--list", action="store_true", help="List collected image URLs and exit")
    parser.add_argument("--download", action="store_true", help="Download images to assets/images/")
    parser.add_argument("--rewrite", action="store_true", help="Rewrite HTML to use local images")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of images to process (0 = all)")
    parser.add_argument("--offset", type=int, default=0, help="Offset to start from")
    parser.add_argument("--prefer-host", dest="prefer_host", default=None, help="Prefer fetching from this host (e.g., zxzfhpdm.elementor.cloud)")
    parser.add_argument("--curl-resolve-ip", dest="curl_resolve_ip", default=None, help="Optional IP to pair with --prefer-host using curl --resolve for fetch")
    args = parser.parse_args()

    urls = collect_image_urls()
    if args.list or (not args.download and not args.rewrite):
        print(f"Found {len(urls)} image URL candidates.")
        for u in urls[:20]:
            print(u)
        if len(urls) > 20:
            print(f"… and {len(urls) - 20} more")
        return 0

    mapping: dict[str, str] = {}
    if args.download:
        session = requests.Session()
        subset = urls[args.offset: args.offset + args.limit] if args.limit else urls[args.offset:]
        # Build a quick index of url -> page path that referenced it (first match used)
        url_to_page: dict[str, pathlib.Path] = {}
        for html_path in iter_html_files():
            text = html_path.read_text(encoding="utf-8", errors="ignore")
            for m in IMG_TAG_RE.finditer(text):
                src = m.group(1)
                for cand in split_candidates(src):
                    if is_http_url(cand) and cand not in url_to_page:
                        url_to_page[cand] = html_path

        for u in subset:
            page_path = url_to_page.get(u)
            out_dir = page_dir_for_url(page_path) if page_path else None
            res = download_one(session, u, args.prefer_host, args.prefer_host, args.curl_resolve_ip, out_dir)
            if res:
                remote, local = res
                mapping[remote] = local

    if args.rewrite:
        # If no new mapping from this run, still try to remap previously downloaded filenames by name
        if not mapping:
            for u in urls:
                fname = sanitize_filename_from_url(u)
                loc = ASSETS_DIR / fname
                if loc.exists():
                    mapping[u] = str(loc.relative_to(ROOT))
        rewrite_html(mapping)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


