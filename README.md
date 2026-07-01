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

## 🤝 Contributors:

None at the moment, but you can become one! Talk to [ANW](https://anw.is-a.dev/#contact) or make a PR to contribute.
