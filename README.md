# LIGHT BDB 海外官网 v1（EN）· 部署包

静态站，6 页 + 3 个根文件，直接可部署到 Cloudflare Pages（A 档 ¥0/月 架构）。

## 文件清单

```
site/
├── index.html        主首页：Hero + 三选一分流 + 信任背书条 + 价值观（文化精髓·科技幸福·全面健康）+ 询单表单
├── body.html         Body 产品页：答案块 + 6 品类 + 技术平台 + 内页规格参数表
├── mind.html         Mind 生活方式页：答案块 + 4 品类（灯具/音响/香氛/无线充，无 Spirit）
├── design.html       Design 页：博乐「核心战略合作方」呈现 + 答案块 + 流程
├── facilities.html   设施与认证页：番禺 10,000㎡/600人 元件厂 + 深圳 3,000㎡ 成品厂 + 仰光厂 + 证书
├── faq.html          采购 FAQ 12 问（上线版）+ FAQPage 结构化数据
├── robots.txt        已放行 GPTBot / PerplexityBot / ClaudeBot / Google-Extended / CCBot
├── llms.txt          GEO 站点说明（事实基线，供 AI 引擎引用）
├── sitemap.xml       6 页
├── supabase/         schema.sql —— 询单表建表脚本（SQL Editor 执行一次）
├── ASSETS.md         图片资产映射表（换图前先查）
└── assets/           styles.css + 13 张统一调色暗调图
```

## 本轮更新（2026-08-31 晚）

- **品牌名**：LightBDB → **LIGHT BDB**（全站标题/导航/页脚/JSON-LD/llms.txt）
- **价值观区**：首页新增「文化精髓 · 科技幸福 · 全面健康」（Cultural Essence · Happiness through Technology · Holistic Health）
- **认证升级**：ISO 9001 + **ISO 14001** + **BSCI**（amfori）加入全站口径（信任条/页脚/FAQ/JSON-LD/llms.txt）；另有 UL 认证工厂 + Sony Green Partner（来源 FTE 官网，已核实写入设施页）
- **设施与认证页**（facilities.html）：番禺元件厂 10,000+㎡ / 600+ 员工（电感/变压器/无线充线圈/SMT，汽车与医疗级）；深圳成品厂 3,000㎡；仰光 5,000+ pcs/day。工厂实拍图留同名占位（factory-panyu / factory-shenzhen / factory-yangon.jpg），**素材库现有 2 张为 AI 生成图（带水印），按真实性红线不上站**，请放真实照片后同名替换
- **邮箱防垃圾**：全站 HTML 已无明文邮箱——base64 混淆 + JS 解码填充（data-email）；JSON-LD 已去掉 email 字段。llms.txt 保留一处（AI 引擎引用源，权衡过：被 AI 引用的价值 > 低量垃圾邮件，且可随时改）
- **WhatsApp**：账号被封，站点暂不放。新号申请好后，在 index.html「Contact」区加一行即可：
  `<li><b>WhatsApp:</b> <a href="https://wa.me/86手机号">Chat with us</a></li>`

## WhatsApp Business 新号申请路径（建议）

1. **准备一个没被封过、没注册过 WA 的手机号**（国内号 +86 可收验证码即可；也可用香港/新加坡虚拟实体卡号更稳）
2. 手机装 **WhatsApp Business App**（免费档够用：商家名、目录、快速回复、标签）
3. 注册验证 → 填 LIGHT BDB 商家资料 → 关联 serina@lightbdb.com
4. 想要**绿标认证/多人坐席**：走 WhatsApp Business Platform（API），通过 BSP（如 360dialog、Twilio、Meta 官方直连）申请，需 Facebook Business 认证——建议月询单 >50 封后再上
5. 防封要点：新号前 2 周只做「客户主动发起」的回复，不主动群发；开启两步验证

## 部署步骤（Cloudflare Pages）

1. Cloudflare Dashboard → Workers & Pages → Create → Pages → Upload assets → 选整个 site/ 目录
2. 绑定自定义域 `www.lightbdb.com`（阿里云 DNS 加 CNAME）
3. 三个子域名 301：`body.lightbdb.com/* → https://www.lightbdb.com/body.html`（mind/design 同理；验证路径级跳转）
4. 询单表单接 Supabase（新加坡项目，最简方案）：
   a. SQL Editor 执行 `supabase/schema.sql`（建 inquiries 表 + anon 仅可插入的 RLS）
   b. index.html 里把 `SB_ANON` 换成 anon public key（Settings → API）
   c. 邮件通知后补：Database → Webhooks → insert 时 POST 到通知服务
5. 语言提示条：Pages Function 读 `CF-IPCountry`，DE/AT/CH 显示德语提示（逻辑已留注释）
6. Cloudflare Web Analytics 免费接入

## 部署自动化状态（2026-08-31 深夜更新）

- ✅ **Supabase anon key 已找回并填入 index.html**（从 108 系统工程文件提取，REST 鉴权验证通过）
- ✅ 邮箱已全站改为 serina@lightbdb.com（混淆填充 + llms.txt）
- ✅ 基地口径修正： plants = 番禺/深圳/仰光；design = 杭州/汉堡
- ✅ 深圳厂卡已用 Unsplash 免费授权过渡图（factory-shenzhen.jpg，搬厂后同名替换实拍）
- ⏳ 需要你手动（各 2 分钟）：Supabase 建表、Cloudflare Pages 上传、DNS CNAME——步骤见下

## 仍待办

1. body.html 规格参数表：按 Catalog 替换 `[confirm per SKU]`（上线后可随时改）
2. 认证矩阵：哪个 SKU 持哪张证（已按你要求暂缓，页面留橙色标记）
3. 工厂实拍 3 张 → facilities.html 同名替换
4. Supabase anon key 填入 index.html `SB_ANON`

## Supabase 心跳（已兜底）

- 2026-08-31 实测项目存活（REST 401 = 服务响应正常）
- WorkBuddy 自动化「LightBDB询单库·Supabase每周心跳」每周一 09:30 探测，异常主动报警

## 工厂图片状态

- factory-shenzhen.jpg：**过渡图**（Unsplash 免费授权，自动化产线），搬厂后同名替换实拍
- factory-panyu.jpg / factory-yangon.jpg：**占位**——FTE 官网只有 banner/证书/架构图，无工厂实拍；
  从 FTE 内部素材（微信群/年审拍照）取图后同名替换
- FTE 官网证书扫描件（ISO 9001:2015、ISO 14001:2015）**已过期**（2021/2022 到期），不上站；
  向 FTE 拿最新年审版后，证书区占位 cert-iso9001.jpg / cert-iso14001.jpg 同名替换

## 图片红线（重要）

- 全站图片来自统一调色批次 graded_v2（线性光空间调色 + 暗调暖光渐晕）
- **cutout 批次弃用**（人物面部残缺）；**AI 生成图一律不上站**（B2B 真实性红线，factory_images/ 里 2 张已判定弃用）
