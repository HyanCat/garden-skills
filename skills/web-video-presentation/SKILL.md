---
name: web-video-presentation
description: 把一篇文章或口播稿，做成 16:9 视频。**默认产出 Remotion 项目 + `npx remotion render` 直接出 MP4**（帧精确，无录屏伪影）；用户明确要"可点击现场演示"时才走 Vite + 网页录屏旧路径。流程：原始文章 → **一次产出**口播稿 + outline 开发计划 → 用户**一次对齐** 5 件事（稿子 / outline / 主题 / 素材 / 开发模式）→ 视频开发（逐章 / 顺序 / 并行）→ 音频合成（MiniMax / DMXAPI 兼容）→ 渲染 MP4。**outline 只规划节奏与信息密度，不规划动画** —— 动画由章节开发时按 PRINCIPLES + ANTI-AI 法则即时设计。每个 step = 口播稿的一个节拍，每一步独占整屏。适用场景：把口播稿 / 文章做成发布级视频（B 站 / YouTube / 视频号），有电影感的产品 / talk demo，参数化重渲（i18n / A/B 变体）。本 Skill 沉淀的是设计方法论 + 协作流程 —— 不绑定任何特定样式 / 字体 / 颜色 —— 因此能复用到任意主题与美学。
---

# Web Video Presentation

把一篇文章或口播稿，一步步做成 16:9 视频。**默认走 Remotion 路径**：
React + frame-based 动画 → `npx remotion render` 直出 MP4，**不需要屏幕录制**。

> **何时不走 Remotion**：用户明确要"可点击的现场演示 / 网页 demo"——
> 这时回退到 Vite + 网页 + Auto 录屏的旧路径（详见 [`RECORDING.md`](references/RECORDING.md)）。
> 其它情况（要发布到视频平台 / 要 mp4 文件 / 要参数化重渲）一律 Remotion。

## 适用场景

- "我有口播稿 / 一篇文章，帮我做成视频" —— 口播驱动的内容
- 想做 "动态 PPT"
- 16:9 横屏录屏，大字、留白、每屏都要有动效
- 教学 / 产品演示 / keynote 想要电影感
- B 站 / YouTube /抖音视频内容

本 Skill **以方法论 + 协作流程为核心**。脚手架模板提供 token 和原语，
但每个美学决策（配色、字型、动效气质）都应该针对你的主题重新设计 ——
不要照搬。

---

## 工作流总览

```
Phase 1   内容编写
   1.1  识别用户输入
   1.2  一次产出 script.md + outline.md
        （口播稿 + 开发计划）
   ▼
[Checkpoint Plan]      ← 必须停。一次对齐 5 件事：
                         稿子 / outline / 主题 / 素材 / 开发模式
   ▼
Phase 2   视频开发（默认 Remotion；详见 references/REMOTION.md）
   2.1  脚手架（npx create-video --blank --no-tailwind）
   2.2  第 1 章 = 主线程 + 完整版本（强制 anchor）
        ▼
        [硬节点] 用户验收第 1 章（Studio 预览 + 关键帧 still）
        ▼
   2.3  第 2~N 章（按选定模式：A 逐章 / B 顺序 / C 并行）
   ▼
[Checkpoint Audio]     ← 必须停。是否合成音频
   ▼
Phase 3   音频合成（MiniMax / DMXAPI 兼容；详见 references/AUDIO.md）
   3.1  extract-narrations 抽 segments
   3.2  填回 theme.ts 的 AUDIO_DURATIONS_SEC（ffprobe 实测每段时长）
   ▼
Phase 4   成片输出
   Remotion 路径： npx remotion render Full out/full.mp4
   Vite 路径（仅互动 demo）： Auto 模式 + 屏幕录制
```

工作目录约定（agent 在用户当前目录下创建 / 编辑）：

```
my-video/
├── article.md          # 用户给原文时必有 —— 不删！开发阶段画面信息源
├── script.md           # 必有：B 站风格口播稿（决定节拍）
├── outline.md          # 必有：开发计划（章节切分 + 每步内容 + 信息池）
└── presentation/       # 视频项目
    │
    │  ── 默认 Remotion 模式（详见 references/REMOTION.md） ──
    ├── src/
    │   ├── index.ts                # registerRoot 入口
    │   ├── Root.tsx                # Composition 定义（Full + 各章预览）
    │   ├── Composition.tsx         # Full：所有章节 wire up
    │   ├── theme.ts                # ★ 主题 token + AUDIO_DURATIONS_SEC（音频时长真相源）
    │   ├── components/             # 共用（Masthead / MaskReveal / ...）
    │   └── chapters/<NN>-<id>/
    │       ├── <Chapter>.tsx       # 该章节 Composition 组件
    │       └── scenes/             # 每个 step 一个文件（可选拆）
    │           ├── Step0XXX.tsx
    │           └── ...
    ├── public/audio/<id>/<N>.mp3   # 音频（共享 Vite / Remotion 两种模式）
    ├── package.json / tsconfig.json / remotion.config.ts
    │
    │  ── Vite 模式（仅"互动 demo"场景） ──
    ├── src/chapters/<NN>-<id>/<Chapter>.tsx + <Chapter>.css + narrations.ts
    ├── src/registry/chapters.ts
    └── scripts/{extract-narrations.ts, synthesize-audio.py, start-dev.sh}
```

> **唯一真相源**（两种模式都适用）：
> - **step 数源**：Remotion 模式 = `chapters/<id>/scenes/` 目录下文件数 / `narrations.ts` 数组长度；Vite 模式 = 章节 `.tsx` 里 `if (step === N)` 出现的最大 N + 1
> - **音频时长源**：Remotion 模式 = `theme.ts` 的 `AUDIO_DURATIONS_SEC`（ffprobe 实测填进去）；Vite 模式 = Auto 模式按 `<audio>.ended` 事件推进，不需要时长表
>
> 这套约束保证 script / outline / 章节代码 / 音频文件**永远不会漂**。

---

## 硬性自检协议（贯穿整个 Skill）

下面三个产出，每一个**完成后必须走自检 → 修复 → 再汇报 / 推进**：

| 产出 | 自检清单出处 |
|---|---|
| `script.md` | [`SCRIPT-STYLE.md`](references/SCRIPT-STYLE.md) 三层自检（形式 / 风骨 / 念出来） |
| `outline.md` | [`OUTLINE-FORMAT.md`](references/OUTLINE-FORMAT.md) 自检 |
| 单章实现完成 | [`CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md) 完工自检 |

**执行方式**（按能力降级，**优先用更隔离的方式**）：

1. **Agent Teams（最优）**：开一个独立的 reviewer agent，给它"产出文件
   路径 + 对应清单 + 关键上下文"，让它逐项核查并**严格汇报结论**
   （哪几条 pass / 哪几条 fail + 证据 + 改写建议）。
2. **subAgent（次优）**：没有 Teams 能力但能开 subagent 就用 subagent
   走同样流程。
3. **自检（兜底）**：当前 agent 都没有上述能力，就自己**严格逐项**
   核查 —— 不允许目测一遍就放行。

**铁律**：拿到结论后**先按 fail 项把产出改完**，再向用户汇报"做完了
+ 自检结论 + 改了什么"。**直接拿原始结论汇报但不修复 = 违规**。

---

## 各阶段文件读取指南

不同阶段读不同的文件。**长会话里 agent 容易遗忘原则**，特别是
Phase 2.4 的"实现单章"会重复 N 次 —— 每次都要回看核心约束。

| 阶段 | 必读（每次都看） | 一次性看完 / 按需查 |
|---|---|---|
| Phase 1.1-1.2 内容编写 | `references/SCRIPT-STYLE.md` + `references/OUTLINE-FORMAT.md` + `article.md`（用户原文，如有） | —— |
| **Checkpoint Plan 选主题** | —— | `themes/*/theme.json`（动态读全部，列清单 + `bestFor` 推荐 + `descriptionZh`）；`references/THEMES.md`（用户想了解主题系统时） |
| **Phase 2.1 脚手架（Remotion）** | **`references/REMOTION.md`** —— 脚手架（含手动 fallback）/ Composition 顶层结构 / theme.ts 模板 | SKILL.md 本节看一次 |
| **Phase 2.4 实现单章（×N 次，被 2.2 / 2.3 调用）** | **`references/CHAPTER-CRAFT.md`** 单一入口（十条原则 / 反 AI 味 / 字号下限 / 代码硬规则 / 完工自检）+ 当前主题 `themes/<id>/theme.json` + 当前章节 outline.md 段落 + **`article.md` 本章对应段落** + 素材清单 + **Remotion 模式下：`references/REMOTION.md` 的"动画模式：CSS keyframes → interpolate"章节** | `references/EXAMPLES/`（结构示意，不是抄袭模板）；`references/THEMES.md` 完整 token 契约 |
| Phase 3 音频合成 | `references/AUDIO.md`（含 narrations.ts → segments.json → MiniMax / DMXAPI 流程） | —— |
| Phase 4 成片输出 | `references/REMOTION.md` 末尾"渲染命令"（默认）/ `references/RECORDING.md`（仅 Vite 互动 demo 模式） | —— |
| 选 / 造 / 切主题 | —— | `references/THEMES.md` |

> **写章节时只读一份 `CHAPTER-CRAFT.md`**。十条原则 / 开工 self-prompting /
> 决策树 / 反 AI 味反模式 / 完工自检全部并入这一份单一入口。`EXAMPLES/`
> **不是必读** —— 先按内容自由设计，卡壳才翻（按 anchor 翻"形"，不要照搬）。

---

## Phase 1 —— 内容编写（一次产出）

### 1.1 识别用户输入

| 用户给的东西 | 该做的 |
|---|---|
| 原始文章（书面语 / 公众号 / 论文 / 博客） | 一次产出 `script.md` + `outline.md`（1.2），过 Checkpoint Plan |
| 直接的口播稿 / 视频脚本 | 落盘成 `script.md`，一次产出 `outline.md`（1.2 简化版），过 Checkpoint Plan |
| 啥都没有，只说"帮我做个 X 主题的视频" | **反问**：先给一段素材或大纲。Skill 不替用户构思内容 |

### 1.2 一次产出 script.md + outline.md

**两份产出物在一次思考中完成**：

1. **生成 `script.md`**：按 [`references/SCRIPT-STYLE.md`](references/SCRIPT-STYLE.md)
   的规则把 article 转 B 站风口播稿。**保留 `article.md` 不删**——它是
   outline 写信息池和章节实现画面时的细节源（双源原则）。
2. **生成 `outline.md`**：按 [`references/OUTLINE-FORMAT.md`](references/OUTLINE-FORMAT.md)
   规则切章节 + 切 step + 每章首段抽**信息池**。

**outline 的边界**（关键）：

| outline 必须写 | outline 不要写 |
|---|---|
| 章节切分 / 每章 step 数 / 估时 | 具体动画类型（blur clear / wipe / 弹簧） |
| 每步屏幕内容（hero / 数据 / 标语 / 列表项） | CSS 实现手段（filter / SVG / clip-path） |
| 章节级**信息池**：从 article 抽的数字 / 引用 / 案例 / 标签 | 时长数值（不写 ~2.5s / 80~120ms） |
| 步级关系名前缀（"反差对照" / "递进列表" / "金句" 等可选 hint） | 持续微动 / 错峰量等微观节奏 |

> **outline 不写动画的理由**：写死动画 = chapter agent 退化为翻译机；
> 留白让 chapter agent 在每步开工时按 [`CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md)
> 的"内容驱动决策树"自由设计，才有真正的视频感。详见
> [`CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md) Part 0 原则 7。

**落盘后必须先走自检再进 Checkpoint Plan**：按上文「硬性自检协议」分别
对 `script.md` / `outline.md` 执行（优先 Agent Teams → subAgent → 自检），
按结论修复完成后再进入 Checkpoint Plan。

---

## Checkpoint Plan —— 5 件事一次对齐（**硬节点**）

`script.md` + `outline.md` 写完后必须停下来。**用户在这一个节点同时确认
5 件事**。

### agent 此时要做的预备工作

1. 读所有 `themes/*/theme.json` 拿 `nameZh` / `descriptionZh` / `bestFor`
   / `mood` —— **不要硬编码清单**
2. 根据 `script.md` 的内容类型 / 关键词 / 语气，**主动**从主题里挑 2~3
   套**最匹配的推荐**（匹配 `bestFor` 字段）
3. 扫一遍 `outline.md` 末尾"素材清单"部分

### 总结模板（骨架，agent 按情况填充）

```
内容计划写完，产出文件：
  📄 article.md     {若用户给原文则保留}
  📄 script.md      {X} 字 / ~{T} 分钟
  📄 outline.md     {N} 章 / {M} 步 + 每章信息池 + 末尾素材清单

章节速览：
  1. <id>     <章节标题>    <S> 步 ~<T>s
  2. ...

接下来一次对齐 5 件事：

  1. 稿子 (script.md) 要不要改？
     可以直接编辑文件，或口头告诉我修改方向。

  2. 开发计划 (outline.md) 要不要改？重点看：
     - 章节切分 / step 数 / 估时是否合理（合理判断：每章 30~60s）
     - 每步屏幕内容是否清晰
     - 每章首段「信息池」是否有足够的 article 细节供画面挂
     - 末尾素材清单是否完整

  3. 选哪个主题？我的推荐：
     ★ <推荐 1：nameZh (id)> — 因为 <bestFor 命中>；<descriptionZh 摘要>
     ★ <推荐 2 / 推荐 3>
     其它可选：<剩余主题，nameZh + 一句话>
     也可以让我帮你做新主题（详见 themes/THEMES.md）。

  4. 真素材怎么准备？粗看本视频要的图：<列粗略清单>
     a) 我从 <现有素材路径> 帮你挑   b) 你自己提供   c) 全部 placeholder

  5. 开发模式选哪个？

     **第 1 章无论哪种模式都必须主线程做完 + 用户验收**（强制 anchor）。
     差异在第 2 章及之后：

     A) 默认 · 逐章确认（推荐）
        每章做完都暂停验收 → 风险可控 / 节奏最稳
     B) 第 1 章后顺序开发（不并行）
        第 2~N 章主线程顺序做完后统一验收 → 速度中 / 适合 agent 不支持并行
     C) 第 1 章后并行开发（subagent）
        第 2~N 章用 subagent 并行 → 最快 / 用户控并行数（一次几章）
        ⚠️ 风格各章会有差异（这是预期，主题禁区兜底）
```

收到反馈后：
- 稿子 / outline 要改：直接编辑文件，编辑完 ping 一次（或口头描述 agent 改）
- **主题必须明确**才进入 Phase 2。用户说"主题你帮我选" → 取你推荐的第 1 个，
  **告诉用户你选了什么、为什么**，给反悔机会
- 模式选定 → 进 Phase 2

---

## Phase 2 —— 视频开发（默认 Remotion）

详细规范见 [`references/REMOTION.md`](references/REMOTION.md)。

### 2.1 脚手架

**默认 Remotion**：

```bash
cd <user-cwd>
npx create-video@latest --yes --blank --no-tailwind presentation
```

跑通后**手动写**这几个项目根文件（用 Write 工具，不要 cat）：
- `src/theme.ts` —— 把选定主题的颜色 / 字体从 `themes/<id>/tokens.css`
  转写成 TS const，外加 `AUDIO_DURATIONS_SEC` 占位（音频合成完后填实测）
- `src/components/Masthead.tsx` / `MaskReveal.tsx` —— 看 [`REMOTION.md`](references/REMOTION.md)
  的"动画模式"章节抄常用组件

**网络挡 github** 时（中国大陆 / 公司内网常见）：手动搭最小 6 文件骨架 +
`npm install`（npm registry 通常已是 alibaba / npmmirror 镜像）。
逐字模板见 [`REMOTION.md`](references/REMOTION.md) "网络不可达 github 时的手动路径"。

**Vite + 网页录屏旧路径**（仅"用户明确要可点击现场演示"）：

```bash
bash .agent/skills/web-video-presentation/scripts/scaffold.sh \
  ./presentation \
  --theme=<用户选的主题 id>
```

> 自定义主题 → 先按 [`references/THEMES.md`](references/THEMES.md)
> "创作新主题"流程做一个 `themes/<my-theme>/` 再用。Remotion 模式下也通过
> tokens.css 获取色板，再手动转写为 `theme.ts`。

### 2.2 第 1 章 —— 主线程 + 强制验收

**核心**：第 1 章 = 完整版本一次到位（节奏 + 视觉 + 真素材齐全）。
**没有"骨架版"概念** —— 第一章就要做出**用户能直接验收**的样板。

为什么第 1 章必须主线程：

- 它是 [`CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md) 这套指引在**当前
  主题 + 当前题材**下的第一次落地
- 如果指引有盲区 / 主题颜色 / 字体 token 不够用，第 1 章一定会暴露 ——
  这时候有人类反馈就能修指引 / 调主题，**早改成本最低**
- 后续章节（无论顺序 / 并行）都要参考第 1 章的代码模式，所以第 1 章 =
  当次项目的"风格锚点（不强求章节间一致，但单章自身得有完整说服力）"

**做完第 1 章后必须停下来**等用户验收：

```
第 1 章 <id> 做完了。

【Remotion 模式】
  Studio 预览：cd presentation && npx remotion studio  → http://localhost:3000
  关键帧 still：npx remotion still <id> out/x.png --frame=N --scale=0.5
  整章 MP4：    npx remotion render <id> out/<id>.mp4

【Vite 模式（互动 demo）】
  dev server:   localhost:5174

验收重点：
  □ 视觉气质对不对？符合 <theme nameZh> 的预期吗？
  □ 节奏对不对？某些步太快 / 太慢 / 信息太薄？
  □ 内容驱动动画是否到位？还是有几步是无脑入场动画？
  □ 双源原则：屏幕画面有没有"口播没念但 article 能挂"的细节？
  □ 反 AI 味检查：紫粉渐变 / 圆角彩色边框 / 假插画 / emoji 是否有？
  □ 字号下限：所有可见文本 ≥ 18px（mono 辅助小标签下限 / 主文案 ≥ 60-200px）

问题告诉我，我针对性改。OK 了告诉我"继续"，我按选定模式做第 2 章及之后。
```

### 2.3 第 2~N 章 —— 按选定模式

**所有模式下的共同规则**：每章独立按 [`CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md)
开发。**风格不强求章节间完全一致** —— 主题颜色 / 字体 token 兜底视觉
统一，动画 / 节奏 / 视觉演示由章节自由发挥是设计预期。

#### 模式 A · 默认 · 逐章确认

第 2 章做完 → 暂停验收 → OK → 第 3 章 → 暂停 → ... → 第 N 章。**每章
独立验收**，问题随时改，**风险最低，节奏最稳**。**用户不明确选模式时
默认走这个**。

#### 模式 B · 第 1 章后顺序开发

第 2 章 → 第 3 章 → ... → 第 N 章 **主线程顺序做完，最后统一验收**。
速度中等，适合 agent 不支持并行任务的环境。

#### 模式 C · 第 1 章后并行开发（subagent）

用 subagent 把第 2~N 章并行做完，最大并行数由用户控制（"一次 4 章"
/ "一次 2 章"）。**最快，但风格各章会有差异** —— 这是预期，因为：

1. 每个 subagent 看不到别的 subagent 产出，无法机械对齐
2. 章节代码物理分离（每章一个文件夹 / 自己的 CSS 前缀），不会互相
   破坏
3. 主题 token 兜底视觉统一（颜色 / 字体 / hero 数字 / 卡片 / 分割线
   性格 / 装饰），气质不会跑偏
4. **风格不一致 = 人手写视频的呼吸感**（多 voice / 多视角）

并行 subagent 的 prompt 必须包含：

- 当前章节 outline 段落（含信息池）
- `references/CHAPTER-CRAFT.md` 的路径（**单一必读** —— 视觉演示要求 +
  逐步揭示 + 双源原则 + 反 AI 味 + 代码红线 + 完工自检全部在这一份里）
- **Remotion 模式额外必读**：`references/REMOTION.md` 的"动画模式：CSS keyframes
  → interpolate"小节（CSS / Tailwind animation 禁用，全用 `interpolate` / `spring`）
- 当前主题 `theme.json` 的 `descriptionZh` / `mood` / `bestFor`（参考气质
  即可，动画 / 时长 / 字号 / emoji 由 chapter agent 自由决定）
- **第 1 章代码作为"代码风格"参考**（不是"视觉抄袭对象"）
- 硬规则：每章独立文件夹 + 文件级隔离；不修改 `Root.tsx` / `Composition.tsx` /
  `theme.ts` 等共享文件（章节注册由协调者统一做）；完工跑 `npx tsc --noEmit` +
  渲一帧 still 验证

**重要**：无论选哪种模式，**用户随时可以中途切换模式**。第 2 章 OK
后用户说"剩下的并行" / "剩下的逐章" 都行。

### 2.4 实现单章（每章必走）

详细指引见 [`references/CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md) ——
**单一必读入口**，覆盖：视觉演示要求 / 逐步揭示 / 内容取舍 / 双源原则
/ 视频演示基本审美 / 反 AI 味 / 代码红线 / 完工自检。

**核心要点**（CHAPTER-CRAFT.md 详述）：

- **每章必须有 CSS / SVG / Canvas / JS 视觉演示**，禁纯文字章节
- **逐步揭示**：清单 / 列表必须 1 项 = 1 step，禁一次全展示
- **双源原则**：节奏跟口播稿（顺序不能乱），细节回原文章抽（信息池 +
  本章 article 段落）
- **完工自检逐项过**，不达标回去改 —— 按上文「硬性自检协议」执行
  （优先 Agent Teams → subAgent → 自检），**改完再向用户汇报本章交付**

### 2.5 章节结构变化后的同步

**Remotion 模式**：改了某章的 step 数 → 同步更新 `theme.ts` 的 `AUDIO_DURATIONS_SEC`
对应章节数组长度 → `Root.tsx` 的 `durationInFrames` 自动跟着算 → 重渲。

**Vite 模式**：改动 `chapters.ts`（增加 / 删除 / 重排章节，或某章 `narrations.ts`
长度变化）后，**bump** `presentation/src/hooks/useStepper.ts` 的
`STORAGE_KEY`（如 `v4` → `v5`），避免持久化游标落到不存在的 step 上。

---

## Checkpoint Audio —— 是否合成音频（**硬节点**）

Phase 2 结束后必须停下来，问用户：

```
视频章节做完，{N} 章 {M} 步。

【Remotion 模式】预览：cd presentation && npx remotion studio
【Vite 模式】预览：    localhost:5174

要不要合成音频？
  ✓ 合成 → 扫所有章节的 narrations 出 audio-segments.json，
           调 MiniMax / DMXAPI 合成每步一个 mp3 到 public/audio/。
           Remotion 模式：合成完后用 ffprobe 实测时长，填回 theme.ts 的
                          AUDIO_DURATIONS_SEC，然后 npx remotion render 出片。
           Vite 模式：合成完后 ?auto=1 一镜到底录屏。
           需要 API key（详见 references/AUDIO.md）。
  ✗ 不合成 →
           Remotion 模式：用静音版渲 mp4，或后期配音
           Vite 模式：手动点击推进 + 后期配音
```

要合成 → Phase 3。不合成 → 直接 Phase 4。

---

## Phase 3 —— 音频合成

详细流程见 [`references/AUDIO.md`](references/AUDIO.md)。简版：

```bash
cd presentation
npm run extract-narrations   # 扫 narrations → audio-segments.json
# 让用户扫一眼 audio-segments.json 确认文本对
npm run synthesize-audio     # 调 MiniMax / DMXAPI 串行合成；增量、跳过已存在
                             # 需要 API key（见 references/AUDIO.md）
```

**Remotion 模式额外一步**：合成完用 ffprobe 测每段实际时长，更新 `theme.ts` 的
`AUDIO_DURATIONS_SEC`：

```bash
for f in public/audio/*/*.mp3; do
  d=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f")
  echo "$f: $d"
done
```

把按章分组的秒数粘进 `theme.ts` —— 这是 frame 计算的输入，不准会音画错位。

合成完告诉用户：输出位置 / 总段数 / 哪些段时长异常（太长 = 该 step 拆
分；太短 = 文案太薄）—— 给最后一次校准节奏的机会。然后进入 Phase 4。

---

## Phase 4 —— 成片输出

### Remotion 模式（默认）

```bash
cd presentation
npx remotion render Full out/full.mp4              # 默认 1080p / 30fps / h.264
npx remotion render Full --concurrency=4           # 并发提速（M1/M2 Pro 建议 2~4）
npx remotion still <id> out/x.png --frame=N        # 单帧导出（QA / 海报）
```

**完了**——文件就在 `out/full.mp4`，可以直接发布。无需录屏，无需后期对音轨。

需要参数化变体（不同语言 / A/B 标题）→ [`REMOTION.md`](references/REMOTION.md)
"Composition 顶层结构"看 `defaultProps` + Zod schema 用法。

### Vite 模式（仅互动 demo 场景）

详见 [`references/RECORDING.md`](references/RECORDING.md)。

| 场景 | 推荐路径 |
|---|---|
| Phase 3 已合成音频 | **Auto 模式一镜到底**：浏览器开 `localhost:5174/?auto=1` → 按 SPACE → 整片自动播完 → 停录 → 裁头尾即成片 |
| Phase 3 跳过 | 默认 Manual 模式手动点击推进 → 后期任意剪辑工具配音 |

> agent 在 Phase 3 / Checkpoint Audio 后**主动告诉用户**适合的成片路径
> （Remotion 路径就一个 `npx remotion render` 命令）。

---

## 十条原则（一句话清单）

完整展开见 [`references/CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md)
Part 0 —— **写章节时回那里查**，下面只是索引。

| # | 原则 | 一句话 |
|---|---|---|
| 1 | 16:9 固定舞台 | 内容 1920×1080 + transform scale，没有响应式 |
| 2 | 全局 step 计数器 | 章节是 step 的纯函数，无定时器 |
| 3 | 每步独占整屏 | `if (step === N) return <FullScene />` |
| 4 | 口播节拍 = step | 一节拍 = 一 step = 一聚焦想法 |
| 5 | 隐藏的边角控件 | 进度条 / 翻页器默认 opacity 0 |
| 6 | 舞台无 chrome | 没有 header / footer / 页码 / 品牌条 |
| 7 | **内容驱动动画** | 先找内在动作，找不到才入场动画兜底；持续微动慎用 |
| 8 | 多点逐个揭示 | 1 项 = 1 step，禁同步 stagger 上 N 项 |
| 9 | 整片同一主题 | 章节间不翻表面色；**颜色 / 字体走 token**，其它尺度章节自由 |
| 10 | 双源原则 | script 定节拍，**article 定画面密度**（落到信息池） |

---

## 常见用户反馈速查

简化表见 [`references/CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md)
Part 8「常见反馈速查」。**关键**：先定位是哪一层（节奏 / 视觉 / 内容
/ 代码），再改最小切片，**不要重做整章**。

---

## 相关资源

按"何时读"标注，避免一次性全读：

| 文件 | 何时读 | 内容 |
|---|---|---|
| [`references/SCRIPT-STYLE.md`](references/SCRIPT-STYLE.md) | Phase 1.2 必读 | 文章 → 口播稿规则、平台变体 |
| [`references/OUTLINE-FORMAT.md`](references/OUTLINE-FORMAT.md) | Phase 1.2 必读 | outline.md 字段 spec、命名约定、章节切分、信息池 |
| [`references/REMOTION.md`](references/REMOTION.md) | **Phase 2 默认必读（Remotion 模式）** | 脚手架（含手动 fallback）/ Composition 结构 / theme.ts 模板 / CSS keyframes → interpolate / Google Fonts / 渲染命令 / 常见坑 |
| [`references/CHAPTER-CRAFT.md`](references/CHAPTER-CRAFT.md) | **Phase 2.4 每章单一必读入口** | 十条原则 / 开工 5 问 / 决策树 / 视觉工具箱 / 时长 / 反 AI 味 / 字号下限 / 代码硬规则 / 完工自检 / 反馈速查 |
| [`references/EXAMPLES/`](references/EXAMPLES/) | **可选** —— 看结构 | 章节结构示意（hook / list-reveal / case-tech-review）；**不是抄袭模板** |
| [`references/THEMES.md`](references/THEMES.md) | 选 / 造 / 切主题时 | 完整 token 契约 + 内置主题清单 + 创作流程 |
| [`references/AUDIO.md`](references/AUDIO.md) | Phase 3 才读 | MiniMax / DMXAPI 兼容、TTS 流程、故障排查 |
| [`references/RECORDING.md`](references/RECORDING.md) | Phase 4 才读（仅 Vite 模式） | 录屏工具 + 后期合成 |
| [`themes/`](themes) | Checkpoint Plan / Phase 1.2 时翻 | 内置主题（每个含 `theme.json` + `tokens.css`） |
| [`scripts/scaffold.sh`](scripts/scaffold.sh) | 仅 Vite 模式 | 一键 Vite 项目脚手架（Remotion 用 `npx create-video`） |

