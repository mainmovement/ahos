# ahos_llm_bridge.ps1 - local Anthropic-compatible bridge for Claude Code.
# Claude (Node) -> localhost -> PowerShell Invoke-WebRequest -> OpenRouter (then Groq fallback).
param([int]$Port = 8787)
$ErrorActionPreference = 'Stop'
$or = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','User')
if (-not $or) { $or = [Environment]::GetEnvironmentVariable('ANTHROPIC_AUTH_TOKEN','User') }
$gq = [Environment]::GetEnvironmentVariable('GROQ_API_KEY','User')
if (-not $or -and -not $gq) { throw 'No OPENROUTER_API_KEY or GROQ_API_KEY in User env' }
$prefix = "http://127.0.0.1:$Port/"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add($prefix)
$listener.Start()
"$(Get-Date -Format s) bridge listening on $prefix" | Out-File -Append -Encoding utf8 (Join-Path $PSScriptRoot 'ahos_llm_bridge.log')

function Write-JsonResponse($ctx, [int]$code, $obj) {
  $json = if ($obj -is [string]) { $obj } else { $obj | ConvertTo-Json -Depth 40 -Compress }
  $bytes = [Text.Encoding]::UTF8.GetBytes($json)
  $ctx.Response.StatusCode = $code
  $ctx.Response.ContentType = 'application/json; charset=utf-8'
  $ctx.Response.ContentLength64 = $bytes.Length
  $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
  $ctx.Response.OutputStream.Close()
}

function Read-Body($req) {
  $reader = New-Object IO.StreamReader($req.InputStream, $req.ContentEncoding)
  try { return $reader.ReadToEnd() } finally { $reader.Close() }
}

function Invoke-OpenRouter([string]$body) {
  $headers = @{ Authorization = "Bearer $or"; 'anthropic-version' = '2023-06-01' }
  return Invoke-WebRequest -UseBasicParsing -Method Post -Uri 'https://openrouter.ai/api/v1/messages' -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 300
}

function ConvertTo-OpenAIChat([string]$anthropicBody) {
  $j = $anthropicBody | ConvertFrom-Json
  $msgs = @()
  if ($j.system) {
    $sys = $j.system
    if ($sys -is [string]) { $msgs += @{ role = 'system'; content = $sys } }
    else {
      $parts = @()
      foreach ($b in @($sys)) { if ($b.type -eq 'text') { $parts += $b.text } elseif ($b.text) { $parts += $b.text } }
      $msgs += @{ role = 'system'; content = ($parts -join "`n") }
    }
  }
  foreach ($m in @($j.messages)) {
    $role = $m.role
    $c = $m.content
    if ($c -is [string]) { $msgs += @{ role = $role; content = $c } }
    else {
      $texts = @()
      foreach ($b in @($c)) {
        if ($b.type -eq 'text') { $texts += $b.text }
        elseif ($b.type -eq 'tool_result') { $texts += ("tool_result $($b.tool_use_id): $($b.content)") }
        elseif ($b.type -eq 'tool_use') { $texts += ("tool_use $($b.name): $($b.input | ConvertTo-Json -Compress)") }
        elseif ($b.text) { $texts += $b.text }
      }
      $msgs += @{ role = $role; content = ($texts -join "`n") }
    }
  }
  $max = 1024
  if ($j.max_tokens) { $max = [int]$j.max_tokens }
  return (@{ model = 'openai/gpt-oss-20b'; max_tokens = $max; messages = $msgs } | ConvertTo-Json -Depth 20)
}

function Invoke-GroqFromAnthropic([string]$body) {
  $chat = ConvertTo-OpenAIChat $body
  $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri 'https://api.groq.com/openai/v1/chat/completions' -Headers @{ Authorization = "Bearer $gq" } -ContentType 'application/json' -Body $chat -TimeoutSec 300
  $o = $r.Content | ConvertFrom-Json
  $text = $o.choices[0].message.content
  $out = @{
    id = $o.id
    type = 'message'
    role = 'assistant'
    model = $o.model
    content = @(@{ type = 'text'; text = $text })
    stop_reason = 'end_turn'
    stop_sequence = $null
    usage = @{ input_tokens = 0; output_tokens = 0 }
  }
  return ($out | ConvertTo-Json -Depth 20 -Compress)
}

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  try {
    $path = $ctx.Request.Url.AbsolutePath.TrimEnd('/')
    if ($ctx.Request.HttpMethod -eq 'GET' -and ($path -eq '' -or $path -eq '/health')) {
      Write-JsonResponse $ctx 200 (@{ ok = $true; openrouter = [bool]$or; groq = [bool]$gq })
      continue
    }
    if ($ctx.Request.HttpMethod -eq 'GET' -and $path -eq '/v1/models') {
      Write-JsonResponse $ctx 200 (@{ data = @(@{ id = 'openrouter/free'; object = 'model' }, @{ id = 'claude-sonnet-4-5'; object = 'model' }) })
      continue
    }
    if ($ctx.Request.HttpMethod -eq 'POST' -and ($path -eq '/v1/messages' -or $path -eq '/messages')) {
      $body = Read-Body $ctx.Request
      # Force free router model for coding sessions
      try {
        $j = $body | ConvertFrom-Json
        $j.model = 'openrouter/free'
        $body = $j | ConvertTo-Json -Depth 40 -Compress
      } catch {}
      $ok = $false
      if ($or) {
        try {
          $r = Invoke-OpenRouter $body
          Write-JsonResponse $ctx ([int]$r.StatusCode) $r.Content
          $ok = $true
        } catch {
          "$(Get-Date -Format s) OR fail: $($_.Exception.Message)" | Out-File -Append -Encoding utf8 (Join-Path $PSScriptRoot 'ahos_llm_bridge.log')
        }
      }
      if (-not $ok -and $gq) {
        try {
          $g = Invoke-GroqFromAnthropic $body
          Write-JsonResponse $ctx 200 $g
          $ok = $true
        } catch {
          "$(Get-Date -Format s) GROQ fail: $($_.Exception.Message)" | Out-File -Append -Encoding utf8 (Join-Path $PSScriptRoot 'ahos_llm_bridge.log')
          Write-JsonResponse $ctx 502 (@{ type = 'error'; error = @{ type = 'api_error'; message = "bridge failover failed: $($_.Exception.Message)" } })
        }
      } elseif (-not $ok) {
        Write-JsonResponse $ctx 502 (@{ type = 'error'; error = @{ type = 'api_error'; message = 'openrouter failed and no groq key' } })
      }
      continue
    }
    if ($ctx.Request.HttpMethod -eq 'POST' -and $path -like '*/count_tokens') {
      Write-JsonResponse $ctx 200 (@{ input_tokens = 1000 })
      continue
    }
    Write-JsonResponse $ctx 404 (@{ error = 'not found'; path = $path })
  } catch {
    try { Write-JsonResponse $ctx 500 (@{ type = 'error'; error = @{ type = 'api_error'; message = $_.Exception.Message } }) } catch {}
  }
}
