param([int]$Port = 8787)
$ErrorActionPreference = 'Continue'
$or = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
$gq = [Environment]::GetEnvironmentVariable('GROQ_API_KEY', 'User')
$log = Join-Path $PSScriptRoot 'ahos_llm_bridge.log'
function Log([string]$m) { "$(Get-Date -Format s) $m" | Out-File -Append -Encoding utf8 $log }
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()
Log "listen-iwr $Port or=$([bool]$or) groq=$([bool]$gq)"

function Reply($ctx, [int]$code, [string]$text) {
  $bytes = [Text.Encoding]::UTF8.GetBytes($text)
  $ctx.Response.StatusCode = $code
  $ctx.Response.ContentType = 'application/json; charset=utf-8'
  $ctx.Response.ContentLength64 = $bytes.Length
  $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
  $ctx.Response.Close()
}

function Post-Iwr([string]$url, [hashtable]$headers, [string]$body) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 180
    return @{ ok = $true; code = [int]$r.StatusCode; text = $r.Content }
  }
  catch {
    $code = 0; $text = $_.Exception.Message
    if ($_.Exception.Response) {
      $code = [int]$_.Exception.Response.StatusCode
      try {
        $stream = $_.Exception.Response.GetResponseStream()
        $sr = New-Object IO.StreamReader($stream)
        $text = $sr.ReadToEnd()
        $sr.Close()
      } catch {}
    }
    return @{ ok = $false; code = $code; text = $text }
  }
}

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $path = $ctx.Request.Url.AbsolutePath.TrimEnd('/')
  $method = $ctx.Request.HttpMethod
  try {
    if ($method -eq 'GET' -and ($path -eq '' -or $path -eq '/health')) { Reply $ctx 200 '{"ok":true}'; continue }
    if ($method -eq 'GET' -and $path -eq '/v1/models') { Reply $ctx 200 '{"data":[{"id":"openrouter/free","object":"model"}]}'; continue }
    if ($method -eq 'POST' -and $path -like '*count_tokens*') { Reply $ctx 200 '{"input_tokens":1000}'; continue }
    if ($method -eq 'POST' -and ($path -eq '/v1/messages' -or $path -eq '/messages')) {
      $reader = New-Object IO.StreamReader($ctx.Request.InputStream)
      $body = $reader.ReadToEnd()
      $reader.Close()
      if ($body -match '"model"') {
        $body = [regex]::Replace($body, '"model"\s*:\s*"[^"]*"', '"model":"openrouter/free"', 1)
      }
      Log ("REQ bytes=" + $body.Length)
      $r = Post-Iwr 'https://openrouter.ai/api/v1/messages' @{
        Authorization = "Bearer $or"
        'anthropic-version' = '2023-06-01'
        'HTTP-Referer' = 'https://github.com/anthropics/claude-code'
        'X-Title' = 'AHOS-Claude-Bridge'
      } $body
      $head = if ($r.text.Length -gt 300) { $r.text.Substring(0, 300) } else { $r.text }
      Log "OR code=$($r.code) ok=$($r.ok) head=$head"
      if ($r.ok) { Reply $ctx 200 $r.text; continue }

      if ($gq) {
        $matches = [regex]::Matches($body, '"text"\s*:\s*"(.*?)"')
        $plain = (($matches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Last 2) -join ' ')
        if (-not $plain) { $plain = 'Continue the coding task.' }
        $gbody = (@{
          model = 'openai/gpt-oss-20b'
          max_tokens = 1024
          messages = @(@{ role = 'user'; content = $plain })
        } | ConvertTo-Json -Compress)
        $g = Post-Iwr 'https://api.groq.com/openai/v1/chat/completions' @{ Authorization = "Bearer $gq" } $gbody
        $ghead = if ($g.text.Length -gt 200) { $g.text.Substring(0, 200) } else { $g.text }
        Log "GROQ code=$($g.code) ok=$($g.ok) head=$ghead"
        if ($g.ok) {
          $o = $g.text | ConvertFrom-Json
          $text = [string]$o.choices[0].message.content
          $anth = @{
            id = $o.id; type = 'message'; role = 'assistant'; model = $o.model
            content = @(@{ type = 'text'; text = $text })
            stop_reason = 'end_turn'
            usage = @{ input_tokens = 0; output_tokens = 0 }
          } | ConvertTo-Json -Depth 6 -Compress
          Reply $ctx 200 $anth
          continue
        }
      }
      $msg = "upstream $($r.code) "
      if ($r.text.Length -gt 200) { $msg += $r.text.Substring(0, 200) } else { $msg += $r.text }
      Reply $ctx 502 ((@{ type = 'error'; error = @{ type = 'api_error'; message = $msg } } | ConvertTo-Json -Compress))
      continue
    }
    Reply $ctx 404 '{"error":"not found"}'
  }
  catch {
    $em = $_.Exception.Message -replace '"', ''
    try { Reply $ctx 500 ('{"type":"error","error":{"type":"api_error","message":"' + $em + '"}}') } catch {}
  }
}
