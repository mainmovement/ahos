Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Start-Sleep -Seconds 2

$screen = [Windows.Forms.Screen]::PrimaryScreen
$bounds = $screen.Bounds
$bitmap = New-Object Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size, [Drawing.CopyPixelOperation]::SourceCopy)
$bitmap.Save("G:/robat/ahos/reports/dashboard/screens/01_dashboard_fix/dashboard_2026-10-16.png", "PNG")
$graphics.Dispose()
$bitmap.Dispose()
Write-Host "Screenshot saved successfully"
