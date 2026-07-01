# 🔥 Ablaze

A simple search engine + website proxy so that you can browse the modern web on browsers from the late 20th century.  

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

## ⚙ Backend on dih.pythonanywhere.com

`anw.is-a.dev` is whitelisted on PythonAnywhere. By using my domain, I created a 3-step proxy for Ablaze's website. Why? Because PythonAnywhere is the only reliable host which allows `HTTP` while Vercel forces `HTTPS`, which most retro browsers don't support. Here's the source code:

```python
from flask import Flask, request, Response
from urllib.parse import urlparse
import requests

app = Flask(__name__)

BACKEND_URL = "https://anw.is-a.dev/api/ablaze"

@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def relay(path):
    target_url = f"{BACKEND_URL}/{path}" if path != '' else f"{BACKEND_URL}"
    params = request.args

    try:
        if request.method == "GET":
            resp = requests.get(target_url, params=params, headers={"User-Agent": request.headers.get("User-Agent")}, allow_redirects=False)
        else:
            resp = requests.post(target_url, params=params, data=request.get_data(), headers={"User-Agent": request.headers.get("User-Agent")}, allow_redirects=False)

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers}

        if 'Location' in resp.headers:
            location = resp.headers['Location']
            parsed_loc = urlparse(location)
            
            if location.startswith('/') and not location.startswith('/api/ablaze'):
                headers['Location'] = f"/api/ablaze{location}"
            elif parsed_loc.netloc == "anw.is-a.dev" and not parsed_loc.path.startswith('/api/ablaze'):
                new_path = f"/api/ablaze{parsed_loc.path}"
                headers['Location'] = location.replace(parsed_loc.path, new_path, 1)

        return Response(resp.content, status=resp.status_code, headers=headers)
    except Exception as e:
        return f"Relay error: {e}", 500
```

## ⚙ Backend on anw.is-a.dev/api/ablaze

This is the source code for the Flask endpoint at `anw.is-a.dev/api/ablaze`. **Please host it yourself and do not use my API for production. I do NOT guarantee 100% uptime.**

```python
@app.route('/api/ablaze', defaults={'url_path': ''}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
@app.route('/api/ablaze/<path:url_path>', methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def ablaze_backend_proxy(url_path):
    target_url = f"https://ablaze-cyan.vercel.app/{url_path}"
    
    headers = { k: v for k, v in request.headers.items() if k.lower() != "host" }
    
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
        
        for k, v in response.headers.items():
            if k.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                proxy_resp.headers[k] = v
                
        return proxy_resp
        
    except Exception as e:
        return f"Ablaze API Gateway Error: {e}", 500
```

## 🤝 Contributors:

None at the moment, but you can become one! Talk to [ANW](https://anw.is-a.dev/#contact) or make a PR to contribute.
