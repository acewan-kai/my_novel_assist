# My Novel Assist 使用指南

## 从灵感到小说：完整工作流

本文通过一个完整的案例，演示如何利用此工具写出一篇小说。

---

## 一、准备工作

```bash
cd backend
pip install -r requirements.txt
```

### 配置 API Key（可选）

不配也能使用大部分功能（审核、校验、叙事规划等），只有「生成章节」需要：

```bash
cp .env.example .env
# 编辑 .env，填入你的 key
# OPENAI_API_KEY=sk-xxx
```

支持的提供商：`openai`、`deepseek`、`anthropic`、`google`、`ollama`、`custom`

切换提供商：在 `.env` 中设置 `LLM_PROVIDER=deepseek`

---

## 二、快速体验所有功能

先跑一遍 demo，确认一切正常：

```bash
python -m app.cli demo
```

你会看到 9 个模块依次演示：Provider Bank → Quality Metrics → 33维审核 → De-AI检测 → 后写作校验 → 叙事引擎 → Schema验证 → @DSL解析 → 状态追踪。

---

## 三、实战案例：奇幻小说《星穹之下》

### 故事灵感

> 一个在天文台工作的青年，意外发现星空其实是某种巨大生物的「外壳」。星光的变化是这个生物呼吸的节奏。一群知晓这个秘密的人，在暗中守护着这个真相。主角被迫卷入一场跨越千年的博弈。

---

### Step 1 — 用 Schema 验证故事设定

在开始写作前，先用 Schema Registry 验证你的故事 premise 是否完整：

```bash
python -m app.cli schema validate --name story_premise \
  --data '{"title":"星穹之下","genre":"奇幻","logline":"一个在天文台工作的青年意外发现星空是巨大生物的外壳，从此卷入跨越千年的秘密。"}'
```

输出：

```
+ Schema 'story_premise' validation PASSED
```

内置的 Schema 类型：
| Schema | 必填字段 | 用途 |
|--------|---------|------|
| `story_premise` | title, genre | 验证故事核心设定 |
| `character` | name, role | 验证角色卡 |
| `chapter` | number, title | 验证章节结构 |

---

### Step 2 — 设定质量标准

明确你的成稿质量目标，工具后续会按此标准进行审核：

```bash
python -m app.cli quality --coherence 0.85 --integration 0.75 --polish 0.70
```

```
+--------------------+
| Quality Metrics    |
| Coherence:    0.85 |
| Integration:  0.75 |
| Polish:       0.70 |
| ---                |
| Overall:      0.77 |
| Passed:       Yes  |
+--------------------+
```

三个维度含义：
- **Coherence（连贯性）**：情节逻辑是否自洽
- **Integration（整合性）**：伏笔和设定是否有机融入
- **Polish（润色度）**：语言表达是否精炼

---

### Step 3 — 规划叙事结构

使用叙事引擎查看 Dramatica 16 阶段的推进节奏：

```bash
python -m app.cli narrative --chapter 1 --total 20
```

```
+---------------------------------------------------------------------+
| 16 Dramatica Stages                                                 |
| #  | Stage              | Prompt                                    |
|----+--------------------+-------------------------------------------|
| 1  | setup              | Establish the world, tone...              |
| 2  | inciting_incident  | Introduce the event that disrupts...      |
| 3  | response           | Show the protagonist's initial reaction... |
| ... | ...                | ...                                       |
| 14 | climax             | The ultimate confrontation...              |
| 15 | denouement         | Fallout from the climax...                 |
| 16 | resolution         | The new normal is established...           |
+---------------------------------------------------------------------+

Beats for Chapter 1 of 20:
  * setup: Establish the world, tone, and ordinary life of the protagonist.
  * inciting_incident: Introduce the event that disrupts the status quo.
```

20 章小说的节奏分配：
| 章节 | 阶段 | 叙事目标 |
|------|------|---------|
| 1-2 | setup → inciting incident | 建立世界观，引入激励事件 |
| 3-5 | response → pursuit | 主角反应与行动 |
| 6-8 | ally intro → antagonist rise | 伙伴与对手登场 |
| 9-10 | first turning point → midpoint | 第一个转折点 |
| 11-13 | crisis → betrayal → dark night | 危机升级 |
| 14-16 | second turning point → climax | 反转 → 高潮 |
| 17-20 | denouement → resolution | 收尾 |

---

### Step 4 — 生成章节内容

启动 API 服务：

```bash
python -m app.cli server
```

服务器启动在 http://localhost:8000，API 文档在 http://localhost:8000/docs。

创建项目：

```bash
python -m app.cli api create-project --title "星穹之下"
```

输出：

```json
{"id":"abc123","title":"星穹之下","author":"","chapter_count":0,...}
```

创建章节：

```bash
# 首先确保 server 在运行，然后在另一个终端执行：
python -m app.cli api chapters --project abc123
```

使用 REST API 生成章节（需要 API Key）：

```bash
curl -X POST http://localhost:8000/api/generate/chapter \
  -H "Content-Type: application/json" \
  -d '{"project_id":"abc123","chapter_number":1,
       "outline":"林夜在天文台值夜班时发现星空异常",
       "pov_character":"林夜",
       "world_context":"现代都市背景，天文台位于城郊山上"}'
```

成功时返回包含章节内容和各 agent 阶段数据的 JSON。

> **注意**：生成需要配置有效的 LLM API Key（OpenAI / DeepSeek / Anthropic 等）。
> 如果不配置 API Key，管线会运行但返回 401 错误，这是预期的。

---

### Step 5 — 质量审核

写好的草稿可以用 33 维审核系统检查质量问题：

```bash
python -m app.cli audit "林夜猛然抬头，星空在头顶旋转。不，不是旋转——它们在移动，像是有生命的。他揉了揉眼睛，再次确认。天文台的望远镜从不会骗人。然而，这一刻他看到的景象已经超出了所有天文理论的解释。突然间，所有的星星都暗了一瞬。"
```

输出：

```
+ Audit PASSED
Overall Score: 0.96
Dimension Scores:
  fatigue: 0.90
  forbidden: 1.00
  meta: 1.00
  collective: 1.00
  consecutive_le: 1.00
```

审核的五个维度：

| 维度 | 检查内容 | 常见问题 |
|------|---------|---------|
| fatigue | 疲劳词（突然、仿佛、竟然…） | 过度使用降低阅读体验 |
| forbidden | 禁用模式（全场震惊、所有人都…） | 群体描写的偷懒写法 |
| meta | 元叙事（核心动机、人物弧线…） | 写作分析混入正文 |
| collective | 集体反应（众人齐声…） | 群体描写的简化处理 |
| consecutive_le | 连续「了」字句 | 句尾连续「了」字 |

---

### Step 6 — De-AI 痕迹检测

检查文本是否有 AI 写作的典型特征：

```bash
python -m app.cli de-ai "首先，让我们探讨星空的意义。其次，我们需要分析数据。最后，值得注意的是..."
```

输出：

```
AI Score: 0.24 / 1.00
+ Passes De-AI check

Issues found:
  WARN [warning] 作者介入: x1
  WARN [warning] 结构化列举: x1
  WARN [warning] 评论插入: x1
  INFO [info] sensory: 密度0.0/千字
```

De-AI 检测的模式包括：

| 模式 | 示例 | 建议替换 |
|------|------|---------|
| 作者介入 | "让我们看看…" | 直接叙述 |
| 结构化列举 | "首先…其次…最后…" | 自然过渡 |
| 总结句式 | "总的来说…" | 融入正文 |
| LLM 常用动作 | "他深吸一口气" | 多样化描写 |
| 感官密度 | 视觉/听觉/触觉/嗅觉 | 增加五感描写 |

> 目标：AI Score < 0.4。分数越低越接近人类写作。

---

### Step 7 — 校验与修订

对最终的章节做后写作校验：

```bash
python -m app.cli validate --min-words 100 "林夜猛然抬头，星空在头顶旋转..."
```

校验内容：
- 字数是否达标
- 是否有重复段落
- 句子开头是否多样化

---

### Step 8 — 状态追踪

Delta Store 提供了类似 Git 的状态追踪，可以在写作过程中设置检查点：

```bash
python -m app.cli state
```

```
State Delta Tracking Demo

1. Record 'title' = 'My Novel'
2. Record 'author' = 'Tester'
3. History: 2 entries
   [user] title: '' -> 'My Novel'
   [user] author: '' -> 'Tester'
4. Checkpoint 'v1' — 保存当前状态快照
5. Record 'title' = 'Great Novel'  — 继续修改
6. Rollback to 'v1' — 回滚到检查点
   Reverted 2 changes: ['title', 'word_count']
```

在写作工作流中，你可以在每个章节完成后设置检查点，方便回溯。

---

### Step 9 — 使用 @DSL 模板注入

在写作提示词中使用 @DSL 语法，实现动态内容注入：

```bash
python -m app.cli dsl "在@type:location中，@title遇到了@type:character。"
```

```
Input: 在@type:location中，@title遇到了@type:character。
+---------------------------+
| DSL Matches               |
| Type  | Target    | Valid |
|-------+-----------+-------|
| type  | location  | True  |
| title | title     | True  |
| type  | character | True  |
+---------------------------+
```

@DSL 语法：
| 语法 | 含义 | 示例 |
|------|------|------|
| `@title` | 按标题查找 | `@星穹之下` |
| `@type:type_name` | 按类型查找 | `@type:character` |
| `@self` | 当前上下文 | `@self` |
| `@prev` | 上一章内容 | `@prev` |

---

## 四、完整写作流一览

```
灵 感
  │
  ▼
Schema 验证故事 premise  ────  python -m app.cli schema validate
  │
  ▼
设定质量标准  ────────────────  python -m app.cli quality
  │
  ▼
规划叙事结构  ────────────────  python -m app.cli narrative
  │
  ▼
┌─────────────────────────────────────┐
│         写作循环                     │
│                                     │
│  生成章节 ─→ 33维审核 ─→ De-AI检测  │
│      ↑               │             │
│      └── 修订 ───────┘             │
└─────────────────────────────────────┘
  │
  ▼
后写作校验  ────────────────────  python -m app.cli validate
  │
  ▼
状态检查点 / 回滚  ──────────────  python -m app.cli state
  │
  ▼
成 稿
```

对应的 CLI 命令序列：

```bash
# 1. 验证故事 premise
python -m app.cli schema validate -n story_premise -d '{"title":"...","genre":"...","logline":"..."}'

# 2. 查看叙事节奏
python -m app.cli narrative --chapter 1 --total 20

# 3. 写完后审核
python -m app.cli audit "章节文本..."

# 4. 检查 AI 痕迹
python -m app.cli de-ai "章节文本..."

# 5. 后写作校验
python -m app.cli validate --min-words 500 "章节文本..."

# 6. 查看提供商列表
python -m app.cli providers

# 7. 启动 API 服务（需要生成时）
python -m app.cli server
```

---

## 五、命令速查

| 命令 | 用途 | 不需要 API Key |
|------|------|:---:|
| `demo` | 完整功能演示 | ✅ |
| `server` | 启动 API 服务 | ✅ |
| `providers` | 列出 LLM 提供商 | ✅ |
| `quality` | 质量评分计算 | ✅ |
| `audit <text>` | 33 维质量审核 | ✅ |
| `de-ai <text>` | AI 痕迹检测 | ✅ |
| `validate <text>` | 后写作校验 | ✅ |
| `narrative` | 叙事结构展示 | ✅ |
| `schema` | Schema 验证 | ✅ |
| `dsl <template>` | @DSL 语法解析 | ✅ |
| `state` | 状态追踪演示 | ✅ |
| `api <action>` | API 快捷调用 | ✅（需要 server） |
| 生成章节 (API) | AI 生成内容 | ❌ 需要 API Key |

---

## 六、常见问题

**Q: 没有 API Key 能用吗？**
A: 可以。除了「生成章节」外的所有功能（审核、校验、叙事规划、Schema 验证等）都无需 API Key。

**Q: 用什么 LLM 最好？**
A: 中文小说推荐 DeepSeek（性价比高）或 Anthropic Claude（质量好）。用 Ollama 可以在本地运行，完全免费。

**Q: 如何切换 LLM？**
A: 在 `.env` 中设置 `LLM_PROVIDER=deepseek` 并填入对应的 API Key。

**Q: 前端页面有什么用？**
A: 前端（http://localhost:5173）提供项目管理和章节生成触发的可视化界面，但 CLI 才是完整的功能入口。
