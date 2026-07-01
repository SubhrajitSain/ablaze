from flask import Flask, request, Response, redirect, stream_with_context, render_template, abort, session, jsonify
from urllib.parse import quote, unquote, urljoin
from bs4.element import Comment
from upstash_redis import Redis
from bs4 import BeautifulSoup
from ddgs import DDGS
import requests
import json
import time
import uuid
import os
ddgs = DDGS()

try:
    db = Redis.from_env()
except Exception:
    db = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY")
# proxy_sessions = {}
# proxy_last_used = {}

def check_or_create_session():
    if "proxy_id" not in session:
        session["proxy_id"] = str(uuid.uuid4())

    pid = session["proxy_id"]
    return pid

def get_proxy_session():
    pid = check_or_create_session()
    proxy = requests.Session()
    
    if not db:
        return proxy

    try:
        saved_cookies_json = db.get(f"cookies:{pid}")
        if saved_cookies_json:
            cookies_dict = json.loads(saved_cookies_json)
            proxy.cookies.update(cookies_dict)
    except Exception:
        pass

    return proxy

def save_proxy_session_cookies(proxy_session_obj):
    if "proxy_id" not in session or not db:
        return

    pid = session["proxy_id"]
    try:
        cookies_dict = proxy_session_obj.cookies.get_dict()
        db.set(f"cookies:{pid}", json.dumps(cookies_dict), ex=3600)
    except Exception:
        pass

# def cleanup():
#     now = time.time()
#
#     for pid in list(proxy_last_used):
#         if now - proxy_last_used[pid] > 3600:
#             proxy_sessions.pop(pid, None)
#             proxy_last_used.pop(pid, None)

def cleanup():
    pass

def clean_html_for_retro(html_content, base_url, use_pure_proxy_route=False, allowed_attrs=None, interactive_tags=None, replacements=None):
    if allowed_attrs is None: allowed_attrs = set()
    if interactive_tags is None: interactive_tags = []
    if replacements is None: replacements = {}
    if not html_content: return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    for tag in soup(['script', 'style']):
        tag.decompose()

    for tag in soup.find_all(True):
        if tag.name in interactive_tags:
            attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
            for attr in attrs_to_remove:
                del tag.attrs[attr]

            for attr in ['href', 'src', 'action']:
                if attr in tag.attrs:
                    original_url = tag.attrs[attr]
                    absolute_url = urljoin(base_url, original_url)
                    encoded_url = quote(absolute_url, safe="")

                    if use_pure_proxy_route:
                        tag.attrs[attr] = f"/api/ablaze/pure-proxy/{encoded_url}"
                    else:
                        tag.attrs[attr] = f"/api/ablaze/proxy/{encoded_url}"                        
                    if attr == "action" and "method" not in tag.attrs:
                        tag["method"] = "get"
        else:
            tag.attrs = {}

    for old_tag, new_tag_name in replacements.items():
        for tag in soup.find_all(old_tag):
            if new_tag_name == 'p':
                new_tag = soup.new_tag(new_tag_name)
                new_tag.extend(tag.contents)
                tag.replace_with(new_tag)
            elif new_tag_name == 'a' and 'action' in tag.attrs:
                tag.name = 'a'
                tag.attrs['href'] = tag.attrs['action']
                del tag.attrs['action']
            else:
                tag.name = new_tag_name

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    body_tag = soup.find('body')
    if body_tag:
        return ''.join(str(c) for c in body_tag.contents)
    else:
        return str(soup)

@app.route('/')
def index():
    cleanup()
    return render_template('index.html', query=request.args.get('q', ''), title="Ablaze")

@app.route('/lite')
def index_lite():
    cleanup()
    return render_template('index_lite.html', query=request.args.get('q', ''), title="Ablaze Lite")

@app.route('/go')
@app.route('/go<lite>')
def go(lite=None):
    cleanup()
    lite = lite == '-lite'
    url = request.args.get('url', '').strip()
    if not url:
        return render_template('error_lite.html' if lite else 'error.html', title="Proxy Error", error_message="A URL is needed to proxy. Please enter one.", note="Because proxying to an URL withought knowing the URL is like losing the full world map.")

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    return redirect(f"/proxy{"-lite" if lite else ""}/{quote(url, safe='')}")

@app.route('/go-pure')
@app.route('/go-pure<lite>')
def go_pure(lite=None):
    cleanup()
    lite = lite == '-lite'
    url = request.args.get('url', '').strip()
    if not url:
        return render_template('error_lite.html' if lite else 'error.html', title="Pure Proxy Error", error_message="A URL is needed to pure-proxy. Please enter one.", note="You can and should enter the URL you want to pure-proxy. It is free to do so.")

    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    return redirect(f"/pure-proxy{"-lite" if lite else ""}/{quote(url, safe='')}")

@app.route('/search')
@app.route('/search<lite>')
def search(lite=None):
    cleanup()
    lite = lite == '-lite'
    query = request.args.get('q', '').strip()
    if not query:
        return render_template('error_lite.html' if lite else 'error.html', title="Search Error", error_message="A search query is needed to perform a search.", note="Please enter a search query beforehand.")

    if not ddgs:
        return render_template('error_lite.html' if lite else 'error.html', title="Search Error", error_message="Search functionality is currently unavailable. [ddgs not found]", note="Please contact the maintainers and show this information.")

    try:
        #api_url = f"https://anw.is-a.dev/api/ddgs"
        #params = {"q": query, "r": 50}

        #proxy = get_proxy_session()
        #response = proxy.get(api_url, params=params, timeout=10)
        #response.raise_for_status()

        #results = response.json()
        
        results = ddgs.text(query=query, max_results=50, safesearch="off") # on | moderate | off, currently hardcoded to off to allow all results

        formatted_results = []
        for i, result in enumerate(results):
            title = result.get('title', 'No Title')
            href = result.get('href')
            body = result.get('body', 'No body snippet is available for this result.')
            formatted_results.append({
                'index': i + 1,
                'title': title,
                'proxy': f"/proxy{"-lite" if lite else ""}/{quote(href, safe='')}" if href else None,
                'body': body,
                'href': href if href else None
            })
        return render_template('search_results_lite.html' if lite else 'search_results.html', title=f"Results for '{query}'", query=query, results=formatted_results)
    except Exception as e:
        return render_template('error_lite.html' if lite else 'error.html', title="Search Error", error_message=f"Failed to perform search: {e}", query=( query if query else None ), note="We accidentally lost our magnifying glass. Try searching again later.")

@app.route('/proxy/<path:url>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.route('/proxy<lite>/<path:url>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def proxy(url, lite=None):
    cleanup()
    lite = lite == '-lite'
    url = unquote(url)
    if url.startswith("https:/") and not url.startswith("https://"):
        url = "https://" + url[7:]
    elif url.startswith("http:/") and not url.startswith("http://"):
        url = "http://" + url[6:]

    allowed_attrs = {
        'href', 'src', 'alt', 'action', 'method',
        'type', 'value', 'placeholder', 'name',
        'id', 'class', 'style', 'height', 'width',
        'color', 'bgcolor'
    }

    interactive_tags = ['a', 'img', 'form', 'input', 'link']

    replacements = {
        'div': 'p',
        'span': 'p',
        'header': 'p',
        'footer': 'p',
        'nav': 'p',
        'section': 'p',
        'article': 'p',
        'main': 'p',
        'aside': 'p',
        #'button': 'a',
    }

    try:
        target = url
        headers = { k: v for k, v in request.headers.items() if k.lower() != "host" }

        # block prevention
        headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers["Accept-Language"] = "en-US,en;q=0.9"

        proxy = get_proxy_session()
        if request.method == "GET":
            response = proxy.request(
                method=request.method,
                url=target,
                params=request.args,
                stream=True,
                timeout=10,
                headers=headers,
                allow_redirects=False
            )
        else:
            response = proxy.request(
                method=request.method,
                url=target,
                params=request.args,
                data=request.get_data(),
                files=request.files,
                stream=True,
                timeout=10,
                headers=headers,
                allow_redirects=False
            )
        save_proxy_session_cookies(proxy)
        if 300 <= response.status_code < 400:
            location = response.headers.get("Location")

            if location:
                location = urljoin(url, location)
                return redirect(f"/proxy{"-lite" if lite else ""}/" + quote(unquote(location), safe=""))
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()

        if 'text/html' not in content_type:
            return Response(
                response.content,
                status=response.status_code,
                content_type=response.headers.get("Content-Type")
            )

        html_content = response.text
        cleaned_html_body = clean_html_for_retro(html_content, url, False, allowed_attrs, interactive_tags, replacements)

        html = render_template('proxied_content_lite.html' if lite else 'proxied_content.html', title=f"Proxied: {url}", proxied_url=url, cleaned_body=cleaned_html_body)
        server_resp = Response(html)
        return server_resp

    except requests.exceptions.RequestException as e:
        error_message = f"Could not proxy URL: {url}<br>Error: {e}"
        return render_template('error_lite.html' if lite else 'error.html', title="Proxy Error", error_message=error_message, query=request.args.get('q', ''))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error_lite.html' if lite else 'error.html', title="Proxy Error", error_message=error_message, query=request.args.get('q', ''))

@app.route('/pure-proxy/<path:url>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.route('/pure-proxy<lite>/<path:url>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def pure_proxy(url, lite=None):
    cleanup()
    lite = lite == '-lite'
    url = unquote(url)
    if url.startswith("https:/") and not url.startswith("https://"):
        url = "https://" + url[7:]
    elif url.startswith("http:/") and not url.startswith("http://"):
        url = "http://" + url[6:]

    allowed_attrs = {
        'href', 'src', 'alt', 'action', 'method',
        'type', 'value', 'placeholder', 'name',
        'id', 'class', 'style', 'height', 'width',
        'color', 'bgcolor'
    }

    interactive_tags = ['a', 'img', 'form', 'input', 'link']

    replacements = {
        'div': 'p',
        'span': 'p',
        'header': 'p',
        'footer': 'p',
        'nav': 'p',
        'section': 'p',
        'article': 'p',
        'main': 'p',
        'aside': 'p',
        #'button': 'a',
    }

    try:
        target = url
        headers = { k: v for k, v in request.headers.items() if k.lower() != "host" }
        
        # block prevention
        headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers["Accept-Language"] = "en-US,en;q=0.9"

        proxy = get_proxy_session()
        if request.method == "GET":
            response = proxy.request(
                method=request.method,
                url=target,
                params=request.args,
                stream=True,
                timeout=10,
                headers=headers,
                allow_redirects=False
            )
        else:
            response = proxy.request(
                method=request.method,
                url=target,
                params=request.args,
                data=request.get_data(),
                files=request.files,
                stream=True,
                timeout=10,
                headers=headers,
                allow_redirects=False
            )
        save_proxy_session_cookies(proxy)
        if 300 <= response.status_code < 400:
            location = response.headers.get("Location")

            if location:
                location = urljoin(url, location)
                return redirect(f"/pure-proxy{"-lite" if lite else ""}/" + quote(unquote(location), safe=""))
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()

        if 'text/html' not in content_type:
            return Response(
                response.content,
                status=response.status_code,
                content_type=response.headers.get("Content-Type")
            )

        html_content = response.text
        cleaned_html_body = clean_html_for_retro(html_content, url, True, allowed_attrs, interactive_tags, replacements)
        server_resp = Response(cleaned_html_body)
        return server_resp

    except requests.exceptions.RequestException as e:
        error_message = f"Could not pure-proxy URL: {url}<br>Error: {e}"
        return render_template('error_lite.html' if lite else 'error.html', title="Pure Proxy Error", error_message=error_message, query=request.args.get('q', ''))
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        return render_template('error_lite.html' if lite else 'error.html', title="Pure Proxy Error", error_message=error_message, query=request.args.get('q', ''))

@app.route("/health")
def health_check():
    return jsonify({"status": "online"})

@app.route("/except/<int:status_code>")
def http_status_code_abort(status_code):
    abort(status_code)
    return render_template('error.html', title="Except Route Failed", error_message="The /except route failed to abort the connection."), 500

@app.route('/cdn-cgi/<path:path>', methods=["GET", "POST"])
def ignore_cloudflare_challenges(path):
    return "", 204

@app.route('/favicon.ico')
def favicon_bypass():
    return "", 204

@app.errorhandler(Exception)
def exception_handler(e):
    cleanup()
    return render_template('error.html', title="HTTP Error", error_message=e, note="Please contact ANW and give the report above."), 0

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
