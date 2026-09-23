#!/usr/bin/env python3
"""case_studies.py — 生成 /case-studies 页面 + 全站导航注入（幂等）

用法:
  python3 scripts/case_studies.py            # 生成 case-studies.html（幂等覆盖）
  python3 scripts/case_studies.py --link-nav # 同时向根目录所有页面 nav/footer 注入 Case Studies 链接（幂等）

加新案例：只改 CASES 列表，重跑本脚本即可——页面自动重建。
"""
import sys, re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- 案例数据（唯一需要维护的地方）
CASES = [
    {
        "slug": "tree-of-light",
        "tag": "Light & Mood · global retail",
        "title": "Tree of Light — from our wood-lamp platform to global retail",
        "body": [
            "A branch-shaped solid-wood lamp that combines a bedside lamp, a Qi wireless charger and a Bluetooth speaker in one base — built on our Light & Mood platform and sold internationally under the HomeTree brand, plus retail editions under distributor brands such as Articture (\"Light of Life\", \"Noir Lamp\").",
            "What makes this case different from a typical supplier story: almost every milestone is a <b>publicly checkable record</b>. We list the receipts so you can verify instead of trusting marketing copy.",
        ],
        "evidence": [
            ("US design patent D1,024,003 S (Bluetooth speaker), granted April 2024",
             "https://patents.justia.com/patent/D1024003"),
            ("Indiegogo campaign \u201cHome Tree \u2014 Light From The Forest\u201d (38-LED cherry-wood edition)",
             "https://www.indiegogo.com/en/projects/hometreetech/home-tree-light-from-the-forest--2"),
            ("TechAcute review, May 2020: \u201cMaglamp \u2014 The Happiness Lamp with Wireless Charging\u201d",
             "https://techacute.com/maglamp/"),
            ("Boing Boing features on the Tree of Light retail edition, 2021 & 2022",
             "https://boingboing.net/2021/06/27/tree-of-light-is-a-lamp-charger-and-bluetooth-speaker-all-in-one.html"),
            ("Australian Giftguide trade-press coverage with founder interview, October 2017",
             "https://www.giftguideonline.com.au/"),
            ("Shanghai Youth Daily designer interview, August 2016",
             "http://app.why.com.cn/epaper/webpc/shzk/html/2016-08/02/content_6146.html"),
        ],
        "takeaway": "Public records \u2014 patents, crowdfunding pages, independent press \u2014 compound over years. This is the evidence trail we build for clients who want their brand to be findable and citable, not just sellable.",
    },
    {
        "slug": "heated-wellness-usa",
        "tag": "Body care · anonymized (NDA)",
        "title": "Heated wellness line for a US brand — platform to repeat orders",
        "body": [
            "A US wellness brand came to us with a brief, not a drawing. We matched their price band and target market to one of our heated body-care platforms, then customized logo, packaging, colours and finishes (OEM scope).",
            "Sampling took 14 days including one revision round. Mass production shipped FOB Shenzhen within the standard 4\u20138 week window; the line is covered by our 500-day warranty. The client has re-ordered across subsequent seasons and extended into a second product from the same platform family.",
        ],
        "evidence": [
            ("Heated body-care platforms (knee, waist, eye) with per-card MOQ and sample specs",
             "/product-platforms#body-care"),
            ("Our buying terms: MOQ Lite 100-499 / Slim 500-999 / Pro 1,000+, T/T 30/70, L/C accepted",
             "/moq-guide"),
        ],
        "takeaway": "Client details stay anonymous under NDA \u2014 the process, terms and timelines above are the real, citable part of the story.",
    },
    {
        "slug": "design-first-odm",
        "tag": "Design services · with Bole Design",
        "title": "Design-first ODM — from category insight to shelf",
        "body": [
            "For buyers who don't want to pick from a catalog, our design route starts earlier: category strategy and industrial design with our core strategic partner Bole Design (20 years of consulting, 500+ design awards, national industrial design center, studios in Hangzhou and Hamburg), then full-chain delivery into LightBDB production.",
            "One anonymously-credited personal-care case followed this exact path: market insight \u2192 concept \u2192 3D rendering \u2192 engineering \u2192 pilot run \u2192 mass production, with the buyer touching one team instead of coordinating a design house and a factory separately.",
        ],
        "evidence": [
            ("Design services scope and Bole Design credentials", "/design-services"),
            ("The 3-step co-creation journey: Choose \u00b7 Customize \u00b7 Deliver", "/brand-co-creation"),
        ],
        "takeaway": "Design and manufacturing under one roof is what turns \u201cwe can make anything\u201d into a delivery plan with dates.",
    },
]

FAQS = [
    ("Can you share client references?",
     "Yes \u2014 for the Tree of Light case most of the evidence is public (patent, crowdfunding page, independent press), linked below. For NDA cases we anonymize client names but can walk qualified buyers through the process, terms and timelines in a call."),
    ("What is publicly verifiable in the Tree of Light case?",
     "The US design patent record (D1,024,003 S), the Indiegogo campaign page, and independent media coverage from TechAcute, Boing Boing, Australian Giftguide and Shanghai Youth Daily. Every link on this page opens a third-party source."),
    ("What did the anonymized US wellness project look like in numbers?",
     "Platform-based OEM: sampling in about 14 days, production FOB Shenzhen within 4\u20138 weeks, MOQ per our tiered schedule (Lite 100-499 units upward), 500-day warranty. Exact unit prices are quoted per brief."),
    ("How would a similar project start for me?",
     "Send your brief via the RFQ form \u2014 you get a shortlist of matching platforms plus a proposal with 3D rendering and indicative quotation within one business day."),
    ("Do you sign NDAs?",
     "Yes. Anonymized cases on this page are the result of NDAs; public references are used only where the record is already public."),
    ("Which case is closest to a first-time buyer with low volume?",
     "The heated wellness case: every catalog platform starts at 100 units (Lite tier), sampling in 7\u201314 days, and the first sample fee is waived for first-time cooperation."),
]

# ---------------------------------------------------------------- 页面模板
def faq_jsonld():
    items = []
    for q, a in FAQS:
        items.append('{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
                     % (q.replace('"', '\\"'), a.replace('"', '\\"')))
    return ('<script type="application/ld+json">\n{"@context":"https://schema.org","@type":"FAQPage",'
            '"mainEntity":[\n' + ',\n'.join(items) + '\n]}\n</script>')

def case_html(i, c):
    ev = "\n".join(
        f'      <li><a href="{u}" target="_blank" rel="noopener nofollow">{t}</a></li>'
        for t, u in c["evidence"])
    paras = "\n".join(f'    <p>{p}</p>' for p in c["body"])
    return f'''  <article class="case" id="case-{c['slug']}" style="border:1px solid #e5e8da;border-radius:12px;padding:26px 28px;margin-bottom:26px;background:#fdfdfb">
    <p style="margin:0 0 6px"><span class="kicker" style="font-size:12px">Case {i} · {c['tag']}</span></p>
    <h2 style="margin:0 0 12px;font-size:clamp(20px,2.4vw,26px)">{c['title']}</h2>
{paras}
    <h3 style="margin:16px 0 8px;font-size:16px">Public evidence &amp; records</h3>
    <ul style="margin:0 0 12px;padding-left:20px;line-height:1.9">
{ev}
    </ul>
    <p style="margin:0;padding:10px 14px;background:#f4f6ec;border-radius:8px;font-size:15px"><b>Why it matters:</b> {c['takeaway']}</p>
  </article>'''

def build_page():
    cases = "\n\n".join(case_html(i + 1, c) for i, c in enumerate(CASES))
    faq_acc = "\n".join(
        f'    <details><summary>{q}</summary><div class="faq-a">{a}</div></details>'
        for q, a in FAQS)
    faq_json = faq_jsonld()
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- p0:meta -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="LightBDB">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="https://www.lightbdb.com/case-studies">
<meta property="og:title" content="Case Studies - LightBDB | Build · Design · Brand">
<meta property="og:description" content="Verifiable OEM/ODM case studies: a global-retail wood lamp with public patent and press records, an anonymized US heated-wellness line, and design-first ODM with Bole Design.">
<meta property="og:image" content="https://www.lightbdb.com/assets/img/design-case-hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Case Studies - LightBDB | Build · Design · Brand">
<meta name="twitter:description" content="Verifiable OEM/ODM case studies with public evidence: patents, crowdfunding, independent press.">
<meta name="twitter:image" content="https://www.lightbdb.com/assets/img/design-case-hero.jpg">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Case Studies - LightBDB | Build · Design · Brand</title>
<meta name="description" content="Verifiable OEM/ODM case studies: a global-retail wood lamp with public patent and press records, an anonymized US heated-wellness line, and design-first ODM with Bole Design.">
<link rel="canonical" href="https://www.lightbdb.com/case-studies">
<link rel="alternate" hreflang="en" href="https://www.lightbdb.com/case-studies">
<link rel="stylesheet" href="assets/css/styles.css">

<!-- p0:analytics -->
<!-- Cloudflare Web Analytics (auto-inject ruleset 不生效, 显式补) -->
<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "9857fc9065ca424194af3688274d319f"}}'></script>
{faq_json}
</head>
<body>

<header class="site">
  <div class="wrap nav">
    <a class="logo" href="/">
      <svg class="hex" viewBox="0 0 24 24" fill="none"><path d="M12 1.5 21.5 7v10L12 22.5 2.5 17V7L12 1.5Z" stroke="#B8C439" stroke-width="2.4"/><circle cx="12" cy="11.4" r="3.2" fill="#F7991D"/></svg>
      LIGHT <span class="bdb"><span class="b1">B</span><span class="d">D</span><span class="b2">B</span></span>
    </a>
    <nav class="links">
      <a href="/">Home</a>
      <a href="/product-platforms">Product Platforms</a>
      <a href="/brand-co-creation">Brand Co-creation</a>
      <a href="/design-services">Design Services</a>
      <a href="/about">About</a>
      <a href="/case-studies">Case Studies</a>
      <a href="/contact">Contact</a>
    </nav>
    <a class="cta" href="/rfq">Start Your Brand Upgrade</a>
  </div>
</header>
<div class="wrap">
  <section style="padding-top:56px;padding-bottom:28px">
    <span class="kicker">Case Studies</span>
    <h1 style="font-size:clamp(28px,3.6vw,40px);margin:12px 0 10px">Work you can check, not just claims you can read.</h1>
    <p class="lead">Three projects that show how we work \u2014 one with a fully public evidence trail, two anonymized under NDA but with real terms and timelines.</p>
  </section>

  <div class="answer">
    <h2>Quick answers</h2>
    <ul>
      <li><b>Public evidence:</b> the Tree of Light case is backed by a US design patent, an Indiegogo campaign and independent press (TechAcute, Boing Boing, Australian Giftguide) \u2014 every link opens a third-party source.</li>
      <li><b>Confidential cases:</b> anonymized under NDA; terms, timelines and MOQ tiers on this page are real.</li>
      <li><b>Starting point:</b> every catalog platform starts at 100 units; sampling in 7\u201314 days; proposal with 3D rendering and quotation within 24 hours.</li>
    </ul>
  </div>

{cases}

  <section style="padding-bottom:8px">
    <div class="sec-head">
      <span class="kicker">Before you ask</span>
      <h2 class="title">Honest limits</h2>
    </div>
    <div class="answer">
      <ul>
        <li>NDA cases on this page cannot be independently verified by design \u2014 that is what confidentiality costs. The public Tree of Light trail exists precisely because that brand chose a public route.</li>
        <li>We list certifications we actually hold (ISO 9001, ISO 14001, BSCI, UL registered factory, Sony Green Partner). We are not a medical-device factory and hold no ISO 13485 or FDA clearances.</li>
        <li>Unit economics vary by platform and volume; nothing on this page is a quotation.</li>
      </ul>
    </div>
  </section>

  <section style="padding-bottom:8px">
    <div class="sec-head">
      <span class="kicker">FAQ</span>
      <h2 class="title">Questions buyers ask about our cases</h2>
    </div>
    <div class="faq-acc">
{faq_acc}
    </div>
    <p style="margin-top:20px"><a href="/faq" style="color:var(--orange);font-weight:700">All 12 buying questions \u2192</a></p>
  </section>

  <section class="cta-band">
    <div class="wrap">
      <h2>Want a case plan for <em>your brand</em>?</h2>
      <p>Tell us your target market and budget \u2014 shortlist, 3D rendering and indicative quotation within one business day.</p>
      <a class="btn primary" href="/rfq">Start Your Brand Upgrade \u2192</a>
    </div>
  </section>
</div>

<footer class="site">
  <div class="wrap">
    <div class="cols">
      <div>
        <div class="brandline">
          <svg class="hex" viewBox="0 0 24 24" fill="none" style="flex:0 0 24px"><path d="M12 1.5 21.5 7v10L12 22.5 2.5 17V7L12 1.5Z" stroke="#B8C439" stroke-width="2.4"/><circle cx="12" cy="11.4" r="3.2" fill="#F7991D"/></svg>
          LIGHT <span class="bdb"><span class="b1">B</span><span class="d">D</span><span class="b2">B</span></span>
        </div>
        <p class="tagline">
          <span class="bdb"><span class="b1">Build</span></span>
          <span class="bdb"><span style="color:var(--muted);font-weight:400;margin:0 6px">\u00b7</span><span class="d">Design</span></span>
          <span class="bdb"><span style="color:var(--muted);font-weight:400;margin:0 6px">\u00b7</span><span class="b2">Brand</span></span><br>
          Your brand co-creation partner for certified wellness product platforms.
        </p>
      </div>
      <div>
        <h4>Quick Links</h4>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/product-platforms">Product Platforms</a></li>
          <li><a href="/brand-co-creation">Brand Co-creation</a></li>
          <li><a href="/design-services">Design Services</a></li>
          <li><a href="/about">About</a></li>
          <li><a href="/case-studies">Case Studies</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="legal">
      <span>\u00a9 2026 LightBDB. All rights reserved.</span>
      <span>LightBDB: Your Brand Co-creation Partner. \u00b7 <a href="/privacy" style="color:var(--muted)">Privacy Policy</a> \u2014 inquiry data is stored securely and used only to respond.</span>
    </div>
  </div>
</footer>

<div class="cookie" id="cookie">
  <p>We use minimal cookies to measure site performance. No tracking for advertising. You can change your choice any time.</p>
  <button onclick="acceptCookie()">Accept</button>
  <button class="ghost" onclick="acceptCookie()">Decline</button>
</div>

<script>
function acceptCookie(){{
  try {{ localStorage.setItem('lbdb_cookie','1'); }} catch(e){{}}
  var c=document.getElementById('cookie'); if(c) c.style.display='none';
}}
try {{ if(localStorage.getItem('lbdb_cookie')) document.getElementById('cookie').style.display='none'; }} catch(e){{}}
</script>
<!-- icp:foot --><div class="icp-foot" style="text-align:center;font-size:12px;line-height:1.9;color:#8b8f7e;padding:14px 16px 26px"><a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">\u7ca4ICP\u59072026117928\u53f7-1</a></div>
</body>
</html>'''

# ---------------------------------------------------------------- 导航/页脚注入（幂等）
NAV_LINK = '<a href="/case-studies">Case Studies</a>'
FOOT_LI = '<li><a href="/case-studies">Case Studies</a></li>'

def inject_nav(html):
    changed = False
    if '/case-studies' not in html:
        # nav: 插在 <a href="/contact">Contact</a> 之前（要求行首空白 + 独占一行，避免误命中注释）
        html2, n1 = re.subn(r'(?m)^(\s*)(<a href="/contact">Contact</a>)$',
                            r'\1' + NAV_LINK + '\n\\1\\2', html)
        # footer: 插在 Quick Links 的 Contact li 之前
        html2, n2 = re.subn(r'(?m)^(\s*)(<li><a href="/contact">Contact</a></li>)$',
                            r'\1' + FOOT_LI + '\n\\1\\2', html2)
        changed = (n1 + n2) > 0
        return html2, changed
    return html, changed

def structure_check(html):
    assert html.lstrip().lower().startswith('<!doctype'), 'missing doctype'
    for t in ('section', 'article', 'table', 'ul', 'li', 'div', 'details'):
        o = len(re.findall(r'<%s[\s>]' % t, html)); c = html.count('</%s>' % t)
        assert o == c, f'tag {t} unbalanced {o}/{c}'
    assert html.count('<!--') == html.count('-->'), 'comment unbalanced'

def main():
    apply_nav = '--link-nav' in sys.argv
    page = build_page()
    structure_check(page)
    out = SITE / 'case-studies.html'
    out.write_text(page, encoding='utf-8')
    print(f'wrote {out} ({len(page)} bytes), cases={len(CASES)}, faqs={len(FAQS)}')
    if apply_nav:
        n_changed = 0
        for f in sorted(SITE.glob('*.html')):
            if f.name in ('404.html', 'case-studies.html'):
                continue
            h = f.read_text(encoding='utf-8')
            h2, changed = inject_nav(h)
            if changed:
                structure_check(h2)
                f.write_text(h2, encoding='utf-8')
                n_changed += 1
                print(f'  nav+footer: {f.name}')
        print(f'nav injected into {n_changed} pages')

if __name__ == '__main__':
    main()
