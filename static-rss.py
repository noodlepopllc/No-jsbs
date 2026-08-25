#!/usr/bin/env python3
import os
import sqlite3
import markdown
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_static_rss_feed(db_path="site.db", posts_folder="posts", output_file="feed.xml"):
    site_url = "https://noodle-pop.com"
    
    # 1. Connect to site.db and query eligible RSS rows to find the exact filenames
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, slug, description, created_at 
        FROM search_index 
        WHERE is_rss = 1
        ORDER BY created_at DESC 
        LIMIT 15
    """)
    posts = cursor.fetchall()
    conn.close()

    if not posts:
        print("ℹ No RSS-eligible posts found in database. Skipping feed step.")
        return

    # 2. Build out the structured XML document object
    rss = ET.Element("rss", version="2.0", 
                     xmlns_atom="http://w3.org",
                     xmlns_content="http://purl.org")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = "No-jsbs Blog"
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = "A fast, zero-javascript minimalist development blog."

    # 3. Process the dataset rows by reading the actual local filesystem Markdown files
    for post in posts:
        slug = post['slug']
        md_filename = f"{slug}.md"
        md_file_path = os.path.join(posts_folder, md_filename)
        
        # Fallback raw markdown content placeholder
        raw_markdown = ""
        
        # Read the actual physical markdown file contents
        if os.path.exists(md_file_path):
            with open(md_file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                
                # Check for and strip the YAML front-matter metadata block if it exists
                if raw_content.startswith("---"):
                    parts = raw_content.split("---", 2)
                    if len(parts) >= 3:
                        raw_markdown = parts[2].strip()
                    else:
                        raw_markdown = raw_content.strip()
                else:
                    raw_markdown = raw_content.strip()
        else:
            print(f"⚠ Warning: Could not find physical markdown file at {md_file_path}")
            continue

        # 4. Compile the raw markdown content cleanly to standard HTML for the RSS reader layout
        compiled_html = markdown.markdown(raw_markdown, extensions=['fenced_code', 'codehilite'])
        
        # 5. Resolve relative path structures to absolute domain URLs
        absolute_html = compiled_html.replace('href="index.php', f'href="{site_url}index.php')
        absolute_html = absolute_html.replace('src="', f'src="{site_url}')

        # 6. Populate standard RSS node attributes
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post['title']
        ET.SubElement(item, "link").text = f"{site_url}index.php?view={slug}"
        ET.SubElement(item, "description").text = post['description'] if post['description'] else post['title']
        
        # Pack the clean raw compiled file data directly into the required CDATA block
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = f"<![CDATA[{absolute_html}]]>"
        
        # Parse timestamp string or fall back to system execution time if empty
        try:
            date_cleaned = post['created_at'].split(" ")[0]  # Isolate YYYY-MM-DD string
            dt = datetime.strptime(date_cleaned, "%Y-%m-%d")
            pub_date_str = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pub_date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
            
        ET.SubElement(item, "pubDate").text = pub_date_str
        ET.SubElement(item, "guid").text = f"{site_url}index.php?view={slug}"

    # 7. Generate text and clean string characters
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    
    xml_str = ET.tostring(rss, encoding="utf-8").decode("utf-8")
    xml_str = xml_str.replace("&lt;![CDATA[", "<![CDATA[").replace("]]&gt;", "]]>")
    
    # 8. Physical disk deployment step
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
        
    print(f"✓ Static RSS feed compiled cleanly -> {len(posts)} markdown file dumps written to {output_file}")

if __name__ == "__main__":
    generate_static_rss_feed()
