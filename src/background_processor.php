<?php
// This runs in background - no output needed
require 'vendor/autoload.php';

// Get arguments
$csv_file = $argv[1];
$pdf_file = $argv[2];
$page_size = $argv[3];
$orientation = $argv[4];
$header_row = $argv[5];
$log_file = $argv[6];

// Log start
file_put_contents($log_file, "[" . date('Y-m-d H:i:s') . "] Background processing started\n", FILE_APPEND);

try {
    // Initialize TCPDF
    $pdf = new TCPDF($orientation, 'mm', $page_size, true, 'UTF-8', false);
    
    // PDF metadata
    $pdf->SetCreator('PDFToolsLover.com');
    $pdf->SetAuthor('CSV to PDF Converter');
    $pdf->SetTitle('Converted CSV Document');
    $pdf->SetMargins(15, 15, 15);
    $pdf->AddPage();
    
    // Read CSV
    $csv_data = [];
    if (($handle = fopen($csv_file, "r")) !== false) {
        while (($row = fgetcsv($handle, 10000, ",")) !== false) {
            $csv_data[] = $row;
        }
        fclose($handle);
    }
    
    // Create HTML table
    $html = '<table border="1" cellpadding="4" style="width:100%">';
    foreach ($csv_data as $i => $row) {
        $html .= '<tr>';
        foreach ($row as $cell) {
            // Apply header style if first row and header enabled
            if ($i === 0 && $header_row === '1') {
                $html .= '<th style="background-color:#f8f9fa;font-weight:bold;padding:5px;">' 
                       . htmlspecialchars($cell) . '</th>';
            } else {
                $html .= '<td style="padding:5px;">' . htmlspecialchars($cell) . '</td>';
            }
        }
        $html .= '</tr>';
    }
    $html .= '</table>';
    
    // Write to PDF
    $pdf->writeHTML($html, true, false, true, false, '');
    $pdf->Output($pdf_file, 'F');
    
    // Cleanup CSV
    unlink($csv_file);
    
    // Log success
    file_put_contents($log_file, "[" . date('Y-m-d H:i:s') . "] Conversion completed successfully\n", FILE_APPEND);
    
    // Ping Bing
    $bing_url = "https://www.bing.com/indexnow?url=https://pdftoolslover.com/csv-to-pdf-pro/&key=ec2fb07f1c6e4f81b832a3e04ae36f92";
    @file_get_contents($bing_url);
    
} catch (Exception $e) {
    // Log errors
    file_put_contents($log_file, "[" . date('Y-m-d H:i:s') . "] ERROR: " . $e->getMessage() . "\n", FILE_APPEND);
    
    // Cleanup on error
    if (file_exists($csv_file)) @unlink($csv_file);
    if (file_exists($pdf_file)) @unlink($pdf_file);
}
?>
