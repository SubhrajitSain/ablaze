# 🔥 Ablaze

A simple search engine + website proxy so that you can browse the modern web on browsers from the late 20th century.  

> [!WARNING]
> Turn of JavaScript in your browser or else you may get JS errors due to the Cloudflare challenge script.  

**Website Links:**  

- http://dih.pythonanywhere.com/ (HTTP/HTTPS, slowest)
- https://ablaze-cyan.vercel.app/ (only HTTPS and modern TLS/SSL, may not work on old browsers, fastest)
- https://ablaze.anw.is-a.dev/ (same as above, but custom domain, coming soon, fastest)

It uses the Python DDGS module for getting search results (aggregated) and a custom-made page stripper based proxy service so that you can freely browse the current, modern Internet on super old browsers. It also comes with a lite mode (to use, visit the `/lite` route!) for even more compatibility. It has both HTTP and HTTPS support, thanks to Vercel!  

Ablaze stores your cookies on Upstash for a maximum duration of 1 hour after inactivity to keep you logged into sites using the proxy.

## ✅ Tested On:

- (Oracle VirtualBox VM) Windows XP Pro SP3 64bit /w K-Meleon 76.4 - `OK`
- (DOSBox-X VM) Windows 98 SE /w MS IE 5.0 - `OK`
- Windows 10 Pro 22H2 64bit /w Perplexity Comet, Google Chrome, Mozilla Firefox - `OK`
- Android 8.1 /w Google Chrome - `OK`
- [MrrpOS GNU/Linux](https://anw.is-a.dev/mrrpos) /w linux 6.13.2 /w Lynx 2.9.2 - `OK`
- (DOSBox-X VM) Windows 98 SE /w Netscape Navigator 3.0 (JS off) - `PARTIAL` (UI issues and CF challenge JS)

## ⚙ Backend on dih.pythonanywhere.com

`anw.is-a.dev` is whitelisted on PythonAnywhere. By using my domain, I created a 3-step proxy for Ablaze's website. Why? Because PythonAnywhere is the only reliable host which allows `HTTP` while Vercel forces `HTTPS`, which most retro browsers don't support. Here's the source code:

```python
from flask import Flask, request, Response
from urllib.parse import quote
import requests

app = Flask(__name__)

@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def relay(path):
    if path.startswith("api/ablaze/"):
        path = path.replace("api/ablaze/", "", 1)
    elif path == "api/ablaze":
        path = ""

    path = quote(path, safe="")

    target_url = (
        f"https://anw.is-a.dev/api/ablaze/{path}"
        if path else
        "https://anw.is-a.dev/api/ablaze"
    )

    try:
        headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in (
                "host",
                "user-agent",
                "content-length",
                "connection"
            )
        }

        headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )

        resp = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            headers=headers,
            allow_redirects=False,
            timeout=30
        )

        excluded_headers = {
            "host",
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        }

        response_headers = {
            k: v
            for k, v in resp.headers.items()
            if k.lower() not in excluded_headers
        }

        return Response(
            resp.content,
            status=resp.status_code,
            headers=response_headers
        )

    except Exception as e:
        return f"Relay error: {e}", 500
```

**Please do not use my API for production.**

## ⚙ Backend on anw.is-a.dev/api/ablaze

This is the source code for the Flask endpoint at `anw.is-a.dev/api/ablaze`. **Please host it yourself and do not use my API for production. I do NOT guarantee 100% uptime.** Why not just host Ablaze on `anw.is-a.dev`? Because I don't want to. Ofcourse, you don't need this if you are hosting it by yourself.  

```python
@app.route('/api/ablaze', defaults={'url_path': ''}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.route('/api/ablaze/<path:url_path>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def ablaze_backend_proxy(url_path):
    url_path = unquote(url_path)
    
    if url_path.startswith("api/ablaze/"):
        url_path = url_path.replace("api/ablaze/", "", 1)
    elif url_path == "api/ablaze":
        url_path = ""

    if "proxy/https:/" in url_path and "proxy/https://" not in url_path:
        url_path = url_path.replace("proxy/https:/", "proxy/https://", 1)
    elif "proxy/http:/" in url_path and "proxy/http://" not in url_path:
        url_path = url_path.replace("proxy/http:/", "proxy/http://", 1)
        
    if "pure-proxy/https:/" in url_path and "pure-proxy/https://" not in url_path:
        url_path = url_path.replace("pure-proxy/https:/", "pure-proxy/https://", 1)
    elif "pure-proxy/http:/" in url_path and "pure-proxy/http://" not in url_path:
        url_path = url_path.replace("pure-proxy/http:/", "pure-proxy/http://", 1)

    if url_path.startswith("proxy/"):
        url_path = "proxy/" + quote(unquote(url_path[6:]), safe="")
    elif url_path.startswith("pure-proxy/"):
        url_path = "pure-proxy/" + quote(unquote(url_path[11:]), safe="")

    target_url = f"https://ablaze-cyan.vercel.app/{url_path}"
    headers = { k: v for k, v in request.headers.items() if k.lower() not in ["host", "accept-encoding"] }
    
    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            headers=headers,
            allow_redirects=False,
            timeout=60
        )
        
        proxy_resp = Response(response.content, status=response.status_code)
        
        excluded_headers = ['content-encoding', 'transfer-encoding', 'content-length', 'content-range']
        for k, v in response.headers.items():
            if k.lower() not in excluded_headers:
                proxy_resp.headers[k] = v
                
        return proxy_resp
        
    except Exception as e:
        return f"Ablaze API Gateway Error: {e}", 500
```

## 🤝 Contributors:

None at the moment, but you can become one! Talk to [ANW](https://anw.is-a.dev/#contact) or make a PR to contribute.
