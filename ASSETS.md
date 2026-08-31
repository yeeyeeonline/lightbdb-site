# LightBDB 站点图片资产映射（防熵增：替换图片前先查此表）

> 状态图例：✅ 已上站 · ⏸ 已拷贝未引用 · ❌ 弃用
> 权威源：`outputs/assets/healthcare/graded_v2/`（统一调色 + 渐晕，102 张中的 74 张）
> 替换规则：同名覆盖即可（宽高属性需同步改 HTML）；新图先入 graded 通道（线性光空间调色）再上站

## Body（body.html / index.html）

| 站内文件 | 源文件 | 品类 | 状态 |
|---|---|---|---|
| eye-massager.jpg | HC_13_183_1160x879_v2.jpg | 眼部按摩仪（主 Hero 图） | ✅ |
| eye-massager-2.jpg | HC_12_174_751x1009_v2.jpg | 眼部按摩仪（品类卡） | ✅ |
| knee-massager.jpg | HC_25_291_753x1008_v2.jpg | 护膝加热 wraps（品类卡） | ✅ |
| knee-massager-2.jpg | HC_19_246_752x1007_v2.jpg | 护膝（首页 BODY 卡） | ✅ |
| back-belt.jpg | HC_41_450_751x1009_v2.jpg | 腰背加热带 | ✅ |
| abdominal-belt.jpg | HC_29_342_1160x879_v2.jpg | 腹部加热带 | ✅ |
| heated-scarf.jpg | HC_49_531_1160x879_v2.jpg | 加热围巾 | ✅ |
| hand-warmer.jpg | HC_57_591_1160x879_v2.jpg | 暖手宝 | ✅ |

## Mind（mind.html）

| 站内文件 | 源文件 | 品类 | 状态 |
|---|---|---|---|
| mind-light.jpg | LM_00_1097x680.jpeg | 灯具（火光场景） | ✅ |
| mind-audio.jpg | LM_06_1580x988.jpeg | 音响（MINP 心系列） | ✅ |
| mind-candle.jpg | LM_04_1379x899.jpeg | 香氛蜡烛（光系列） | ✅ |
| —（无线充） | 无合适图 | 文字卡占位 | ⏸ 待补图 |

## Design（design.html）

| 站内文件 | 源文件 | 用途 | 状态 |
|---|---|---|---|
| design-case-nir.jpg | BL_10（已压 2000px/q62→164KB） | 设计案例卡 | ✅ |

## 信任/证书

| 站内文件 | 源文件 | 用途 | 状态 |
|---|---|---|---|
| certificates.jpg | DG_81_2560x1433.jpeg | 证书墙（CNAS/CE/FCC/PSE/RoHS） | ⏸ 已拷贝未引用——留给后续 Facilities/证书页 |

## 弃用

| 目录 | 原因 |
|---|---|
| healthcare/cutout/（22 张） | ❌ 人物面部残缺、光晕、衣物丢失，一律不上站 |
| healthcare/graded/（v1，74 张） | ❌ 被 graded_v2 取代，仅存档 |
| YK_13–17（AI 生成图） | ❌ 禁止上站（B2B 真实性红线） |
