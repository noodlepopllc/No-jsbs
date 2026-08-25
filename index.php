<?php
// index.php - Dual-mode dashboard embedding compiled HTML content straight from SQLite
$db = new SQLite3('site.db');
$search = $_GET['q'] ?? null;
$view_slug = $_GET['view'] ?? null; // 💡 NEW: Triggers dynamic dashboard page rendering

$sidebar_results = $db->query("SELECT title, slug, url FROM search_index ORDER BY created_at DESC LIMIT 20");
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>no-jsbs Search Dashboard</title>
    <link rel="stylesheet" href="./style.css">
    <link rel="alternate" type="application/rss+xml" href="feed.php" title="RSS Feed">
</head>
<body>

<div class="layout">
    <!-- 🎛️ SIDEBAR NAV PORTAL -->
    <aside class="sidebar">
        <h2><a href="index.php">no-jsbs Dashboard</a></h2>
        <a href="feed.php" target="_blank" class="rss-link">📡 Subscribe via RSS XML</a>
        
        <form method="GET" action="index.php" class="search-form">
            <input type="text" name="q" class="search-input" placeholder="Search summaries..." value="<?php echo htmlspecialchars($search ?? ''); ?>">
            <button type="submit" class="search-button">Search</button>
        </form>
        
        <h3>All Articles</h3>
        <ul>
            <?php if ($sidebar_results): ?>
                <?php while ($row = $sidebar_results->fetchArray(SQLITE3_ASSOC)): ?>
                    <li>
                        <!-- 💡 Embedded view link keeps users inside the dashboard layout -->
                        <a href="index.php?view=<?php echo urlencode($row['slug']); ?>">
                            <?php echo htmlspecialchars($row['title']); ?>
                        </a>
                    </li>
                <?php endwhile; ?>
            <?php endif; ?>
        </ul>
    </aside>

    <!-- 📄 BODY INTERFACE CONTAINER -->
    <main class="main-panel">
        <?php 
        // 🚀 PATH 1: Dynamic Article View (Embed content body right inside the PHP shell)
        if ($view_slug): 
            $stmt = $db->prepare("SELECT title, url, html_body, created_at FROM search_index WHERE slug = :slug");
            $stmt->bindValue(':slug', $view_slug);
            $post = $stmt->execute()->fetchArray(SQLITE3_ASSOC);

            if ($post): ?>
                <h1><?php echo htmlspecialchars($post['title']); ?></h1>
                <div style="display: flex; gap: 16px; margin-top: -8px; margin-bottom: 24px;">
                    <span class="date">📅 Published: <?php echo htmlspecialchars($post['created_at']); ?></span>
                    <!-- 💡 Option to read or share the direct standalone 100% static leaf file alternative -->
                    <a href="<?php echo htmlspecialchars($post['url']); ?>" target="_blank" style="font-size: 0.85rem; color: var(--brand-link); text-decoration: none; font-weight: 600;">📄 View Standalone Static Page →</a>
                </div>
                <hr>
                <!-- Dumps the raw compiled HTML body directly onto the page container node canvas -->
                <article class="prose-content">
                    <?php echo $post['html_body']; ?>
                </article>
            <?php else: ?>
                <h1>Article Not Found</h1>
                <p>The requested document content index could not be located inside the local SQLite table cache.</p>
            <?php endif; ?>

        <?php 
        // 🔍 PATH 2: Search Engine Results view
        elseif ($search): ?>
            <h1>Search Matches</h1>
            <p style="color: var(--text-alt); margin-top: -8px;">Filtering indices for: "<strong><?php echo htmlspecialchars($search); ?></strong>"</p>
            <hr>
            <?php
            $stmt = $db->prepare("SELECT * FROM search_index WHERE title LIKE :q OR description LIKE :q OR keywords LIKE :q ORDER BY created_at DESC");
            $stmt->bindValue(':q', '%' . $search . '%');
            $results = $stmt->execute();
            
            $count = 0;
            if ($results) {
                while ($row = $results->fetchArray(SQLITE3_ASSOC)): $count++; ?>
                    <div class="search-item">
                        <!-- Links click straight into the embedded view template -->
                        <h3><a href="index.php?view=<?php echo urlencode($row['slug']); ?>"><?php echo htmlspecialchars($row['title']); ?></a></h3>
                        <span class="date">Published: <?php echo htmlspecialchars($row['created_at']); ?></span>
                        <p><?php echo htmlspecialchars($row['description']); ?></p>
                        <?php if (!empty($row['keywords'])): ?>
                            <p class="tags">🏷️ Keywords: <?php echo htmlspecialchars($row['keywords']); ?></p>
                        <?php endif; ?>
                    </div>
                <?php endwhile;
            }
            if ($count === 0) echo "<p>No matching document indices found.</p>";
            ?>

        <?php 
        // 🏡 PATH 3: Default Empty State Hub Canvas Overview
        else: ?>
            <h1>Knowledge Base Overview</h1>
            <hr>
            <p>Welcome to your <strong>no-jsbs</strong> workspace framework engine.</p>
            <p>Select any tutorial or post from the dynamic sidebar list to read its article text directly inside this dashboard container workspace, or utilize the text filter tracking tools above to index specific search snippets.</p>
        <?php endif; ?>
    </main>
</div>

</body>
</html>
