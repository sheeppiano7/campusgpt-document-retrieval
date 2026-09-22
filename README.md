# CampusGPT：带来源引用的课程资料 RAG 助手

CampusGPT 面向大学课程复习场景。用户可以上传一份或多份 PDF，系统提取原始页码、切分文本、建立本地检索索引，再返回带文件名、页码和原文证据的回答。

应用在没有 API Key 时也能使用本地证据摘要；配置大模型后，可基于检索片段生成带引用的回答。上传内容只在当前进程内处理，API Key 不写入项目文件。

## 功能

- 多 PDF 上传、解析和文件大小校验；
- 保留原始文件名和页码，空白页不会导致页码错位；
- 使用字符 TF-IDF 支持连续中文检索；
- 设置最低相似度阈值，无匹配时拒绝强行回答；
- 支持本地证据摘要、OpenAI 兼容接口、Ollama 本地模型；
- 回答展示引用编号，可展开查看原文、来源页码和匹配分数；
- 提示词要求模型只使用检索证据，并忽略资料内部试图改变规则的文字；
- 自带检索评估脚本和自动化测试。

## 工作流程

```text
上传 PDF → 按页解析 → 重叠切分 → TF-IDF 索引 → Top-K 检索
                                                     ↓
原文证据与页码 ← 引用编号 ← 本地摘要或可选大模型回答
```

## 回答模式

### 本地证据摘要

无需网络和密钥，直接返回相关原文并标注来源。这个模式已经完成本机端到端验证。

### OpenAI 兼容接口

支持提供 `/chat/completions` 的兼容服务。在页面侧栏填写接口地址、模型名称和 API Key，或使用环境变量：

```powershell
$env:CAMPUSGPT_BASE_URL="https://api.openai.com/v1"
$env:CAMPUSGPT_MODEL="gpt-4.1-mini"
$env:CAMPUSGPT_API_KEY="your-key"
```

### Ollama 本地模型

安装并启动 Ollama 后，在页面中填写服务地址和本地模型名称。默认示例为 `http://127.0.0.1:11434` 和 `qwen2.5:3b`。

> OpenAI兼容和Ollama请求格式已经通过本地模拟服务测试。真实模型的回答质量仍取决于所选模型、资料和问题，不能用模拟测试代替真实模型评估。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

浏览器访问：`http://127.0.0.1:8501`

## 自动化测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

当前共 **21 项测试通过**，覆盖PDF解析、切分边界、中文检索、无匹配、来源元数据、无证据拒答、引用生成、两种模型接口契约及Streamlit页面状态。

## 检索评估

```powershell
.\.venv\Scripts\python.exe evaluation\run_retrieval_eval.py
```

仓库中的小型合成数据集包含5个问题，用于确认评估流程和回归基线。当前结果为 `Recall@3 = 1.0`、`MRR = 1.0`，所有目标片段排名第1。该数据集规模很小，结果不能代表真实课程资料上的检索准确率。

## 目录

```text
app.py                         Streamlit 页面与交互
rag/pdf_loader.py              PDF 解析和来源元数据
rag/text_splitter.py           重叠文本切分
rag/simple_search.py           本地 TF-IDF 检索
rag/answer_engine.py           本地摘要及可选模型接口
tests/                         自动化测试
evaluation/                    合成评估数据、脚本和结果
.env.example                   可选模型配置模板
```

## 已知限制

- 扫描型 PDF 需要先进行 OCR；
- 当前索引保存在内存中，重启应用后需要重新上传；
- TF-IDF 擅长关键词匹配，不等同于向量语义检索；
- 尚未使用真实课程问答集评估答案正确性和引用忠实度；
- 未配置真实模型服务时，只能声明接口契约测试通过，不能声明真实大模型调用成功。
