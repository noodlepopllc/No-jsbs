# no-jsbs 🚀

The local AI-powered static site compiler with absolutely zero JavaScript bullshit.

`no-jsbs` lets you write content using standard static **Markdown**, leverages a fast local **Hugging Face SmolLM model** to distill content down into optimal search snippets, updates a relational metadata index, and serves it using a lightweight **PHP** shell layout script.

## 💎 Features
- **100% No-JS**: Zero hydration, zero script tag injection, zero front-end overhead.
- **Local AI Compiling**: Uses `HuggingFaceTB/SmolLM3-3B` locally to generate titles and search summaries.
- **True Static Leaves**: Content files are standard compiled standalone HTML layout structures.
- **Hybrid Performance**: PHP handles structural layout framing and dynamic keyword searches without bloat.

## 🛠️ Local Installation Requirements
Ensure your workspace includes Python 3.8+ and standard PHP server modules.

```bash
pip install markdown torch transformers accelerators
```

## 🚀 Working Workflow
1. Clone this repository locally.
2. Put your raw `.md` content articles inside the `/posts` folder.
3. Compile your database matrix:
   ```bash
   python no-jsbs.py
   ```
4. Fire up your dynamic dashboard workspace using a standard local PHP server environment pointing to `index.php`.
