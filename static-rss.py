#!/usr/bin/env python3
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime

def generate_static_rss_feed(db_path="site.db", output_file="feed.xml", site_url=''):
    
    # 1. Connect to site.db and query rows from search_index
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by text names
    cursor = conn.cursor()
    
    # Pull schema fields based on your design definitions
    cursor.execute("""
        SELECT title, slug, description, html_body, created_at 
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

    # 2. Build out the structured XML document object
    rss = ET.Element("rss", version="2.0", 
                     xmlns_atom="http://w3.org",
                     xmlns_content="http://purl.org")
    channel = ET.SubElement(rss, "channel")
    
    ET.SubElement(channel, "title").text = "No-jsbs Blog"
    ET.SubElement(channel, "link").text = site_url
    ET.SubElement(channel, "description").text = "A fast, zero-javascript minimalist development blog."

    # 3. Process the dataset rows
    for post in posts:
        slug = post['slug']
        html_body = post['html_body'] if post['html_body'] else ""
        
        # 4. Resolve local paths to absolute domain coordinates
        absolute_html = html_body.replace('href="index.php', f'href="{site_url}index.php')
        absolute_html = absolute_html.replace('src="', f'src="{site_url}')

        # 5. Populate standard RSS node attributes
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post['title']
        ET.SubElement(item, "link").text = f"{site_url}index.php?view={slug}"
        
        # Extract the description field as an introductory excerpt snippet
        ET.SubElement(item, "description").text = post['description'] if post['description'] else post['title']
        
        # Pack the full code-highlighted post inside the required CDATA block
        content_encoded = ET.SubElement(item, "content:encoded")
        content_encoded.text = f"<![CDATA[{absolute_html}]]>"
        
        # Parse timestamp string or fall back to system execution time if empty
        try:
            date_cleaned = post['created_at'].split(" ")[0]  # Isolate YYYY-MM-DD
            dt = datetime.strptime(date_cleaned, "%Y-%m-%d")
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
        
    print(f"✓ Static RSS feed compiled using '{db_path}' -> {len(posts)} posts written to {output_file}")

if __name__ == "__main__":
    generate_static_rss_feed(site_url='http://mywebsite.url')
