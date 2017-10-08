function main(splash)
  splash.images_enabled = false
  splash:on_request(function(request)
                request:set_header("User-Agent", "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0")
            end)
  local url = splash.args.url
  local wait = 10.0
  assert(splash:go(url))
  assert(splash:wait(wait))
  return {
    html = splash:html(),
    png = splash:png{render_all=true},
    cookies = splash:get_cookies(),
    url = splash:evaljs("window.location.href"),
  }
end