#!/usr/bin/env python3
import os
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_static_rss_feed(db_path="site.db", posts_folder="posts", output_file="feed.xml", site_url=''):
    
    # 1. Connect to site.db and query rows from search_index
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
        print("ℹ No RSS-eligible posts found in search_index. Skipping feed step.")
        return

    # Explicitly register the namespace prefixes with Python's XML engine globally
    ET.register_namespace('content', 'http://purl.org')
    ET.register_namespace('atom', 'http://w3.org')

    # 2. Build out the structured XML document object
    # FIX: Remove the manual 'attrib' dictionary completely so properties don't double up
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = "No-jsbs Blog"
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = "A fast, zero-javascript minimalist development blog."

    # 3. Process the dataset rows
    for post in posts:
        slug = post['slug']
        md_file_path = os.path.join(posts_folder, f"{slug}.md")
        raw_markdown = ""

        # Read the raw physical markdown file exactly as it sits on disk
        if os.path.exists(md_file_path):
            with open(md_file_path, "r", encoding="utf-8") as f:
                raw_markdown = f.read()
        else:
            print(f"⚠ Warning: Could not find raw file at {md_file_path}")
            continue

        # 4. Populate standard RSS node attributes
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post['title']
        ET.SubElement(item, "link").text = f"{site_url}index.php?view={slug}"
        ET.SubElement(item, "description").text = post['description'] if post['description'] else post['title']
        
        # 5. Direct Raw Markdown Dump into the required content:encoded tag
        content_encoded = ET.SubElement(item, "{http://purl.org}encoded")
        content_encoded.text = f"<![CDATA[{raw_markdown}]]>"
        
        # Parse timestamp string or fall back to system execution time if empty
        try:
            date_cleaned = post['created_at'].split(" ")  # Isolate YYYY-MM-DD safely
            dt = datetime.strptime(date_cleaned[0], "%Y-%m-%d")
            pub_date_str = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            pub_date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
            
        ET.SubElement(item, "pubDate").text = pub_date_str
        ET.SubElement(item, "guid").text = f"{site_url}index.php?view={slug}"

    # 6. Generate text and clean string characters
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    
    xml_str = ET.tostring(rss, encoding="utf-8").decode("utf-8")
    xml_str = xml_str.replace("&lt;![CDATA[", "<![CDATA[").replace("]]&gt;", "]]>")
    
    # 7. Physical disk deployment step
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n' + xml_str)
        
    print(f"✓ Static RSS feed compiled -> {len(posts)} posts cleanly configured for Chrome validation.")

if __name__ == "__main__":
    import sys
    generate_static_rss_feed(site_url=sys.argv[1])
