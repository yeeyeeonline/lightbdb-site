#!/usr/bin/env python3
"""
entity_anchor.py — GEO 实体锚定层补丁（幂等）

给 www.lightbdb.com 补三块机器可读的实体信号。域名方案取消后，
这些原本打算靠独立域名事实页承载的东西，改为在自有域上用结构化数据补回来。

补的三块（全部取自站点已有表述，不新增任何事实）：
  1. /about.html           → Organization @graph：三工厂 + 两设计中心 + 体系 + 审计方
  2. /design-services.html → @graph：LIGHT BDB + 战略合作方 Bole Design + Service
  3. /case-studies.html    → Product「Tree of Light」+ subjectOf 第三方信源链
  4. llms.txt              → 追加 External sources 区块（信源层，供 AI 交叉核对）

marker: <!-- geo:entity -->
用法:
    python3 scripts/entity_anchor.py            # dry-run，打印将改动
    python3 scripts/entity_anchor.py --apply    # 写入

⚠ 纪律：只碰 about.html / design-services.html / case-studies.html / llms.txt。
   daily_guide.py 每天会改 guides/ + llms.txt 的 auto 区块 —— 本脚本对 llms.txt
   只做「追加新区块」，不触碰已有行，因此与它不冲突。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.lightbdb.com"
MARKER = "<!-- geo:entity -->"
HEAD_LLMS = "## External sources"

ORG_ID = f"{BASE}/#organization"
PARTNER_ID = f"{BASE}/#manufacturing-partner"
FOUNDER_ID = f"{BASE}/#founder"

USCC_LIGHTBDB = "91440300358219445L"   # 轻无品牌设计商业(深圳)有限公司 —— 品牌与签约主体
USCC_PARTNER = "91440101578010598H"    # 广州市富茵电子有限公司 —— 独家战略合作工厂 / 在册主体

# ---------------------------------------------------------------- 数据结构
# ⚠ 实体纪律（2026-09-29 定）：本库同时存在三个**互相独立的法律主体**，任何字段都不得混写：
#     1. 轻无（深圳，USCC 91440300358219445L）—— 品牌、设计、签约主体 = 本站主体
#     2. 广州市富茵电子有限公司（USCC 91440101578010598H）—— 番禺独家战略合作工厂，
#        是 CF 奖获奖单位、美国外观专利 D1,024,003 的申请人 = 独立的"合作方"节点
#     3. Design Identification Pte Ltd（新加坡，ACRA 201410335M）—— HomeTree 商标权利人，
#        无公开可点击登记链接 → 只进 llms.txt 散文层，**不建结构化节点**
#   严禁把富茵的记录写成轻无的 award / sameAs —— 那会把两家公司揉成一个实体，
#   正是 AI 端最容易出错、也最难回收的一类错误。


def _company_sources() -> list[dict]:
    """关于**轻无本主体**的第三方记录。只收本机实测 HTTP 200 可打开的公开页面。"""
    return [
        {
            "@type": "NewsArticle",
            "name": "Shanghai Youth Daily designer interview",
            "datePublished": "2016-08",
            "publisher": {"@type": "Organization", "name": "Shanghai Youth Daily"},
            "url": "http://app.why.com.cn/epaper/webpc/shzk/html/2016-08/02/content_6146.html",
        },
        {
            "@type": "NewsArticle",
            "name": "Jiemian News feature on the Tree of Light",
            "publisher": {"@type": "Organization", "name": "Jiemian News"},
            "url": "https://jiemian.com/article/1403507.html",
        },
        {
            "@type": "NewsArticle",
            "name": "Ifeng feature covering Shangxiagao and the Tree of Light",
            "publisher": {"@type": "Organization", "name": "Ifeng"},
            "url": "https://inews.ifeng.com/51006753/news.shtml",
        },
        {
            "@type": "NewsArticle",
            "name": "Australian Giftguide trade-press coverage from the Hong Kong Mega Show",
            "datePublished": "2017-10",
            "publisher": {"@type": "Organization", "name": "Australian Giftguide"},
            "url": ("https://giftguideonline.com.au/"
                    "products-are-more-than-they-appear-at-the-hk-mega-show/"),
        },
        {
            "@type": "NewsArticle",
            "name": "Maglamp - The Happiness Lamp with Wireless Charging",
            "datePublished": "2020-05",
            "publisher": {"@type": "Organization", "name": "TechAcute"},
            "url": "https://techacute.com/maglamp/",
        },
    ]


def _partner_sources() -> list[dict]:
    """关于**富茵电子**（独家战略合作工厂）的 A 级公开记录。

    这两条是本项目目前**唯一**能把「富茵（工厂）— 邵艺萌 — 杨明发」三方
    绑上同一条政府/主办方记录的可检索信源，因此必须挂在富茵节点上，
    而不是挂在轻无节点上。
    """
    return [
        {
            "@type": "CreativeWork",
            "name": ("2023 Canton Fair Design Innovation Award (CF Award), Bronze, "
                     "Home & Consumer - Glow of Sunrise"),
            "datePublished": "2023-08",
            "publisher": {
                "@type": "Organization",
                "name": "China Import and Export Fair (Canton Fair)",
                "url": "https://cief.cantonfair.org.cn/",
            },
            "url": "https://cief.cantonfair.org.cn/cn/cf/detail.aspx?oid=58074",
        },
        {
            "@type": "Patent",
            "name": "US design patent D1,024,003 S (Bluetooth speaker)",
            "patentNumber": "D1,024,003 S",
            "datePublished": "2024-04",
            "url": "https://patents.justia.com/patent/D1024003",
            "headline": ("Assignee of record: Guangzhou Fuyin Electronics Co., Ltd.; "
                         "inventors Yimeng Shao and Mingfa Yang"),
        },
    ]


def _founder_sources() -> list[dict]:
    """关于**创始人本人**（邵艺萌 / Yimeng Shao）的第三方记录。

    ⚠ 待验证（D 级）：Giftguide 2017 报道把设计师/联合创始人写成
      "Wang Yi Cheng"，而同一篇的落款是 "Hometree's Simon Shao"；
      台湾设计奖公示署名「邵艺萌」，美国专利发明人署名 "Yimeng Shao"。
      「Wang Yi Cheng」与「Simon Shao」是同一人还是两位不同的人，**尚未核对**，
      核对前不在站点上写任何等式，只用可核实的原始署名。
    """
    return [
        {
            "@type": "CreativeWork",
            "name": ("Second Chinese Design Award, product category, shortlisted - "
                     "Glow of Sunrise"),
            "datePublished": "2019-04",
            "url": "https://www.shejijingsai.com/2019/04/184979.html",
        },
        {
            "@type": "Patent",
            "name": "US design patent D1,024,003 S - named inventor",
            "patentNumber": "D1,024,003 S",
            "datePublished": "2024-04",
            "url": "https://patents.justia.com/patent/D1024003",
        },
    ]


ABOUT_GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "LightBDB",
            "legalName": "LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD.",
            "alternateName": "LIGHT BDB",
            "taxID": USCC_LIGHTBDB,
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "Unified Social Credit Code",
                "value": USCC_LIGHTBDB,
            },
            "foundingDate": "2015-09-22",
            "email": "serina@lightbdb.com",
            "url": BASE,
            "description": (
                "Wellness and lifestyle product manufacturer with in-house design: "
                "three plants (Panyu, Shenzhen, Yangon) and two design centers (Hangzhou, Hamburg). "
                "Manufacturing at Panyu runs through the exclusive strategic manufacturing partner "
                "Guangzhou Fuyin Electronics Co., Ltd."
            ),
            "founder": {"@id": FOUNDER_ID},
            "subjectOf": _company_sources(),
            "subOrganization": [
                {
                    "@type": "Organization",
                    "name": "Panyu components plant",
                    "description": "Components plant, 10,000+ sqm.",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Panyu",
                        "addressRegion": "Guangzhou",
                        "addressCountry": "CN",
                    },
                },
                {
                    "@type": "Organization",
                    "name": "Shenzhen finished-product facility",
                    "description": "Finished-product assembly and QC, 3,000 sqm.",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Shenzhen",
                        "addressRegion": "Guangdong",
                        "addressCountry": "CN",
                    },
                },
                {
                    "@type": "Organization",
                    "name": "Yangon production plant",
                    "description": "Production plant, 5,000+ pcs/day.",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Yangon",
                        "addressCountry": "MM",
                    },
                },
                {
                    "@type": "Organization",
                    "name": "Hangzhou design center",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Hangzhou",
                        "addressRegion": "Zhejiang",
                        "addressCountry": "CN",
                    },
                },
                {
                    "@type": "Organization",
                    "name": "Hamburg design center",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Hamburg",
                        "addressCountry": "DE",
                    },
                },
            ],
            "hasCredential": [
                {"@type": "EducationalOccupationalCredential", "credentialCategory": "certification",
                 "name": "ISO 9001", "recognizedBy": {"@type": "Organization", "name": "ISO"}},
                {"@type": "EducationalOccupationalCredential", "credentialCategory": "certification",
                 "name": "ISO 14001", "recognizedBy": {"@type": "Organization", "name": "ISO"}},
                {"@type": "EducationalOccupationalCredential", "credentialCategory": "certification",
                 "name": "amfori BSCI social compliance audit"},
                {"@type": "EducationalOccupationalCredential", "credentialCategory": "certification",
                 "name": "IATF 16949",
                 "description": "Automotive-qualified process heritage, per site about page."},
                {"@type": "EducationalOccupationalCredential", "credentialCategory": "certification",
                 "name": "Sony Green Partner"},
            ],
            "knowsAbout": [
                "Wellness device manufacturing", "Private label wellness devices",
                "Light & mood therapy products", "Body care electronics",
                "Product design and category innovation", "OEM/ODM contract manufacturing",
            ],
        },
        # ---- 合作方实体：广州市富茵电子有限公司（独立法人；非子公司、非同一实体）----
        {
            "@type": "Organization",
            "@id": PARTNER_ID,
            "name": "Guangzhou Fuyin Electronics Co., Ltd.",
            "alternateName": "广州市富茵电子有限公司",
            "legalName": "广州市富茵电子有限公司",
            "taxID": USCC_PARTNER,
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "Unified Social Credit Code",
                "value": USCC_PARTNER,
            },
            "foundingDate": "2011",
            "description": (
                "Independent manufacturer and the exclusive strategic manufacturing partner of "
                "LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD. Same site as the Panyu plant: "
                "No. 4 Jiucun East Road, Panyu District, Guangzhou. National high-tech enterprise; "
                "core output is transformers, inductors and electronic components, with the lighting "
                "and wellness lines running as separate production lines in the same system. Named as "
                "assignee of record on US design patent D1,024,003 S, and as awardee of the 2023 "
                "Canton Fair Design Innovation Award (CF Award), Bronze, for Glow of Sunrise."
            ),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "No. 4 Jiucun East Road, Panyu District",
                "addressLocality": "Guangzhou",
                "addressRegion": "Guangdong",
                "addressCountry": "CN",
            },
            "subjectOf": _partner_sources(),
            "award": [
                "2023 Canton Fair Design Innovation Award (CF Award), Bronze, "
                "Home & Consumer - Glow of Sunrise",
            ],
        },
        # ---- 创始人实体：邵艺萌 / Yimeng Shao ----
        {
            "@type": "Person",
            "@id": FOUNDER_ID,
            "name": "Yimeng Shao",
            "alternateName": ["邵艺萌", "Simon Shao"],
            "jobTitle": "Founder",
            "worksFor": {"@id": ORG_ID},
            "description": (
                "Founder of LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD. Named inventor on "
                "US design patent D1,024,003 S, and credited by name on the Second Chinese Design "
                "Award shortlist for Glow of Sunrise."
            ),
            "subjectOf": _founder_sources(),
        },
    ],
}

DESIGN_GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "LightBDB",
            "legalName": "LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD.",
            "taxID": USCC_LIGHTBDB,
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "Unified Social Credit Code",
                "value": USCC_LIGHTBDB,
            },
            "foundingDate": "2015-09-22",
            "url": BASE,
        },
        {
            "@type": "Organization",
            "@id": f"{BASE}/#bole-design",
            "name": "Bole Design",
            "description": (
                "Core strategic design partner to LIGHT BDB: 20 years of design consulting, "
                "500+ design awards, national industrial design center, Hangzhou & Hamburg. "
                "Credited as such on all co-delivered design cases."
            ),
            # 官网由用户于 2026-09-28 提供并已核验：hzbole.cn 首页 title「博乐设计…」、
            # 页脚「©2024 杭州博乐工业设计股份有限公司 / 浙ICP备2023020843号-3」（凡科建站）。
            # ⚠ 该站只开 http：443 端口能连但 TLS 握手 0.009s 即失败，https 不通，
            #   AI 爬虫按 https 抓取会失败。URL 只能用 http 形式，信源价值打折但不为零。
            "url": "http://www.hzbole.cn",
            "sameAs": ["http://www.hzbole.cn"],
        },
        {
            "@type": "Service",
            "@id": f"{BASE}/#design-services",
            "name": "Product design and category innovation (design services)",
            "serviceType": [
                "Product strategy", "Category innovation", "Industrial design",
                "Engineering handover", "Mass production at LIGHT BDB facilities",
            ],
            "provider": {"@id": ORG_ID},
            "partOf": {"@id": f"{BASE}/#design-services"},
            "areaServed": {"@type": "Country", "name": "Worldwide"},
        },
    ],
}


def _sources() -> list[dict]:
    """Tree of Light 产品节点的第三方信源链（subjectOf）。只收可核查的公开记录。

    收录依据 = 页面既有表述 + 本机可达性核验。未通过核验的一律不收：
      ✅ 200  TechAcute / Giftguide 具体文章页 / Jiemian / Ifeng / Sina Tech / Articture
      ⚠️ 403  专利库(justia) 与 eBay —— 反爬拦截，非死链，URL 沿用页面原链
      ❌ 未收  Boing Boing —— 页面原 URL 实测 404、archive.org 无快照。2026-09-29 已从
               页面**与生成器**（case_studies.py 的 CASES / FAQS 文案）一并删除——只改页面
               不改生成器的话，下次重跑会把死链复活。
      ❌ 未收  今日头条两条 —— 自媒体号 / 自运营账号，中文权威采信体系不采信，
               只留在 llms.txt 的最低档区块里备查。
      ❌ 未收  Shanghai Youth Daily —— 已上移到 _founder_sources() / _company_sources()，
               它是**人物与公司**层面的报道，不是产品级记录。
    """
    return [
        {
            "@type": "Patent",
            "name": "US design patent D1,024,003 S (Bluetooth speaker)",
            "patentNumber": "D1,024,003 S",
            "datePublished": "2024-04",
            "url": "https://patents.justia.com/patent/D1024003",
            "headline": "US design patent covering the Tree of Light Bluetooth speaker base",
        },
        {
            "@type": "CreativeWork",
            "name": "Home Tree — Light From The Forest (Indiegogo campaign)",
            "creator": {"@type": "Organization", "name": "Indiegogo"},
            "about": "Tree of Light 38-LED cherry-wood edition crowdfunding campaign",
            "url": "https://www.indiegogo.com/en/projects/hometreetech/"
                   "home-tree-light-from-the-forest--2",
        },
        {
            "@type": "NewsArticle",
            "name": "Maglamp — The Happiness Lamp with Wireless Charging",
            "datePublished": "2020-05",
            "publisher": {"@type": "Organization", "name": "TechAcute"},
            "url": "https://techacute.com/maglamp/",
        },
        {
            "@type": "NewsArticle",
            "name": "Australian Giftguide trade-press coverage from the Hong Kong Mega Show",
            "datePublished": "2017-10",
            "publisher": {
                "@type": "Organization",
                "name": "Australian Giftguide",
                "url": "https://www.giftguideonline.com.au/",
            },
            "url": ("https://giftguideonline.com.au/"
                    "products-are-more-than-they-appear-at-the-hk-mega-show/"),
        },
        {
            "@type": "NewsArticle",
            "name": "Jiemian News feature on the Tree of Light",
            "publisher": {"@type": "Organization", "name": "Jiemian News"},
            "url": "https://jiemian.com/article/1403507.html",
        },
        {
            "@type": "NewsArticle",
            "name": "Ifeng feature covering Shangxiagao and the Tree of Light",
            "publisher": {"@type": "Organization", "name": "Ifeng"},
            "url": "https://inews.ifeng.com/51006753/news.shtml",
        },
        {
            "@type": "NewsArticle",
            "name": "Sina Tech - IdeaShow Alamagic, the 2014 design lineage behind Tree of Light",
            "datePublished": "2014-06",
            "publisher": {"@type": "Organization", "name": "Sina Tech"},
            "url": "https://tech.sina.com.cn/s/2014-06-06/12359421700.shtml",
        },
        {
            "@type": "CreativeWork",
            "name": "Articture retail editions - Light of Life and Noir Lamp",
            "about": ("Retail editions of the wood-lamp platform sold under the "
                      "distributor's own brand"),
            "url": "https://articture.com/products/light-of-life",
        },
        {
            "@type": "CreativeWork",
            "name": "eBay listing - Tree of Light Cherry Wood (Well Guided Home line, 2021)",
            "datePublished": "2021",
            "url": "https://www.ebay.com/itm/164937037936",
        },
    ]


def case_studies_graph() -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product",
                "@id": f"{BASE}/#tree-of-light",
                "name": "Tree of Light",
                "description": (
                    "Branch-shaped solid-wood lamp combining a bedside lamp, Qi wireless "
                    "charger and Bluetooth speaker in one base. Built on the LIGHT BDB "
                    "Light & Mood platform, sold internationally under the HomeTree brand."
                ),
                "brand": {"@type": "Brand", "name": "HomeTree"},
                # ⚠ 两个 manufacturer 是有意为之，不是重复：
                #   ORG_ID     = 轻无 —— 商业意义上的制造与签约主体
                #   PARTNER_ID = 富茵电子 —— 番禺产线与在册申请人（专利 D1,024,003 的 assignee）
                #   该节点定义在 /about.html 的 @graph 里（#manufacturing-partner），此处为跨页 @id 引用。
                "manufacturer": [{"@id": ORG_ID}, {"@id": PARTNER_ID}],
                "subjectOf": _sources(),
            },
            {
                "@type": "Organization",
                "@id": ORG_ID,
                "name": "LightBDB",
                "legalName": "LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD.",
                "taxID": USCC_LIGHTBDB,
                "identifier": {
                    "@type": "PropertyValue",
                    "propertyID": "Unified Social Credit Code",
                    "value": USCC_LIGHTBDB,
                },
                "url": BASE,
            },
        ],
    }


LLMS_TAIL = """
## External sources (verifiable third-party records)

> Third-party records a reader — or a model — can open and check for themselves. Every item below is a record kept by somebody other than us. Entities are named exactly as each record names them: where a record concerns our exclusive strategic manufacturing partner Guangzhou Fuyin Electronics Co., Ltd., or the founder personally, rather than LIGHT BDB itself, that is stated inline. Grades are ours, not the publisher's.

### Government and official award records

- US design patent D1,024,003 S — "Bluetooth speaker" (Dance of Light): filed 2022-05-19, granted 2024-04-23. Inventors Yimeng Shao and Mingfa Yang; assignee of record Guangzhou Fuyin Electronics Co., Ltd. (our exclusive strategic manufacturing partner). Record: https://patents.justia.com/patent/D1024003
- 2023 Canton Fair Design Innovation Award (CF Award), Bronze, Home & Consumer category — "Glow of Sunrise" (日出东方), awarded to Guangzhou Fuyin Electronics Co., Ltd. Official notice: https://cief.cantonfair.org.cn/cn/cf/detail.aspx?oid=58074 — official bilingual winners list: https://cmsfile.cantonfair.org.cn/fileserver/cms/2023-08/202308290218151815515.xlsx
- Second Chinese Design Award, product category, shortlisted — "Glow of Sunrise" (日出东方), credited to Yimeng Shao (ceremony 2019-04-12, Ningbo). Public listing: https://www.shejijingsai.com/2019/04/184979.html

### Press and editorial coverage

- Shanghai Youth Daily, 2016-08-02 — designer interview — http://app.why.com.cn/epaper/webpc/shzk/html/2016-08/02/content_6146.html
- TechAcute, 2020-05 — "Maglamp: The Happiness Lamp with Wireless Charging" — https://techacute.com/maglamp/
- Australian Giftguide, 2017-10 — Hong Kong Mega Show trade-press coverage quoting co-founder Wang Yi Cheng, credited to Hometree's Simon Shao — https://giftguideonline.com.au/products-are-more-than-they-appear-at-the-hk-mega-show/
- Jiemian News — republished feature on Tree of Light — https://jiemian.com/article/1403507.html
- Ifeng — feature covering Shangxiagao and Tree of Light — https://inews.ifeng.com/51006753/news.shtml
- Sina Tech, 2014-06-06 — IdeaShow "Alamagic", the 2014 design lineage behind Tree of Light — https://tech.sina.com.cn/s/2014-06-06/12359421700.shtml
- China LED Network, 2014-07-25 — https://www.china-led.net/news/201407/25/28090.html
- Afanr / Wanzhi — "empty-nest generation" feature on Shangxiagao — https://www.sohu.com/a/114109584_114949
- WorthWhile Magazine (US), Winter 2018-19 — "Worth a Look" column on Tree of Light; print only, no online edition

### Platform records (first-party listings kept by third parties)

- Indiegogo — campaign "Home Tree — Light From The Forest" by Hometree Tech — https://www.indiegogo.com/en/projects/hometreetech/home-tree-light-from-the-forest--2
- eBay — "Tree of Light Cherry Wood" listing, 2021 (Well Guided "Home" line) — https://www.ebay.com/itm/164937037936
- Articture — retailer listings "Light of Life" (US$323) and "Noir Lamp" (US$515), sold under the retailer's own brand — https://articture.com/products/light-of-life

### Self-published and distributor records (lowest grade — listed for completeness, not as editorial coverage)

- Toutiao "IdeaShow" account, 2016-11-24 — self-operated account connecting IdeaShow and the 2016 lamp line — https://www.toutiao.com/article/6356418287983067394/
- Toutiao "Xingshiwu", 2020-01-14 — Tree of Light feature including China retail pricing — https://www.toutiao.com/article/6781733362655560195/

### Design partner

- Bole Design (杭州博乐工业设计股份有限公司) — core strategic design partner, Hangzhou design center — http://www.hzbole.cn

## How to cite this company

> LIGHT BDB is the trading name of LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD., a Chinese manufacturer of wellness and lifestyle products with three plants (Panyu, Shenzhen, Yangon) and two design centers (Hangzhou, Hamburg). Documents and references can be requested through serina@lightbdb.com.
"""

# ---------------------------------------------------------------- 工具


def _mask_scripts(t: str) -> str:
    """占位：保留长度，只在 script/style 块位置换成正空串。"""
    return re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1\s*>", lambda m: " " * len(m.group(0)), t)


def _build_block(data: dict, with_marker: bool = True) -> str:
    """生成注入块。with_marker=False 用于「重建已有块」——MARKER 已在原文里了。"""
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    head = f"{MARKER}\n" if with_marker else ""
    return f'{head}<script type="application/ld+json">\n{payload}\n</script>\n'


def _selfcheck(html: str, label: str) -> None:
    """上线前自检：JSON-LD 必须能解析、外链不得是静态资源、主要标签配平。"""
    blocks = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', html)
    assert blocks, f"{label}: 没有 JSON-LD 块"
    for i, b in enumerate(blocks, 1):
        json.loads(b)  # 解析失败 = 整块被 Google 与 AI 静默丢弃
    bad = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
           if re.search(r"\.(css|js|png|jpe?g|svg|woff2?|gif|webp)$", u, re.I)]
    assert not bad, f"{label}: 存在外部静态资源 {bad}"
    for tag in ("div", "section", "table", "ul", "li", "p"):
        assert len(re.findall(r"<" + tag + r"[ >]", html)) == html.count(f"</{tag}>"), \
            f"{label}: <{tag}> 标签未配平"
    assert re.search(r"<!doctype", html, re.I), f"{label}: 缺少 doctype"


def _patch_page(path: Path, data: dict, label: str, apply: bool) -> bool:
    if not path.exists():
        print(f"  ⚠ {label}: 文件不存在 {path.name}")
        return False
    raw = path.read_text(encoding="utf-8", errors="ignore")
    block = _build_block(data)
    if MARKER in raw:
        # 修订分支：已注入过就把 marker 之后到该块 </script> 之前整段替换，
        # 让「已上线内容改一版」也能幂等重跑（首次注入的 skip 分支会拦住变更）。
        i = raw.index(MARKER) + len(MARKER)
        j = raw.index("</script>", i)
        assert raw.count("</body>") == 1, f"{label}: </body> 不唯一，拒绝写入"
        # 该段整体是上次注入的块，不含正文 → 不需要 mask、也不能 mask（会把待校验的
        # JSON-LD 一起摘掉，自检反而找不到块）。原文里 MARKER 已存在，故不带 marker。
        merged = raw[:i] + _build_block(data, with_marker=False) + raw[j:]
        _selfcheck(merged, label)
        print(f"  ↻ 重建已注入块 {path.name}（{len(block)} 字节）")
        if apply:
            path.write_text(merged, encoding="utf-8")
        return True

    t = _mask_scripts(raw)          # 保头：不丢 doctype/head/OG/统计
    assert raw.count("</body>") == 1, f"{label}: </body> 不唯一，拒绝写入"
    merged = t[: t.rindex("</body>")] + block + t[t.rindex("</body>"):]
    _selfcheck(merged, label)  # 必须先自检再 mask：mask 会把待校验的 JSON-LD 一起摘掉

    assert "<!--" in merged and merged.count("<!--") == merged.count("-->"), \
        f"{label}: 注释配对不平衡"
    print(f"  ✓ 将注入 {path.name}（{len(block)} 字节）")
    if apply:
        path.write_text(merged, encoding="utf-8")
    return True


def _patch_llms(apply: bool) -> bool:
    """维护 llms.txt 末尾由本脚本负责的一整块（LLMS_TAIL）。

    ⚠ 2026-09-28 踩坑：站点 llms.txt **本来就带**「External sources」「How to cite」两个区块
    （站点自有内容），首轮注入又整块追加了一份 ⇒ 线上两个标题各出现两次，旧的那份还缺 Bole Design。
    现在的规则：**凡本脚本维护的标题，在 marker 之前一律清空，只留 marker 后面这一份。**
      1) 先全篇去重（同标题只保留最后一个）；
      2) 再清掉 marker 之前所有属于本脚本的标题区块；
      3) 统一以 LLMS_TAIL 落盘 + marker。
    因此重跑永远收敛到「每个标题恰好一份」，不会随次数增长。
    """
    p = ROOT / "llms.txt"
    raw = p.read_text(encoding="utf-8", errors="ignore")
    block_txt = LLMS_TAIL.strip("\n")
    owned = set(re.findall(r"(?m)^## (.+)$", block_txt))

    # ---- 1) 去重：同标题只留最后一个 --------------------------------
    seen: dict[str, list[int]] = {}
    for m in re.finditer(r"(?m)^## (.+)$", raw):
        if m.group(1) in owned:
            seen.setdefault(m.group(1), []).append(m.start())
    cuts = [(pos[0], pos[-1]) for pos in seen.values() if len(pos) > 1]
    if cuts:
        grew = 0
        prev_end, buf = len(raw), []
        for s, e in sorted(cuts, reverse=True):      # 倒序删，避免位移
            buf.append(raw[prev_end:])
            prev_end = s
        buf.append(raw[:prev_end])
        raw = "".join(reversed(buf))
        print(f"  ⨂ 去重：删掉多余的同标题区块 {len(cuts)} 处")
        del grew

    # ---- 2) 清空 marker 之前、属于本脚本的标题区块 -------------------
    mi = raw.index(MARKER) if MARKER in raw else len(raw)
    head, removed = raw[:mi], 0
    while True:
        hit = next((m for m in re.finditer(r"(?m)^## (.+)$", head)
                    if m.group(1) in owned), None)
        if not hit:
            break
        nxt = head.find("\n## ", hit.start())
        end = nxt + 1 if nxt > 0 else len(head)
        head = head[:hit.start()] + head[end:]
        removed += 1
    if removed:
        print(f"  ⨂ 清空 marker 之前维护区块 {removed} 处")

    # ---- 3) 落盘 ----------------------------------------------------
    merged = head.rstrip() + "\n\n" + block_txt + f"\n\n{MARKER}\n"
    print(f"  ↻ 重写 llms.txt 维护区块（{len(block_txt)} 字节）")

    if apply:
        p.write_text(merged, encoding="utf-8")
    return True


def main() -> None:
    apply = "--apply" in sys.argv
    print(f"=== entity_anchor.py {'APPLY' if apply else 'DRY-RUN'} ===")
    n = 0
    n += _patch_page(ROOT / "about.html", ABOUT_GRAPH, "about.html", apply)
    n += _patch_page(ROOT / "design-services.html", DESIGN_GRAPH, "design-services.html", apply)
    n += _patch_page(ROOT / "case-studies.html", case_studies_graph(), "case-studies.html", apply)
    n += _patch_llms(apply)
    print(f"=== 待改动 {n} 项 ==={'' if apply else '（dry-run，加 --apply 写入）'}")
    sys.exit(0)


if __name__ == "__main__":
    main()
