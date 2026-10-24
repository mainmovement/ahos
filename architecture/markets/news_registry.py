"""M18 news source registry: candidate RSS/Atom feeds -> VERIFIED only after a live fetch from THIS host returns
a parseable feed with dated items newer than MAX_STALE_DAYS. Every check is timestamped per host (box / laptop),
so 'verified' always means 'worked from here, recently'. Free feeds only. PAPER_ONLY."""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import socket
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

UA = {"User-Agent": "Mozilla/5.0 (AHOS news registry; RSS reader)"}
OUT_REL = Path("reports") / "grok" / "M18" / "news_registry.json"
MAX_STALE_DAYS = 14

# (id, category, url). Candidates only; nothing here is trusted until verify() says so.
CANDIDATES: list[tuple[str, str, str]] = [
    # --- crypto ---
    ("cointelegraph", "crypto", "https://cointelegraph.com/rss"), ("decrypt", "crypto", "https://decrypt.co/feed"),
    ("cryptoslate", "crypto", "https://cryptoslate.com/feed/"), ("theblock", "crypto", "https://www.theblock.co/rss.xml"),
    ("coindesk", "crypto", "https://www.coindesk.com/arc/outboundfeeds/rss/"), ("bitcoinmagazine", "crypto", "https://bitcoinmagazine.com/.rss/full/"),
    ("cryptonews", "crypto", "https://cryptonews.com/news/feed/"), ("beincrypto", "crypto", "https://beincrypto.com/feed/"),
    ("newsbtc", "crypto", "https://www.newsbtc.com/feed/"), ("bitcoinist", "crypto", "https://bitcoinist.com/feed/"),
    ("cryptopotato", "crypto", "https://cryptopotato.com/feed/"), ("u_today", "crypto", "https://u.today/rss"),
    ("dailyhodl", "crypto", "https://dailyhodl.com/feed/"), ("ambcrypto", "crypto", "https://ambcrypto.com/feed/"),
    ("coingape", "crypto", "https://coingape.com/feed/"), ("cryptobriefing", "crypto", "https://cryptobriefing.com/feed/"),
    ("blockworks", "crypto", "https://blockworks.co/feed"), ("thedefiant", "crypto", "https://thedefiant.io/feed"),
    ("coinjournal", "crypto", "https://coinjournal.net/feed/"), ("cryptodaily", "crypto", "https://cryptodaily.co.uk/feed"),
    ("bitcoin_com", "crypto", "https://news.bitcoin.com/feed/"), ("coinpedia", "crypto", "https://coinpedia.org/feed/"),
    ("zycrypto", "crypto", "https://zycrypto.com/feed/"), ("cryptoglobe", "crypto", "https://www.cryptoglobe.com/latest/feed/"),
    ("ethereum_blog", "crypto", "https://blog.ethereum.org/feed.xml"), ("bitcoin_core", "crypto", "https://bitcoincore.org/en/rss.xml"),
    ("coinbase_blog", "crypto", "https://www.coinbase.com/blog/rss.xml"), ("kraken_blog", "crypto", "https://blog.kraken.com/feed"),
    ("glassnode_insights", "crypto", "https://insights.glassnode.com/rss/"), ("messari", "crypto", "https://messari.io/rss"),
    ("cryptoslate_research", "crypto", "https://cryptoslate.com/research/feed/"), ("watcher_guru", "crypto", "https://watcher.guru/news/feed"),
    ("coincentral", "crypto", "https://coincentral.com/feed/"), ("crypto_economy", "crypto", "https://crypto-economy.com/feed/"),
    ("finbold", "crypto", "https://finbold.com/feed/"), ("protos", "crypto", "https://protos.com/feed/"),
    # --- markets / business wires ---
    ("cnbc_markets", "markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("cnbc_economy", "macro", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("cnbc_finance", "markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("cnbc_world", "world", "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("cnbc_energy", "energy", "https://www.cnbc.com/id/19836768/device/rss/rss.html"),
    ("marketwatch_top", "markets", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("marketwatch_pulse", "markets", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"),
    ("marketwatch_bulletins", "markets", "https://feeds.content.dowjones.io/public/rss/mw_bulletins"),
    ("wsj_markets", "markets", "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"),
    ("wsj_world", "world", "https://feeds.content.dowjones.io/public/rss/RSSWorldNews"),
    ("wsj_economy", "macro", "https://feeds.content.dowjones.io/public/rss/socialeconomyfeed"),
    ("investing_news", "markets", "https://www.investing.com/rss/news_25.rss"),
    ("investing_commod", "commodities", "https://www.investing.com/rss/news_11.rss"),
    ("investing_forex", "fx", "https://www.investing.com/rss/news_1.rss"),
    ("investing_crypto", "crypto", "https://www.investing.com/rss/news_301.rss"),
    ("investing_economy", "macro", "https://www.investing.com/rss/news_14.rss"),
    ("investing_stocks", "markets", "https://www.investing.com/rss/news_95.rss"),
    ("yahoo_finance", "markets", "https://finance.yahoo.com/news/rssindex"),
    ("seekingalpha_market", "markets", "https://seekingalpha.com/market_currents.xml"),
    ("seekingalpha_all", "markets", "https://seekingalpha.com/feed.xml"),
    ("nasdaq_markets", "markets", "https://www.nasdaq.com/feed/rssoutbound?category=Markets"),
    ("nasdaq_crypto", "crypto", "https://www.nasdaq.com/feed/rssoutbound?category=Cryptocurrencies"),
    ("nasdaq_commod", "commodities", "https://www.nasdaq.com/feed/rssoutbound?category=Commodities"),
    ("ft_markets", "markets", "https://www.ft.com/markets?format=rss"), ("ft_world", "world", "https://www.ft.com/world?format=rss"),
    ("economist_finance", "macro", "https://www.economist.com/finance-and-economics/rss.xml"),
    ("economist_business", "markets", "https://www.economist.com/business/rss.xml"),
    ("bbc_business", "markets", "https://feeds.bbci.co.uk/news/business/rss.xml"), ("bbc_world", "world", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("bbc_mideast", "world", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
    ("guardian_business", "markets", "https://www.theguardian.com/uk/business/rss"), ("guardian_world", "world", "https://www.theguardian.com/world/rss"),
    ("guardian_economics", "macro", "https://www.theguardian.com/business/economics/rss"),
    ("nyt_business", "markets", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
    ("nyt_economy", "macro", "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"),
    ("nyt_world", "world", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("nyt_energy", "energy", "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml"),
    ("npr_business", "markets", "https://feeds.npr.org/1006/rss.xml"), ("npr_world", "world", "https://feeds.npr.org/1004/rss.xml"),
    ("aljazeera", "world", "https://www.aljazeera.com/xml/rss/all.xml"), ("dw_business", "markets", "https://rss.dw.com/rdf/rss-en-bus"),
    ("dw_world", "world", "https://rss.dw.com/rdf/rss-en-world"), ("france24_business", "markets", "https://www.france24.com/en/business/rss"),
    ("france24_world", "world", "https://www.france24.com/en/rss"), ("euronews_business", "markets", "https://www.euronews.com/rss?level=vertical&name=business"),
    ("abc_business", "markets", "https://abcnews.go.com/abcnews/moneyheadlines"), ("cbs_moneywatch", "markets", "https://www.cbsnews.com/latest/rss/moneywatch"),
    ("fox_business", "markets", "https://moxie.foxbusiness.com/google-publisher/markets.xml"),
    ("fox_business_econ", "macro", "https://moxie.foxbusiness.com/google-publisher/economy.xml"),
    ("businessinsider_markets", "markets", "https://markets.businessinsider.com/rss/news"),
    ("fortune", "markets", "https://fortune.com/feed/"), ("forbes_markets", "markets", "https://www.forbes.com/markets/feed/"),
    ("forbes_crypto", "crypto", "https://www.forbes.com/crypto-blockchain/feed/"), ("axios_markets", "markets", "https://api.axios.com/feed/markets"),
    ("thestreet", "markets", "https://www.thestreet.com/.rss/full/"), ("benzinga", "markets", "https://www.benzinga.com/feed"),
    ("zerohedge", "markets", "https://feeds.feedburner.com/zerohedge/feed"), ("calculatedrisk", "macro", "https://www.calculatedriskblog.com/feeds/posts/default"),
    ("wolfstreet", "macro", "https://wolfstreet.com/feed/"), ("marginalrevolution", "macro", "https://marginalrevolution.com/feed"),
    ("abnormalreturns", "markets", "https://abnormalreturns.com/feed/"), ("bespoke", "markets", "https://www.bespokepremium.com/feed/"),
    ("advisorperspectives", "markets", "https://www.advisorperspectives.com/rss/dshort"),
    ("scmp_business", "asia", "https://www.scmp.com/rss/92/feed"), ("scmp_china", "asia", "https://www.scmp.com/rss/4/feed"),
    ("nikkei_asia", "asia", "https://asia.nikkei.com/rss/feed/nar"), ("japantimes_business", "asia", "https://www.japantimes.co.jp/business/feed/"),
    ("straitstimes_business", "asia", "https://www.straitstimes.com/news/business/rss.xml"),
    ("economictimes_markets", "asia", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("livemint_markets", "asia", "https://www.livemint.com/rss/markets"), ("moneycontrol", "asia", "https://www.moneycontrol.com/rss/latestnews.xml"),
    ("businesstimes_sg", "asia", "https://www.businesstimes.com.sg/rss/top-stories"), ("koreaherald_biz", "asia", "https://www.koreaherald.com/rss/020000000000.xml"),
    ("yonhap_economy", "asia", "https://en.yna.co.kr/RSS/economy.xml"), ("caixin", "asia", "https://www.caixinglobal.com/rss/"),
    ("cityam", "eu", "https://www.cityam.com/feed/"), ("thisismoney", "eu", "https://www.thisismoney.co.uk/money/markets/index.rss"),
    ("independent_business", "eu", "https://www.independent.co.uk/news/business/rss"), ("telegraph_business", "eu", "https://www.telegraph.co.uk/business/rss.xml"),
    ("lesechos", "eu", "https://syndication.lesechos.fr/rss/rss_finance-marches.xml"), ("handelsblatt", "eu", "https://www.handelsblatt.com/contentexport/feed/finanzen"),
    ("faz_finanzen", "eu", "https://www.faz.net/rss/aktuell/finanzen/"), ("spiegel_wirtschaft", "eu", "https://www.spiegel.de/wirtschaft/index.rss"),
    ("elpais_economia", "eu", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada"),
    ("ilsole24ore", "eu", "https://www.ilsole24ore.com/rss/finanza.xml"),
    # --- central banks / official ---
    ("fed_press", "central_bank", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("fed_monetary", "central_bank", "https://www.federalreserve.gov/feeds/press_monetary.xml"),
    ("fed_speeches", "central_bank", "https://www.federalreserve.gov/feeds/speeches.xml"),
    ("ny_fed", "central_bank", "https://www.newyorkfed.org/medialibrary/media/rss/press-releases.xml"),
    ("stlouisfed_blog", "central_bank", "https://www.stlouisfed.org/rss/page%20resources/publications/blog%20entries"),
    ("ecb_press", "central_bank", "https://www.ecb.europa.eu/rss/press.html"), ("ecb_blog", "central_bank", "https://www.ecb.europa.eu/rss/blog.html"),
    ("boe_news", "central_bank", "https://www.bankofengland.co.uk/rss/news"), ("boe_publications", "central_bank", "https://www.bankofengland.co.uk/rss/publications"),
    ("boj", "central_bank", "https://www.boj.or.jp/en/rss/whatsnew.xml"), ("rba", "central_bank", "https://www.rba.gov.au/rss/rss-cb-media-releases.xml"),
    ("bankofcanada", "central_bank", "https://www.bankofcanada.ca/content_type/press-releases/feed/"),
    ("snb", "central_bank", "https://www.snb.ch/public/en/rss/news"), ("riksbank", "central_bank", "https://www.riksbank.se/en-gb/rss/press-releases/"),
    ("rbnz", "central_bank", "https://www.rbnz.govt.nz/feeds/news"), ("bis_press", "central_bank", "https://www.bis.org/doclist/all_pressrels.rss"),
    ("bis_speeches", "central_bank", "https://www.bis.org/doclist/cbspeeches.rss"), ("imf_news", "official", "https://www.imf.org/en/News/rss?language=eng"),
    ("worldbank", "official", "https://www.worldbank.org/en/news/rss.xml"), ("oecd", "official", "https://www.oecd.org/newsroom/index.xml"),
    ("treasury", "official", "https://home.treasury.gov/news/press-releases/feed"), ("sec_press", "official", "https://www.sec.gov/news/pressreleases.rss"),
    ("cftc_press", "official", "https://www.cftc.gov/RSS/RSSGP/rssgp.xml"), ("bls_latest", "official", "https://www.bls.gov/feed/bls_latest.rss"),
    ("bls_cpi", "official", "https://www.bls.gov/feed/cpi.rss"), ("bls_empsit", "official", "https://www.bls.gov/feed/empsit.rss"),
    ("bea", "official", "https://apps.bea.gov/rss/rss.xml"), ("census_econ", "official", "https://www.census.gov/economic-indicators/indicator.xml"),
    ("eurostat", "official", "https://ec.europa.eu/eurostat/en/search?p_p_id=estatsearchportlet_WAR_estatsearchportlet&p_p_lifecycle=2&p_p_state=maximized&p_p_mode=view&p_p_resource_id=atom&_estatsearchportlet_WAR_estatsearchportlet_collection=CAT_EURNEW"),
    ("ons", "official", "https://www.ons.gov.uk/releasecalendar?rss"), ("fdic", "official", "https://www.fdic.gov/news/press-releases/rss.xml"),
    ("finra", "official", "https://www.finra.org/rss/newsreleases"), ("esma", "official", "https://www.esma.europa.eu/rss.xml"),
    # --- energy / commodities ---
    ("oilprice", "energy", "https://oilprice.com/rss/main"), ("eia_today", "energy", "https://www.eia.gov/rss/todayinenergy.xml"),
    ("eia_press", "energy", "https://www.eia.gov/rss/press_rss.xml"), ("eia_steo", "energy", "https://www.eia.gov/rss/steo.xml"),
    ("eia_wpsr", "energy", "https://www.eia.gov/rss/petroleum.xml"), ("iea_news", "energy", "https://www.iea.org/rss/news.xml"),
    ("rigzone", "energy", "https://www.rigzone.com/news/rss/rigzone_latest.aspx"), ("offshore_tech", "energy", "https://www.offshore-technology.com/feed/"),
    ("energyvoice", "energy", "https://www.energyvoice.com/feed/"), ("naturalgasintel", "energy", "https://www.naturalgasintel.com/feed/"),
    ("worldoil", "energy", "https://www.worldoil.com/rss?feed=news"), ("ogj", "energy", "https://www.ogj.com/__rss/website-scheduled-content.xml?input=%7B%22sectionAlias%22%3A%22general-interest%22%7D"),
    ("hartenergy", "energy", "https://www.hartenergy.com/rss.xml"), ("spglobal_commod", "commodities", "https://www.spglobal.com/commodityinsights/en/rss-feed/oil"),
    ("kitco_news", "metals", "https://www.kitco.com/rss/KitcoNews.xml"), ("mining_com", "metals", "https://www.mining.com/feed/"),
    ("goldbroker", "metals", "https://www.goldbroker.com/news.rss"), ("gold_org", "metals", "https://www.gold.org/rss/news"),
    ("fxstreet_gold", "metals", "https://www.fxstreet.com/rss/news"), ("silverinstitute", "metals", "https://www.silverinstitute.org/feed/"),
    ("agweb", "commodities", "https://www.agweb.com/rss/news"), ("farmdoc", "commodities", "https://farmdocdaily.illinois.edu/feed"),
    ("usda_news", "commodities", "https://www.usda.gov/rss/latest-releases.xml"),
    # --- FX / macro analysis ---
    ("fxstreet", "fx", "https://www.fxstreet.com/rss"), ("forexlive", "fx", "https://www.forexlive.com/feed/news"),
    ("dailyfx", "fx", "https://www.dailyfx.com/feeds/market-news"), ("actionforex", "fx", "https://www.actionforex.com/feed/"),
    ("fxempire", "fx", "https://www.fxempire.com/api/v1/en/articles/rss/news"), ("babypips", "fx", "https://www.babypips.com/feed.rss"),
    ("econbrowser", "macro", "https://econbrowser.com/feed"), ("bruegel", "macro", "https://www.bruegel.org/rss.xml"),
    ("piie", "macro", "https://www.piie.com/rss/update.xml"), ("brookings_econ", "macro", "https://www.brookings.edu/topic/economic-studies/feed/"),
    ("voxeu", "macro", "https://cepr.org/rss/vox-content"), ("nber_new", "research", "https://www.nber.org/rss/new.xml"),
    ("arxiv_qfin", "research", "https://rss.arxiv.org/rss/q-fin"), ("arxiv_qfin_tr", "research", "https://rss.arxiv.org/rss/q-fin.TR"),
    ("ssrn_fin", "research", "https://papers.ssrn.com/sol3/Jeljour_results.cfm?form_name=journalBrowse&journal_id=203&Network=no&lim=false&npage=1&rss=1"),
    ("alphaarchitect", "research", "https://alphaarchitect.com/feed/"), ("quantocracy", "research", "https://quantocracy.com/feed/"),
    ("quantpedia", "research", "https://quantpedia.com/feed/"), ("robotwealth", "research", "https://robotwealth.com/feed/"),
    ("aqr", "research", "https://www.aqr.com/Insights/Research/rss"), ("cfa_enterprising", "research", "https://blogs.cfainstitute.org/investor/feed/"),
    # --- world / geopolitics / regional ---
    ("ap_top", "world", "https://feedx.net/rss/ap.xml"), ("reuters_via_google", "world", "https://news.google.com/rss/search?q=site:reuters.com+markets&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_oil", "energy", "https://news.google.com/rss/search?q=oil+prices&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_gold", "metals", "https://news.google.com/rss/search?q=gold+price&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_bitcoin", "crypto", "https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_fed", "central_bank", "https://news.google.com/rss/search?q=federal+reserve&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_opec", "energy", "https://news.google.com/rss/search?q=OPEC&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_forex", "fx", "https://news.google.com/rss/search?q=dollar+forex&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_stocks", "markets", "https://news.google.com/rss/search?q=stock+market&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_ecb", "central_bank", "https://news.google.com/rss/search?q=ECB+Lagarde&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_boj", "central_bank", "https://news.google.com/rss/search?q=Bank+of+Japan&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_china_econ", "asia", "https://news.google.com/rss/search?q=China+economy&hl=en-US&gl=US&ceid=US:en"),
    ("gnews_iran_oil", "energy", "https://news.google.com/rss/search?q=Iran+oil&hl=en-US&gl=US&ceid=US:en"),
    ("cnn_business", "markets", "http://rss.cnn.com/rss/money_latest.rss"), ("cnn_world", "world", "http://rss.cnn.com/rss/edition_world.rss"),
    ("politico_econ", "macro", "https://rss.politico.com/economy.xml"), ("thehill_finance", "macro", "https://thehill.com/policy/finance/feed/"),
    ("foreignpolicy", "world", "https://foreignpolicy.com/feed/"), ("crisisgroup", "world", "https://www.crisisgroup.org/rss.xml"),
    ("middleeasteye", "world", "https://www.middleeasteye.net/rss"), ("arabnews_business", "world", "https://www.arabnews.com/cat/3/rss.xml"),
    ("gulfnews_business", "world", "https://gulfnews.com/rss?generatorName=business"), ("thenational_business", "world", "https://www.thenationalnews.com/arc/outboundfeeds/rss/category/business/?outputType=xml"),
    ("tehrantimes_econ", "world", "https://www.tehrantimes.com/rss/tp/698"), ("irna_en", "world", "https://en.irna.ir/rss"),
    ("financialtribune", "world", "https://financialtribune.com/rss.xml"), ("donya_eqtesad", "world", "https://donya-e-eqtesad.com/fa/rss/allnews"),
    ("eghtesadnews", "world", "https://www.eghtesadnews.com/fa/rss/allnews"), ("tasnim_econ", "world", "https://www.tasnimnews.com/fa/rss/feed/0/7/0"),
    ("isna_econ", "world", "https://www.isna.ir/rss/tp/34"), ("bbcpersian", "world", "https://feeds.bbci.co.uk/persian/rss.xml"),
    ("dwpersian", "world", "https://rss.dw.com/rdf/rss-per-all"), ("radiofarda", "world", "https://www.radiofarda.com/api/zpqyveq-uvm"),
    ("iranintl_en", "world", "https://www.iranintl.com/en/feed"), ("rt_business", "world", "https://www.rt.com/rss/business/"),
    ("tass_economy", "world", "https://tass.com/rss/v2.xml"), ("xinhua_business", "asia", "http://www.xinhuanet.com/english/rss/businessrss.xml"),
    ("cgtn_business", "asia", "https://www.cgtn.com/subscribe/rss/section/business.xml"),
    # --- tech / equities ---
    ("techcrunch", "tech", "https://techcrunch.com/feed/"), ("theverge", "tech", "https://www.theverge.com/rss/index.xml"),
    ("arstechnica", "tech", "https://feeds.arstechnica.com/arstechnica/index"), ("wired_business", "tech", "https://www.wired.com/feed/category/business/latest/rss"),
    ("hn_frontpage", "tech", "https://hnrss.org/frontpage"), ("semianalysis", "tech", "https://www.semianalysis.com/feed"),
    ("prnewswire", "markets", "https://www.prnewswire.com/rss/news-releases-list.rss"), ("globenewswire", "markets", "https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20News%20about%20Public%20Companies"),
    ("businesswire", "markets", "https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFtRWA=="),
    ("accesswire", "markets", "https://www.accesswire.com/users/newswire/rss"),
]


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def parse_feed(raw: bytes) -> list[dict[str, Any]]:
    """RSS 2.0 / RDF / Atom -> [{title, link, published}] (namespace-agnostic)."""
    txt = raw.decode("utf-8", "ignore").lstrip("\ufeff \r\n\t")
    txt = re.sub(r"<\?xml[^>]*\?>", "", txt, count=1)
    root = ET.fromstring(txt.encode("utf-8"))
    items = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1].lower()
        if tag not in ("item", "entry"):
            continue
        rec: dict[str, Any] = {}
        for ch in el:
            t = ch.tag.rsplit("}", 1)[-1].lower()
            if t == "title" and ch.text:
                rec["title"] = re.sub(r"\s+", " ", ch.text).strip()
            elif t == "link":
                rec.setdefault("link", (ch.get("href") or ch.text or "").strip())
            elif t in ("pubdate", "published", "updated", "date") and ch.text and "published" not in rec:
                rec["published"] = _parse_date(ch.text)
        if rec.get("title"):
            items.append(rec)
    return items


def check(src: tuple[str, str, str], timeout: float = 12.0) -> dict[str, Any]:
    sid, cat, url = src
    t0 = time.time()
    row: dict[str, Any] = {"id": sid, "category": cat, "url": url, "domain": urlparse(url).netloc.replace("www.", "")}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            raw = r.read(3_000_000)
            row["http"] = r.status
        items = parse_feed(raw)
        dated = [i["published"] for i in items if i.get("published")]
        newest = max(dated) if dated else None
        age_d = (datetime.now(timezone.utc) - newest).total_seconds() / 86400 if newest else None
        row.update({"items": len(items), "dated_items": len(dated), "newest_utc": newest.isoformat() if newest else None,
                    "newest_age_days": round(age_d, 2) if age_d is not None else None})
        row["verified"] = bool(items) and age_d is not None and age_d <= MAX_STALE_DAYS
        row["reason"] = "OK" if row["verified"] else ("NO_ITEMS" if not items else "NO_DATES" if age_d is None else "STALE")
    except ET.ParseError:
        row.update({"verified": False, "reason": "NOT_A_FEED"})
    except urllib.error.HTTPError as e:
        row.update({"verified": False, "reason": f"HTTP_{e.code}"})
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
        row.update({"verified": False, "reason": f"NET:{type(getattr(e, 'reason', e)).__name__}"})
    except Exception as e:  # pragma: no cover
        row.update({"verified": False, "reason": f"ERR:{type(e).__name__}"})
    row["latency_s"] = round(time.time() - t0, 2)
    return row


def verify(root: Path | None, host: str, workers: int = 8, candidates: list[tuple[str, str, str]] | None = None) -> dict[str, Any]:
    cands = candidates or CANDIDATES
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(check, cands))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev: dict[str, Any] = {}
    if root is not None:
        try:
            prev = json.loads((Path(root) / OUT_REL).read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    by_host = prev.get("by_host") or {}
    by_host[host] = {"checked_at": now, "rows": rows}
    merged = {}
    for h, blk in by_host.items():
        for r in blk["rows"]:
            m = merged.setdefault(r["id"], {"id": r["id"], "category": r["category"], "url": r["url"], "domain": r["domain"], "hosts": {}})
            m["hosts"][h] = {k: r.get(k) for k in ("verified", "reason", "items", "newest_age_days", "latency_s")} | {"checked_at": blk["checked_at"]}
    for m in merged.values():
        m["verified_any"] = any(v["verified"] for v in m["hosts"].values())
    snap = {"schema": "ahos.news_registry.v1", "generated_at": now, "paper_only": True,
            "rule": f"verified = live fetch from that host parsed as RSS/Atom with dated items <= {MAX_STALE_DAYS}d old",
            "candidates": len(cands), "by_host": by_host,
            "verified_count_by_host": {h: sum(1 for r in blk["rows"] if r.get("verified")) for h, blk in by_host.items()},
            "sources": sorted(merged.values(), key=lambda m: (m["category"], m["id"]))}
    if root is not None:
        p = Path(root) / OUT_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def verified_feeds(root: Path, host: str | None = None, categories: set[str] | None = None) -> list[dict[str, Any]]:
    try:
        snap = json.loads((Path(root) / OUT_REL).read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for s in snap.get("sources") or []:
        ok = s["hosts"].get(host, {}).get("verified") if host else s.get("verified_any")
        if ok and (not categories or s["category"] in categories):
            out.append(s)
    return out
