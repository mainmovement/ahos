Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

# Load both images
$ownerRef = [Drawing.Image]::FromFile("G:/robat/ahos/reports/dashboard/screens/01_dashboard_fix/owner_reference.jpg")
$fixed = [Drawing.Image]::FromFile("G:/robat/ahos/reports/dashboard/screens/01_dashboard_fix/dashboard_2026-10-16.png")

# Create side-by-side canvas
$canvasWidth = $ownerRef.Width + $fixed.Width + 40
$canvasHeight = [Math]::Max($ownerRef.Height, $fixed.Height) + 80
$canvas = New-Object Drawing.Bitmap $canvasWidth, $canvasHeight
$graphics = [Drawing.Graphics]::FromImage($canvas)
$graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias

# Fill background
$graphics.Clear([Drawing.Color]::FromArgb(30, 30, 30))

# Draw titles
$font = New-Object Drawing.Font("Arial", 18, [Drawing.FontStyle]::Bold)
$brush = New-Object Drawing.SolidBrush([Drawing.Color]::White)
$graphics.DrawString("Owner Reference", $font, $brush, 20, 20)
$graphics.DrawString("Fixed Dashboard", $font, $brush, $ownerRef.Width + 40, 20)

# Draw images
$graphics.DrawImage($ownerRef, 20, 50)
$graphics.DrawImage($fixed, $ownerRef.Width + 40, 50)

# Save result
$canvas.Save("G:/robat/ahos/reports/dashboard/screens/01_dashboard_fix/comparison_2026-10-16.png", "PNG")

$font.Dispose()
$brush.Dispose()
$graphics.Dispose()
$ownerRef.Dispose()
$fixed.Dispose()

Write-Host "Comparison image saved successfully"
