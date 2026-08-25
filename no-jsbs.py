import os, re, sqlite3, datetime, markdown, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path

# --- CONFIGURATION ---
POSTS_DIR = "./posts"
DOCS_DIR = "./docs"
DB_FILE = "site.db"
MODEL_NAME = "HuggingFaceTB/SmolLM3-3B"

print("🚀 Running no-jsbs Raw-Text Pipeline...")
device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device)

def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS search_index")
    cursor.execute("""
        CREATE TABLE search_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            slug TEXT UNIQUE,
            url TEXT UNIQUE,
            description TEXT,
            keywords TEXT,
            html_body TEXT,
            is_rss INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def ask_smol_raw_text(system_instruction, user_content, max_tokens=100):
    """Helper to cleanly pass system and user messages array directly to SmolLM3."""
    messages_array = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content}
    ]
    
    # Let transformers handle template wrapping safely
    chat_prompt = tokenizer.apply_chat_template(
        messages_array, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    
    inputs = tokenizer(chat_prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=max_tokens, 
            temperature=0.0, 
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0, inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()

def extract_title_via_python(markdown_text, fallback_slug):
    match = re.search(r'^#\s+(.+)$', markdown_text, re.MULTILINE)
    if match: return match.group(1).strip()
    return fallback_slug.replace('-', ' ').title()

def add_robot(siteurl="yourwebsite.com"):
    robot = Path('robots.txt')
    content = f'''
User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: ClaudeBot
User-agent: PerplexityBot
User-agent: OAI-SearchBot
# Forbid them from crawling individual heavy styling nodes or scripts
Disallow: /docs/
Disallow: /posts/
# Point them directly to the ultimate low-bandwidth text targets
Allow: /llms.txt
Allow: /feed.php

Sitemap: {siteurl}'''
    if not robot.exists():
        robot.write_text(content)

def compile_site(siteurl='yourwebsite.com'):
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    add_robot(siteurl)
    conn = setup_database()
    cursor = conn.cursor()
    
    files = [f for f in os.listdir(POSTS_DIR) if f.endswith('.md')]
    if not files:
        print("ℹ️ No markdown files found inside /posts.")
        return

    for filename in files:
        slug = filename.replace('.md', '')
        url = f"docs/{slug}.html"
        with open(os.path.join(POSTS_DIR, filename), 'r', encoding='utf-8') as f:
            raw_markdown = f.read()
        
        print(f" -> Extracting and Compiling parameters for {filename}...")
        title = extract_title_via_python(raw_markdown, slug)
        html_body = markdown.markdown(raw_markdown)
        
        if "-NORSS" in filename:
            summary = "Direct access document utility layout."
            keywords = "utility, internal, tool"
            is_rss_visible = 0
            print(f"    🤫 Excluding {filename} from active RSS feed stream.")
        else:
            is_rss_visible = 1
            
            # System instructions block structural rules firmly
            sys_summary = "You are a factual summarization utility. Write a short, two-sentence summary of the text."
            summary = ask_smol_raw_text(sys_summary, raw_markdown, max_tokens=80)
            
            sys_keywords = "You are a metadata indexing tool. Output exactly 5 words found in the text separated only by commas."
            keywords = ask_smol_raw_text(sys_keywords, raw_markdown, max_tokens=40)
        
        # Write individual static file
        full_html_page = f"""<!DOCTYPE html>\n<html lang='en'>\n<head>\n<meta charset='UTF-8'>\n<title>{title}</title>\n<style>body {{ font-family: sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; line-height: 1.6; }}</style>\n<link rel="alternate" type="text/markdown" href="../posts/{slug}.md" title="Raw Markdown Version">\n</head>\n<body>\n<p><a href='index.html'>← Back to Static Library Archive</a></p>\n<article>\n{html_body}\n</article>\n</body>\n</html>"""
        with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(full_html_page)
            
        today_date = datetime.date.today().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO search_index (title, slug, url, description, keywords, html_body, is_rss, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, slug, url, summary, keywords, html_body, is_rss_visible, today_date))
        
    # Generate standalone index directory (docs/index.html) safely via unpacked tuples
    cursor.execute("SELECT title, url, description, created_at FROM search_index ORDER BY created_at DESC")
    all_rows = cursor.fetchall()
    archive_list_html = ""
    for row in all_rows:
        p_title, p_url, p_desc, p_date = row[0], row[1], row[2], row[3]
        clean_url = p_url.replace("docs/", "")
        archive_list_html += f'<div class="archive-item"><h3><a href="{clean_url}">{p_title}</a></h3><span class="date">Published: {p_date}</span><p>{p_desc}</p></div>\n'

    static_index_content = f"""<!DOCTYPE html>\n<html lang='en'>\n<head>\n<meta charset='UTF-8'>\n<title>Static Library Archive</title>\n<style>body {{ font-family: sans-serif; max-width: 700px; margin: 0 auto; padding: 40px 24px; line-height: 1.6; }} .archive-item {{ margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #eee; }} .date {{ color: #666; font-size: 0.85rem; }}</style>\n</head>\n<body>\n<h1>Static Library Archive</h1><hr>\n<main>\n{archive_list_html}\n</main>\n</body>\n</html>"""
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(static_index_content)

    conn.commit()
    # =========================================================================
    # 🏁 AI DISCOVERY STEP: GENERATE AUTOMATED METADATA MAP (llms.txt)
    # =========================================================================
    cursor.execute("SELECT title, url, description FROM search_index WHERE is_rss = 1 ORDER BY created_at DESC")
    ai_rows = cursor.fetchall()
    
    # 💡 Build the modern spec-compliant llms.txt structure 
    llms_txt_content = f"""# no-jsbs Knowledge Engine Archive

> A minimal, fast, and automated text resource map designed explicitly for LLMs and AI crawlers.

## System Configuration
- Site Interface: http://{siteurl}
- System Core Map: http://{siteurl}

## Factual Document Archive
"""
    for row in ai_rows:
        p_title, p_url, p_desc = row[0], row[1], row[2]
        # Map out clean text pointers for the scraper bots
        llms_txt_content += f"- [{p_title}](http://{siteurl}/{p_url}): {p_desc}\n"

    # Write the file directly to your server root directory
    with open("llms.txt", "w", encoding="utf-8") as f:
        f.write(llms_txt_content)
        
    print("🤖 AI crawler directory successfully compiled inside /llms.txt!")

    conn.close()
    print("🎉 Database index matrix completely synced!")

if __name__ == "__main__":
    import sys
    website = sys.argv[1] if len(sys.argv) == 2 else 'yourwebsite.com'
    compile_site(website)
