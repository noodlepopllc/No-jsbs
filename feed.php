<?php
// feed.php - Clean production RSS feed module for the no-jsbs framework
header("Content-Type: application/rss+xml; charset=UTF-8");

// Safely configure server paths to avoid domain slash clipping bugs
$site_url = "http://" . $_SERVER['HTTP_HOST'] . str_replace('/feed.php', '', $_SERVER['REQUEST_URI']);

$db = new SQLite3('site.db');
$results = $db->query("SELECT * FROM search_index WHERE is_rss = 1 ORDER BY created_at DESC LIMIT 25");

echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
echo '<rss version="2.0">' . "\n";
echo "  <channel>\n";
echo "    <title>no-jsbs Master Feed</title>\n";
echo "    <link>" . $site_url . "/docs/index.html</link>\n";
echo "    <description>Dynamic summary logs broadcast via local SmolLM pipelines.</description>\n";

if ($results) {
    while ($post = $results->fetchArray(SQLITE3_ASSOC)) {
        $item_url = $site_url . "/" . $post['url'];
        $date_obj = new DateTime($post['created_at']);
        $rfc_date = $date_obj->format('D, d M Y H:i:s \G\M\T');
        
        $clean_description = "SUMMARY:\n" . html_entity_decode($post['description']) . "\n\n";
        $clean_description .= "TAGS:\n" . html_entity_decode($post['keywords']);
        
        // 💡 FIXED: Strict, flat string indention blocks with clean newlines
        echo "    <item>\n";
        echo "      <title>" . htmlspecialchars($post['title']) . "</title>\n";
        echo "      <link>" . htmlspecialchars($item_url) . "</link>\n";
        echo "      <guid isPermaLink=\"true\">" . htmlspecialchars($item_url) . "</guid>\n";
        echo "      <pubDate>" . $rfc_date . "</pubDate>\n";
        echo "      <description><![CDATA[" . $clean_description . "]]></description>\n";
        echo "    </item>\n";
    }
}

echo "  </channel>\n";
echo "</rss>";
?>
