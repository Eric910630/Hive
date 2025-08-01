# 🐝 Hive v1.0 - 个人AI工作流操作系统 (FINAL)

**`Hive`** 是一个运行于本地的、前后端分离的个人AI工作流操作系统。其终极使命是 **增强人类智慧，而非取代人类**。它旨在将重复性的工作流自动化，并帮助用户安全、高效地利用海量的本地数据。

---

### **📜 设计哲学**

- **人类是最终权威:** 系统的规划权、否决权和最终解释权，永远掌握在用户手中。
- **本地优先，隐私至上:** 核心功能与用户数据在完全离线的状态下运行和存储。
- **日志优先，完全可追溯:** 所有核心链路都记录了完整的日志，确保每个决策都透明、可审计。
- **拥抱业界标准:** 采用经过验证的、最优秀的开源框架，不闭门造车。

---

### **🌟 v1.0 核心特性**

- **🧠 Nexus - L1级AI总指挥:** 基于 `LangGraph` 构建的AI核心，能够将用户的自然语言指令解析为多步骤的行动计划，并具备从工具错误中学习和自我纠错的惊人能力。
- **🛠️ L2级专家Agent团队:**
  - **`Seeker` (网络研究员):** 基于 `Tavily` API，负责对互联网信息进行深度研究和回答。
  - **`Steward` (文件管家):** 负责安全的本地文件读写操作。
  - **`Abacus` (计算专家):** 负责精确的数学计算，并能自动处理"万、亿"等中文单位。
- **🧱 ReflectorNode - 架构级信息防火墙:** Hive 的关键架构创新。它能自动检测并精炼过长的工具输出，从根本上解决了AI Agent在处理海量信息时常见的"宕机"或"失忆"问题，确保了系统的鲁棒性。
- **💾 CoreMemory - 持久化记忆核心:** 基于 `SQLite` 构建，负责记录每一次Agent的调用日志，为系统的可观测性和可审计性提供了坚实基础。
- **🚀 现代化的技术栈:**
  - **后端:** `FastAPI` 驱动的异步Python服务。
  - **前端:** 基于 `React` & `Next.js` 的现代化Web应用。
  - **通信:** 高效的服务器发送事件 (SSE) 流式接口，提供实时的交互体验。

---

### **🏗️ 项目架构**

hive-project/
├── 📄 .env # 环境变量配置 (需从env_template.txt复制创建)
├── 📄 requirements.txt # 后端Python依赖 (v2.1)
├── 📄 env_template.txt # .env文件的模板
│
├── 🐝 hive/ # 后端核心代码 (Python)
│ ├── agents/ # L2专家Agent库 (Seeker, Steward, Abacus)
│ ├── core/ # 核心组件 (CoreMemory)
│ ├── planning/ # Nexus AI核心 (executor.py, LangGraph)
│ └── utils/ # 工具函数 (配置加载, 日志)
│
├── 💻 frontend/ # 前端应用代码 (React + Next.js)
│ ├── src/
│ │ ├── components/
│ │ └── app/
│ ├── package.json
│ └── ...
│
└── 🚀 server.py # 后端FastAPI服务器主入口


---

### **🚀 快速开始**

#### **1. 环境要求**

- Python 3.10+
- Node.js 18+
- `pip` 和 `npm` (或 `yarn`, `pnpm`)

#### **2. 后端设置**

```bash
# 1. 克隆项目
git clone <repository-url>
cd hive-project

# 2. 创建并激活Python虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS / Linux
# venv\Scripts\activate    # Windows

# 3. 安装后端依赖 (使用 v2.1 版本的依赖文件)
pip install -r requirements.txt

# 4. 配置环境变量
# 从模板复制.env文件
cp env_template.txt .env

# 编辑 .env 文件，填入你的API密钥。
# 至少需要 DEEPSEEK_API_KEY 和 TAVILY_API_KEY

提示: env_template.txt 已被移除，您需要手动创建 .env 文件并填入 DEEPSEEK_API_KEY 和 TAVILY_API_KEY。

#### **3. 前端设置**

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装前端依赖
npm install
```

#### **4. 启动系统**

你需要两个独立的终端来分别运行后端和前端。

**终端 1: 启动后端API服务器**

```bash
# 确保你处于项目根目录，并已激活Python虚拟环境
python server.py
```

后端服务将运行在 http://localhost:8000。你会在终端看到详细的日志输出。

**终端 2: 启动前端开发服务器**

```bash
# 确保你处于frontend/目录
npm run dev
```

前端应用将运行在 http://localhost:3000 (或 Next.js 默认的其他端口)。

现在，在你的浏览器中打开前端应用的地址，即可开始与Hive交互。

---

### **📊 v1.0 总复盘 & v1.5 蓝图**

#### **v1.0 核心成果**

- **架构验证:** 成功验证了PRD中设想的核心技术栈（FastAPI, React, LangGraph）完全可行。
- **智能涌现:** 亲眼见证了 Nexus 展现出的多步规划、追问、甚至从工具报错中自我纠错的惊人能力。
- **鲁棒性突破:** ReflectorNode 的引入，是从工程角度为AI系统"兜底"的成功典范，解决了AI Agent开发中最棘手的稳定性问题之一。

#### **v1.0 核心失败：最终的"决策瘫痪"**

**根本原因:** 这不是一个Bug，这是一个架构性能力空缺。我们要求一个"高管"(Nexus)去做"数据分析师"的工作，但他手下却没有相应的"分析工具"或"汇报秘书"。Nexus 被我们制定的规则困在了原地，因为它缺乏完成分析所需的核心能力。

#### **Hive v1.5 核心使命: "专业化协同"**

基于v1.0的最终顿悟，v1.5的核心使命将是：为Nexus建立一支权责分明、能力互补的专业化L2团队，并教会Nexus如何指挥这支团队完成端到端的复杂工作流。

**新增Agents规划:**
- **CalendarAgent (日历专家)**
- **GridAgent (表格管家)**
- **SpokespersonAgent (首席发言人)**【名称待命】 