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

ORG_ID = f"{BASE}/#organization"

# ---------------------------------------------------------------- 数据结构

ABOUT_GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "LightBDB",
            "legalName": "LIGHT BRAND DESIGN BUSINESS (SHENZHEN) CO., LTD.",
            "url": BASE,
            "description": (
                "Wellness and lifestyle product manufacturer with in-house design: "
                "three plants (Panyu, Shenzhen, Yangon) and two design centers (Hangzhou, Hamburg)."
            ),
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
        }
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
    """第三方信源链。只收站点 case-studies 页已声明的报道。

    收录依据 = 页面既有表述 + 本机可达性核验。未通过核验的一律不收：
      ✅ 200  TechAcute / Australian Giftguide / Shanghai Youth Daily(why.com.cn)
      ⚠️ 403  专利库(justia) 与 Indiegogo —— 反爬拦截，非死链，URL 沿用页面原链
      ❌ 未收  Boing Boing —— 页面给的 URL 实测 404，且本机查不到 archive.org 快照，
               无法判定是失效还是反爬，按「写不出出处的一律不写」处理。
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
            "name": "Australian Giftguide trade-press coverage with founder interview",
            "datePublished": "2017-10",
            "publisher": {
                "@type": "Organization",
                "name": "Australian Giftguide",
                "url": "https://www.giftguideonline.com.au/",
            },
            "url": "https://www.giftguideonline.com.au/",
        },
        {
            "@type": "NewsArticle",
            "name": "Shanghai Youth Daily designer interview",
            "datePublished": "2016-08",
            "publisher": {"@type": "Organization", "name": "Shanghai Youth Daily"},
            "url": "http://app.why.com.cn/epaper/webpc/shzk/html/2016-08/02/content_6146.html",
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
                "manufacturer": {"@id": ORG_ID},
                "subjectOf": _sources(),
            },
            {
                "@type": "Organization",
                "@id": ORG_ID,
                "name": "LightBDB",
                "url": BASE,
            },
        ],
    }


LLMS_TAIL = """
## External sources (verifiable third-party records)

> Third-party records a reader — or a model — can open and check for themselves. Every item below is a record kept by somebody other than us.

- US design patent D1,024,003 S — Bluetooth speaker design, granted April 2024 — https://patents.justia.com/patent/D1024003
- TechAcute, May 2020 — "Maglamp: The Happiness Lamp with Wireless Charging" — https://techacute.com/maglamp/
- Australian Giftguide, October 2017 — trade-press coverage with founder interview — https://www.giftguideonline.com.au/
- Shanghai Youth Daily, August 2016 — designer interview — http://app.why.com.cn/epaper/webpc/shzk/html/2016-08/02/content_6146.html
- Indiegogo campaign "Home Tree — Light From The Forest" — https://www.indiegogo.com/en/projects/hometreetech/home-tree-light-from-the-forest--2
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
    p = ROOT / "llms.txt"
    raw = p.read_text(encoding="utf-8", errors="ignore")
    if MARKER in raw:
        i = raw.index(MARKER)
        merged = raw[:i] + LLMS_TAIL.strip("\n") + f"\n{MARKER}\n"
        print(f"  ↻ 重建 llms.txt 外源区块（{len(LLMS_TAIL)} 字节）")
        if apply:
            p.write_text(merged, encoding="utf-8")
        return True
    merged = raw.rstrip() + "\n" + LLMS_TAIL + f"\n{MARKER}\n"
    print(f"  ✓ 将追加 llms.txt 外源区块（+{len(LLMS_TAIL)} 字节）")
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
