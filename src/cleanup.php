<?php
// Run every hour via cron: 0 * * * * /usr/bin/php /path/to/cleanup.php

// Cleanup old files (older than 30 minutes)
$now = time();
$max_age = 1800; // 30 minutes in seconds

// Process uploads
foreach (glob("tmp_uploads/*.csv") as $file) {
    if ($now - filemtime($file) > $max_age) {
        @unlink($file);
    }
}

// Process PDFs
foreach (glob("tmp_pdfs/*.pdf") as $file) {
    if ($now - filemtime($file) > $max_age) {
        @unlink($file);
    }
}

// Process logs (keep for 24 hours)
foreach (glob("logs/*.log") as $file) {
    if ($now - filemtime($file) > 86400) {
        @unlink($file);
    }
}

// Process queued cleanups
if (file_exists("cleanup_queue.txt")) {
    $queue = file("cleanup_queue.txt", FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($queue as $id) {
        @unlink("tmp_pdfs/{$id}.pdf");
    }
    @unlink("cleanup_queue.txt");
}
?>
