# -*- coding: utf-8 -*-
"""Парсер карточки товара example.com -> полный JSON (по спеке)."""
import re
from bs4 import BeautifulSoup

HOST = "https://www.example.com"


def _clean(s):
    return re.sub(r"\s+", " ", s).strip() if s else ""


def _abs(url):
    if not url:
        return url
    url = url.strip()
    if url.startswith("http"):
        return url
    return HOST + url


def _parse_table(table):
    """Строки <tr> -> dict. colspan=2 = заголовок секции; ключи с '-/'–' -> в секцию."""
    result = {}
    section = None
    for tr in table.select("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue
        colspans = [td.get("colspan") for td in tds]
        if len(tds) == 1 or "2" in colspans:
            section = _clean(tds[0].get_text())
            result[section] = {}
            continue
        if len(tds) >= 2:
            key = _clean(tds[0].get_text())
            val = _clean(tds[1].get_text())
            if key.startswith("-") or key.startswith("–"):
                if section is not None:
                    result[section][key] = val
                else:
                    result[key] = val
            else:
                result[key] = val
    return {k: v for k, v in result.items() if v != {}}


def parse_article(html):
    m = re.search(r'item__articule[^>]*>\s*Артикул:\s*([^<]+)', html)
    if not m:
        return None
    return _clean(m.group(1))


def parse_page(html, page_url=None):
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    # name
    h1 = soup.select_one("h1.item__title")
    out["name"] = _clean(h1.get_text()) if h1 else None

    # article
    art = soup.select_one("div.item__articule")
    out["article"] = _clean(art.get_text()).replace("Артикул:", "").strip() if art else None

    # url (canonical)
    canon = soup.select_one('link[rel="canonical"]')
    out["url"] = canon.get("href") if canon else page_url

    # shortDescription (внутренний HTML)
    desc = soup.select_one("div.item__desc")
    out["shortDescription"] = desc.decode_contents().strip() if desc else None

    # images
    images = []
    for a in soup.select("div.item__images a[data-fancybox]"):
        images.append({
            "url": _abs(a.get("href")),
            "caption": a.get("data-caption") or a.get("title"),
        })
    out["images"] = images

    # ---- specifications ----
    specs = {}
    opts = soup.select_one("div.item-settings__options")
    if opts:
        # productName: <p> после <p><strong>Наименование изделия</strong></p>
        label = opts.find("strong", string=re.compile("Наименование изделия"))
        if label and label.find_parent("p"):
            nxt = label.find_parent("p").find_next_sibling("p")
            if nxt:
                specs["productName"] = _clean(nxt.get_text(separator=" "))
        # certificate
        cert = opts.find(string=re.compile("Регистрационное удостоверение"))
        if cert:
            specs["certificate"] = _clean(cert)
        # tables: paramsAndDimensions + characteristics
        tables = opts.select("table")
        if tables:
            specs["paramsAndDimensions"] = _parse_table(tables[0])
        if len(tables) > 1:
            specs["characteristics"] = _parse_table(tables[1])
    # disclaimers
    disc = soup.select_one("div.item-settings__disclaimers")
    if disc:
        specs["disclaimers"] = [_clean(p.get_text()) for p in disc.select("p")]
    # dimensional drawing
    dd = soup.select_one("a.fancy-gallery")
    if dd:
        cap = dd.select_one("figcaption")
        specs["dimensionalDrawing"] = {
            "url": _abs(dd.get("href")),
            "caption": _clean(cap.get_text()) if cap else None,
        }
    out["specifications"] = specs

    # ---- tabs: Стандартное исполнение / Применение ----
    out["standardFeatures"] = []
    out["application"] = {}
    tabs = soup.select("div.g-tabs__container")
    for tab in tabs:
        # определить заголовок вкладки по ближайшей таб-ссылке
        # проще: искать по содержимому
        if tab.select_one("div.item-usage__text"):
            # Применение
            app = {}
            for cap in tab.select("div.item-usage__caption"):
                cap_text = _clean(cap.get_text())
                ul = cap.find_next("ul")
                items = []
                if ul:
                    for li in ul.select("li"):
                        a = li.find("a")
                        items.append({
                            "name": _clean(li.get_text()),
                            "url": a.get("href") if a else None,
                        })
                if cap_text == "Отрасли":
                    app["industries"] = items
                elif cap_text == "Тип защиты":
                    app["protectionTypes"] = items
                elif cap_text == "Виды работ":
                    app["workTypes"] = items
            ut = tab.select_one("div.item-usage__text")
            app["description"] = _clean(ut.get_text()) if ut else None
            out["application"] = app
        elif tab.select("div.g-dropdown"):
            # Стандартное исполнение
            feats = []
            for dd in tab.select("div.g-dropdown"):
                t = dd.select_one("a.g-dropdown__toggler")
                c = dd.select_one("div.g-dropdown__inner")
                feats.append({
                    "title": _clean(t.get_text()) if t else None,
                    "content": c.decode_contents().strip() if c else None,
                })
            out["standardFeatures"] = feats
    # если standardFeatures пустой, попробовать найти dropdown-блоки вне табов
    if not out["standardFeatures"]:
        # некоторые страницы могут иметь их в других контейнерах
        pass

    # ---- extra options ----
    extras = []
    for dd in soup.select("div.item-extra div.g-dropdown"):
        t = dd.select_one("a.g-bolder") or dd.select_one("a.g-dropdown__toggler")
        c = dd.select_one("div.g-dropdown__inner")
        extras.append({
            "title": _clean(t.get_text()) if t else None,
            "content": c.decode_contents().strip() if c else None,
        })
    out["extraOptions"] = extras

    # ---- related products ----
    related = []
    for s in soup.select("div.item-slider__slide"):
        n = s.select_one("a.item-slider__name")
        img = s.select_one("a.item-slider__image img")
        related.append({
            "name": _clean(n.get_text()) if n else None,
            "url": n.get("href") if n else None,
            "image": _abs(img.get("src")) if img else None,
        })
    out["relatedProducts"] = related

    return out
