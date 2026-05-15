# Remotion 模式开发指引（推荐路径）

把同样的 16:9 视频网页用 Remotion 实现 ——
**`npx remotion render` 直接输出 MP4，不需要屏幕录制**。
帧精确、音视频硬对齐、可参数化重渲、所有 CSS 录屏伪影都消失。

> Vite + 网页录屏的旧路径 ([RECORDING.md](RECORDING.md) 末尾保留) 仍能工作 ——
> 但只在用户**明确要做"可点击的现场互动演示"**时才选。其它情况一律走 Remotion。

---

## 关键差异（与 Vite 模式对比）

| 维度 | Vite + 网页录屏 | **Remotion（推荐）** |
|---|---|---|
| 动画写法 | CSS keyframes / transitions | **`useCurrentFrame()` + `interpolate()`** —— CSS 动画禁用 |
| 音视频同步 | Auto 模式按音频结束推进，~200ms 漂移 | **帧级硬对齐**，永不漂 |
| 成片获取 | 屏幕录制工具，受帧率 / 鼠标 / chrome 影响 | **`npx remotion render`**，1920×1080 / 30fps 帧精确 |
| 主题切换 | CSS 变量热切 | TS const，章节按 prop 接 |
| 交互 | 可点击推进，做现场 demo | 纯时间线 |
| Studio 预览 | Vite HMR | `npx remotion studio` HMR |
| 单帧调试 | 浏览器 jump-to-step | `npx remotion still --frame=N` |
| 适合 | 现场演示 / live talk | 视频发布 / B 站 / YouTube |

**判断标准**：要交付的是 **mp4 文件 → Remotion**；要交付的是 **可点击网页 → Vite**。

---

## Phase 2A —— Remotion 脚手架

### 标准路径（网络通畅）

```bash
cd <user-cwd>
npx create-video@latest --yes --blank --no-tailwind <project-name>
```

`<project-name>` 通常 = `presentation`（保持和文档约定一致）或 `remotion-video`。
`--no-tailwind` 是因为 **Tailwind animation class 禁用**（参考 SKILL 顶部规则），
也避免和章节里的 inline style 冲突。

### 网络不可达 github 时的手动路径（中国大陆 / 公司内网常见）

`create-video` 会从 github 克隆模板，被防火墙挡时会报：
`Client network socket disconnected before secure TLS connection`。
此时**手动写最小骨架** + 走 npm 镜像装包：

```bash
mkdir -p <project>/src/{components,scenes} <project>/public/audio
cd <project>
```

**最小文件集**（用 Write 工具创建，不要 cat）：

`package.json`：
```json
{
  "name": "<project>",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "remotion studio",
    "studio": "remotion studio",
    "build": "remotion render Full out/full.mp4",
    "render-still": "remotion still Full --frame=30 --scale=0.5 out/still.png",
    "tsc": "tsc --noEmit"
  },
  "dependencies": {
    "@remotion/cli": "4.0.385",
    "@remotion/google-fonts": "4.0.385",
    "@remotion/media": "4.0.385",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "remotion": "4.0.385"
  },
  "devDependencies": {
    "@types/react": "19.0.0",
    "@types/react-dom": "19.0.0",
    "typescript": "5.8.3"
  }
}
```

`tsconfig.json`：strict + jsx react-jsx + bundler resolution（参考 PoC 模板）。

`remotion.config.ts`：
```ts
import { Config } from "@remotion/cli/config";
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

`src/index.ts`：
```ts
import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";
registerRoot(RemotionRoot);
```

之后 `npm install` 即可（用户 npm 镜像通常是 alibaba / npmmirror，能装通）。

### 验证

```bash
npx tsc --noEmit          # 必须通过
npx remotion studio       # 开 http://localhost:3000 看到空 Composition = 成功
```

---

## 工程结构（Remotion 模式）

```
my-video/
├── article.md             # 用户原文（不删）
├── script.md              # 口播稿
├── outline.md             # 开发计划
├── presentation/          # ← Remotion 项目根
│   ├── package.json
│   ├── tsconfig.json
│   ├── remotion.config.ts
│   ├── public/audio/<chapter-id>/<step>.mp3   # 同 Vite 模式音频路径
│   └── src/
│       ├── index.ts                # registerRoot 入口
│       ├── Root.tsx                # Composition 定义（含 Full + 各章独立预览）
│       ├── Composition.tsx         # Full：所有章节 wire up
│       ├── theme.ts                # 主题 token（TS const，不是 CSS var）
│       ├── narrations.ts           # 全章 narrations + 音频时长表（唯一真相源）
│       ├── components/             # 共用组件（Masthead / MaskReveal / ...）
│       └── chapters/
│           ├── 01-coldopen/
│           │   ├── Coldopen.tsx        # 该章节 Composition 组件
│           │   └── scenes/             # 该章节各 step 拆分（可选）
│           │       ├── Step0Hook.tsx
│           │       └── ...
│           └── ...
└── out/                  # 渲染产出（git ignore）
    ├── full.mp4
    └── still.png
```

> **唯一真相源**：每章 `narrations.ts` 数组长度 = 该章 step 数 = 音频文件数。
> 不能漂。详见 [AUDIO.md](AUDIO.md)。

---

## 主题 token：TS const（而非 CSS var）

Remotion 没有 "切 CSS 变量整片换主题" 的能力。规约：把 newsroom / blueprint
等主题的 token 摘成 TS const，按主题切换 import 路径。

`src/theme.ts` 模板：
```ts
export const T = {
  shell: "#c8bca0",
  surface: "#f1ebd8",
  surface2: "#f8f3e2",
  text: "#14110b",
  textMute: "#5e564a",
  rule: "#968e7a",
  accent: "#c8260d",
  accentSoft: "rgba(200, 38, 13, 0.10)",
} as const;

export const FONTS = {
  serifCn: "'Noto Serif SC', serif",
  serifEn: "'Playfair Display', serif",
  mono: "'JetBrains Mono', monospace",
} as const;

export const AUDIO_DURATIONS_SEC: Record<string, number[]> = {
  coldopen:    [4.5, 7.8, 8.5, 3.5, 9.8],
  company:     [5.3, 6.8, 6.2, 9.8, 12.0, 9.5],
  // ... 一章一行
};

export const TAIL_FRAMES = 6; // 200ms @30fps 节拍呼吸
```

**章节代码消费**：`color: T.text`、`fontFamily: FONTS.serifCn`，**不要硬编码 hex / 字体名**。

> 主题色板从 `themes/<id>/tokens.css` 摘出来即可——`themes/` 目录依然是单一来源，
> Remotion 模式只是手动把它转写成 ts。

---

## Composition 顶层结构

`src/Root.tsx`（注册 Full + 各章预览）：
```tsx
import { Composition } from "remotion";
import { Full } from "./Composition";
import { Coldopen } from "./chapters/01-coldopen/Coldopen";
// ... 其它章节

const FPS = 30;
const totalFramesFor = (durs: number[]) =>
  durs.reduce((acc, sec) => acc + Math.round(sec * FPS) + 6, 0);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Full"
      component={Full}
      durationInFrames={totalFramesFor(AUDIO_DURATIONS_FLAT)}
      fps={FPS}
      width={1920}
      height={1080}
    />
    {/* 单章预览：Studio 里可以独立调一章 */}
    <Composition
      id="Coldopen"
      component={Coldopen}
      durationInFrames={totalFramesFor(AUDIO_DURATIONS_SEC.coldopen)}
      fps={FPS}
      width={1920}
      height={1080}
    />
    {/* ... 其它章节 */}
  </>
);
```

`src/Composition.tsx`（Full：所有章节按顺序 Sequence 起来）：
```tsx
import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { AUDIO_DURATIONS_SEC, TAIL_FRAMES, T } from "./theme";

const CHAPTERS = [
  { id: "coldopen",    Component: Coldopen },
  { id: "company",     Component: Company },
  // ...
];

export const Full: React.FC = () => {
  const { fps } = useVideoConfig();
  let cursor = 0;
  return (
    <AbsoluteFill style={{ background: T.surface }}>
      {CHAPTERS.map(({ id, Component }) => {
        const durs = AUDIO_DURATIONS_SEC[id]!;
        const totalFrames = durs.reduce(
          (a, s) => a + Math.round(s * fps) + TAIL_FRAMES, 0,
        );
        const from = cursor;
        cursor += totalFrames;
        return (
          <Sequence key={id} from={from} durationInFrames={totalFrames} name={id}>
            <Component />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
```

每个章节组件内部再用 Sequence + Audio：
```tsx
export const Coldopen: React.FC = () => {
  const { fps } = useVideoConfig();
  const durs = AUDIO_DURATIONS_SEC.coldopen;
  let cursor = 0;
  return (
    <AbsoluteFill>
      {SCENES.map((Scene, i) => {
        const audioFrames = Math.round(durs[i] * fps);
        const totalFrames = audioFrames + TAIL_FRAMES;
        const from = cursor;
        cursor += totalFrames;
        return (
          <Sequence key={i} from={from} durationInFrames={totalFrames}>
            <Scene />
            {/* 音频严格等于 mp3 实际帧数，不溢到尾部呼吸 */}
            <Sequence durationInFrames={audioFrames} layout="none">
              <Audio src={staticFile(`audio/coldopen/${i + 1}.mp3`)} />
            </Sequence>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
```

---

## 动画模式：CSS keyframes → interpolate

**CSS keyframes 禁用**（Remotion 渲染不到）。所有动画都要重写为 frame-based。

### 场景 1：单次入场（fade + translate）

CSS：
```css
@keyframes mast-in { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.co-mast { animation: mast-in 700ms ease-out 100ms both; }
```

Remotion：
```tsx
const frame = useCurrentFrame();
const opacity = interpolate(frame, [3, 24], [0, 1], {
  extrapolateLeft: "clamp", extrapolateRight: "clamp",
});
const y = interpolate(frame, [3, 24], [-6, 0], {
  extrapolateLeft: "clamp", extrapolateRight: "clamp",
});
return <div style={{ opacity, transform: `translateY(${y}px)` }}>...</div>;
```

时间换算：`delay 100ms` → frame 3（@30fps），`duration 700ms` → 21 帧。

### 场景 2：clip-path wipe（MaskReveal 等价）

```tsx
export const MaskReveal: React.FC<{
  from: number; durationFrames?: number; children: ReactNode;
}> = ({ from, durationFrames = 27, children }) => {
  const frame = useCurrentFrame();
  const right = interpolate(frame, [from, from + durationFrames], [100, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 4),
  });
  return (
    <span style={{ display: "inline-block", clipPath: `inset(0 ${right}% 0 0)` }}>
      {children}
    </span>
  );
};
```

### 场景 3：spring overshoot（弹入图章）

```tsx
import { spring, useVideoConfig } from "remotion";

const { fps } = useVideoConfig();
const stamp = spring({ frame: frame - 51, fps, config: { damping: 12, mass: 0.6 } });
const scale = 1.5 - 0.5 * stamp;
const rotate = -20 + 14 * stamp;
return <div style={{ transform: `rotate(${rotate}deg) scale(${scale})`, opacity: stamp }}>11×</div>;
```

### 场景 4：循环动画（时钟旋转 / 蒸汽云飘动）

CSS keyframes `animation: spin 4s linear infinite` → 完全重写：
```tsx
const cycleFrames = 4 * fps; // 4s loop
const angle = ((frame % cycleFrames) / cycleFrames) * 360;
return <line transform={`rotate(${angle})`} />;
```

错峰循环（多个粒子）：
```tsx
const particle = (delay: number) => {
  const t = (((frame - delay) % cycle) + cycle) % cycle / cycle;
  const opacity = t < 0.5
    ? interpolate(t, [0, 0.5], [0, 0.18])
    : interpolate(t, [0.5, 1], [0.18, 0]);
  return { opacity, y: -30 * t };
};
```

### 场景 5：清单逐项揭示（stagger）

CSS `animation-delay: calc(var(--i) * 130ms + 250ms)` → 每项各算各的 from：
```tsx
const items = HEIGHTS.map((h, i) => {
  const start = 8 + i * 4;  // 250ms 起点 + 130ms 间隔
  const progress = interpolate(frame, [start, start + 27], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return progress * h;
});
```

---

## Google Fonts 加载

模块级加载，Studio 启动 + render 都生效：

```tsx
import { loadFont as loadPlayfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as loadNotoSerifSC } from "@remotion/google-fonts/NotoSerifSC";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";

loadPlayfair({ weights: ["400", "700"], subsets: ["latin"] });
loadNotoSerifSC({ weights: ["400", "700"] });
loadJetBrainsMono({ weights: ["400", "500"] });
```

**首次渲染会下载所有字重**——给 `weights` / `subsets` 显式收窄能省网络请求（Studio
里 warning 提示"Made N network requests"就是没收窄）。

CJK 字体（Noto Serif SC）整字库 ~9MB，建议 **subset 用 `chinese-simplified` + `latin`**。

---

## 渲染命令

| 命令 | 用途 |
|---|---|
| `npx remotion studio` | 实时预览，HMR，跳帧调试，scrub timeline |
| `npx remotion still <id> out/x.png --frame=N --scale=0.5` | 单帧验证（scale 缩小快） |
| `npx remotion render <id> out/x.mp4` | 出 MP4（默认 1080p / 30fps） |
| `npx remotion render <id> --concurrency=4` | 并发提速 |
| `npx remotion render <id> --quality=80 --codec=h264` | 调质量 / 编码 |

**concurrency 建议**：mac M1/M2 Pro = 2~4，老机器 = 1。太高会内存爆。

---

## 性能与体积

PoC 实测（5 step / 35.1s / 1920×1080 / 30fps / concurrency=2）：
- 渲染时间 ≈ 30s（逻辑复杂度低 / 字体已 cache）
- MP4 大小 ≈ 2.7 MB（h.264 默认 CRF 18）

**全片预估**（46 step / ~6 分钟）：渲染 ~3-5 分钟 / MP4 ~30-40 MB。
比录屏导出小且更稳。

---

## 完工自检（Remotion 章节专用）

替代 Vite 模式的 CSS keyframes 检查项：

- [ ] **没用 `transition` / `animation:` CSS 属性** —— grep 章节代码应 0 命中
- [ ] **没用 Tailwind 动画 class**（`animate-*`）—— Remotion 不渲染
- [ ] **没用 `setTimeout` / `setInterval`** —— 用 `interpolate` 或 `spring` 代替
- [ ] **每个动画有明确 `from` / `durationFrames`**，落在 step 时长内
- [ ] **音频与场景对齐**：`audioFrames = Math.round(durations[i] * fps)`，**不要把 audio 放进尾部呼吸**
- [ ] **所有颜色 / 字体走 theme.ts 常量**，禁硬编码 hex / 字体名
- [ ] **`npx tsc --noEmit` 通过**
- [ ] **关键帧 still 渲染验证**：每章至少抽 1 帧渲出来看（`--scale=0.5` 节省时间）
- [ ] 字号下限表（[CHAPTER-CRAFT.md](CHAPTER-CRAFT.md) Part 视频演示基本审美）依然适用

---

## 常见坑

| 现象 | 原因 / 修法 |
|---|---|
| 动画在 Studio 看着对，render 出来对不上 | 用了 CSS animation / transition，render 时不生效 → 改成 interpolate |
| 字体在 render 第一帧丢失 | 没有 module-level loadFont，或 fonts 只在某 hook 里加载 → 提到顶层 |
| 音频比预期早结束 | `audioFrames` 用了 totalFrames 而非 audioDuration*fps → 校准 |
| 渲染卡在 Bundling | npm 镜像未配置 / 防火墙 → 使用 alibaba mirror 或本地 cache |
| 单段音频长度不准 | 估算字数 ÷ 4 误差 ±20% → 用 ffprobe 实测填进 `AUDIO_DURATIONS_SEC` |
| concurrency 高了内存爆 | 调到 1~2 重试 |
| Made N network requests warning | 没 subset 字体 → loadFont({ weights, subsets }) 显式收窄 |
| `useCurrentFrame` 在某组件里返回奇怪值 | 该组件不在 Sequence 内 → 包一层 Sequence 或保证它是 Composition 的子树 |

---

## 与 Phase 3 音频合成的关系

**音频合成完全共享 Vite 模式的脚本**——`scripts/extract-narrations.ts` +
`synthesize-audio.py` 输出的 `public/audio/<chapter>/<step>.mp3` 文件路径
两种模式都能用。Remotion 模式额外要做的：把每段实际时长（ffprobe 测）填到
`theme.ts` 的 `AUDIO_DURATIONS_SEC` 里 —— 这是 frame 计算的输入。

简易脚本：
```bash
for f in public/audio/*/*.mp3; do
  d=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f")
  echo "$f: $d"
done
```

把输出按章组成 `AUDIO_DURATIONS_SEC` 字典即可。

---

## 与 Phase 4 录屏的关系

**Remotion 路径不需要录屏**。Phase 4 直接 `npx remotion render Full out/full.mp4`
即成片。RECORDING.md 末尾仍保留旧的 Vite 录屏路径，仅在选了 Vite 模式时走。
