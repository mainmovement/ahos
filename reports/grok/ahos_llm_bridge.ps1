param([int]$Port = 8787)
# AHOS Anthropic-compatible bridge with provider rotation.
# Chain: Z.ai (Anthropic passthrough) -> Gemini -> OpenRouter -> LLM7 -> Pollinations -> HF -> Groq.
# Debug: header "x-bridge-provider: zai|gemini|openrouter|llm7|pollinations|hf|groq" forces a provider (ignores cooldown).
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.Web.Extensions
$json = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$json.MaxJsonLength = [int]::MaxValue
$json.RecursionLimit = 1000
$or = [Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY', 'User')
$gq = [Environment]::GetEnvironmentVariable('GROQ_API_KEY', 'User')
$gm = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')
$hf = [Environment]::GetEnvironmentVariable('HF_TOKEN', 'User')
$zai = [Environment]::GetEnvironmentVariable('ZAI_API_KEY', 'User')
$l7 = [Environment]::GetEnvironmentVariable('LLM7_API_KEY', 'User')
$pol = [Environment]::GetEnvironmentVariable('POLLINATIONS_API_KEY', 'User')
$log = Join-Path $PSScriptRoot 'ahos_llm_bridge.log'
function Log([string]$m) { "$(Get-Date -Format s) [$Port] $m" | Out-File -Append -Encoding utf8 $log }

# Slots tried in order. kind: anth = raw Anthropic passthrough, oai = OpenAI chat/completions translation.
$slots = @(
  @{ name = 'zai'; kind = 'anth'; auth = 'xkey'; key = $zai; model = 'glm-4.7-flash'; url = 'https://api.z.ai/api/anthropic/v1/messages' }
  @{ name = 'zai'; kind = 'anth'; auth = 'xkey'; key = $zai; model = 'glm-4.5-flash'; url = 'https://api.z.ai/api/anthropic/v1/messages' }
  @{ name = 'gemini'; kind = 'oai'; key = $gm; model = 'gemini-3.5-flash-lite'; maxTok = 32768; url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions' }
  @{ name = 'gemini'; kind = 'oai'; key = $gm; model = 'gemini-3.8-flash'; maxTok = 32768; url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions' }
  @{ name = 'gemini'; kind = 'oai'; key = $gm; model = 'gemini-flash-latest'; maxTok = 32768; url = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions' }
  @{ name = 'openrouter'; kind = 'anth'; key = $or; model = 'openrouter/free'; url = 'https://openrouter.ai/api/v1/messages'; timeout = 90; dropCool = 600 }
  @{ name = 'llm7'; kind = 'oai'; key = $l7; model = 'GLM-5.3-Flash'; maxTok = 16384; url = 'https://api.llm7.io/v1/chat/completions' }
  @{ name = 'llm7'; kind = 'oai'; key = $l7; model = 'DeepSeek-V4-Flash-0731'; maxTok = 16384; url = 'https://api.llm7.io/v1/chat/completions' }
  @{ name = 'llm7'; kind = 'oai'; key = $l7; model = 'gpt-oss:20b'; maxTok = 16384; url = 'https://api.llm7.io/v1/chat/completions' }
  # Pollinations: cheap non-paid_only models (draw from free daily pollen first)
  @{ name = 'pollinations'; kind = 'oai'; key = $pol; model = 'openai/gpt-6-luna'; maxTok = 16384; url = 'https://gen.pollinations.ai/v1/chat/completions' }
  @{ name = 'pollinations'; kind = 'oai'; key = $pol; model = 'z-ai/glm-5.3-flash'; maxTok = 16384; url = 'https://gen.pollinations.ai/v1/chat/completions' }
  @{ name = 'hf'; kind = 'oai'; key = $hf; model = 'moonshotai/Kimi-K2.7-Code'; maxTok = 16384; url = 'https://router.huggingface.co/v1/chat/completions' }
  @{ name = 'hf'; kind = 'oai'; key = $hf; model = 'zai-org/GLM-4.7'; maxTok = 16384; url = 'https://router.huggingface.co/v1/chat/completions' }
  @{ name = 'hf'; kind = 'oai'; key = $hf; model = 'deepseek-ai/DeepSeek-V3.2'; maxTok = 16384; url = 'https://router.huggingface.co/v1/chat/completions' }
  @{ name = 'groq'; kind = 'oai'; key = $gq; model = 'openai/gpt-oss-20b'; maxTok = 8192; url = 'https://api.groq.com/openai/v1/chat/completions' }
)
$cool = [hashtable]::Synchronized(@{})      # "name|model" -> DateTime until
$sigCache = @{}  # tool_call id -> gemini thought_signature

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()
# Independent /health responder (separate runspace + listener on the /health/ prefix) so health
# answers while the main loop is busy with an upstream call. Falls back to main-loop /health if it fails.
$state = [hashtable]::Synchronized(@{ busy = $false; since = $null })
try {
  $hrs = [runspacefactory]::CreateRunspace(); $hrs.Open()
  $hps = [powershell]::Create(); $hps.Runspace = $hrs
  [void]$hps.AddScript({
    param($port, $cool, $state)
    $hl = New-Object System.Net.HttpListener
    $hl.Prefixes.Add("http://127.0.0.1:$port/health/")
    $hl.Start()
    while ($hl.IsListening) {
      $c = $hl.GetContext()
      try {
        $now = Get-Date; $parts = @()
        foreach ($k in @($cool.Keys)) { $sec = [int]($cool[$k] - $now).TotalSeconds; if ($sec -gt 0) { $parts += ('"' + $k + '":' + $sec) } }
        $busy = if ($state.busy) { [int]((Get-Date) - $state.since).TotalSeconds } else { 0 }
        $t = '{"ok":true,"busy_seconds":' + $busy + ',"cooldowns":{' + ($parts -join ',') + '}}'
        $b = [Text.Encoding]::UTF8.GetBytes($t)
        $c.Response.ContentType = 'application/json'; $c.Response.ContentLength64 = $b.Length
        $c.Response.OutputStream.Write($b, 0, $b.Length); $c.Response.Close()
      } catch { try { $c.Response.Abort() } catch {} }
    }
  }).AddArgument($Port).AddArgument($cool).AddArgument($state)
  [void]$hps.BeginInvoke()
} catch { }
Log "listen-rotate $Port or=$([bool]$or) gemini=$([bool]$gm) zai=$([bool]$zai) llm7=$([bool]$l7) pol=$([bool]$pol) hf=$([bool]$hf) groq=$([bool]$gq)"

function Reply($ctx, [int]$code, [string]$text, [string]$ctype = 'application/json; charset=utf-8') {
  $bytes = [Text.Encoding]::UTF8.GetBytes($text)
  $ctx.Response.StatusCode = $code
  $ctx.Response.ContentType = $ctype
  $ctx.Response.ContentLength64 = $bytes.Length
  $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
  $ctx.Response.Close()
}

function Post-Iwr([string]$url, [hashtable]$headers, [string]$body, [int]$timeout = 180) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $url -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec $timeout
    $t = [Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
    return @{ ok = $true; code = [int]$r.StatusCode; text = $t }
  }
  catch {
    $code = 0; $text = $_.Exception.Message
    if ($_.Exception.Response) {
      $code = [int]$_.Exception.Response.StatusCode
      try {
        $sr = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
        $text = $sr.ReadToEnd(); $sr.Close()
      } catch {}
    }
    return @{ ok = $false; code = $code; text = $text }
  }
}

function Norm($x) {
  if ($null -eq $x) { return $null }
  $x = $x.PSObject.BaseObject
  if ($x -is [string] -or $x -is [ValueType]) { return $x }
  if ($x -is [System.Collections.IDictionary]) {
    $o = New-Object 'System.Collections.Generic.Dictionary[string,object]'
    foreach ($k in @($x.Keys)) { $v = Norm $x[$k]; if ($null -ne $v) { $v = $v.PSObject.BaseObject }; $o.Add([string]$k, $v) }
    return $o
  }
  if ($x -is [System.Collections.IEnumerable]) {
    $l = New-Object 'System.Collections.Generic.List[object]'
    foreach ($i in $x) { $v = Norm $i; if ($null -ne $v) { $v = $v.PSObject.BaseObject }; $l.Add($v) }
    return , $l
  }
  return [string]$x
}
function Ser($x) { $n = Norm $x; return $json.Serialize($n) }
function Head([string]$s, [int]$n = 250) { if ($null -eq $s) { return '' }; if ($s.Length -gt $n) { return $s.Substring(0, $n) } else { return $s } }
function Get-K($d, [string]$k) { if ($d -is [System.Collections.IDictionary] -and ([System.Collections.IDictionary]$d).Contains($k)) { return , $d[$k] } return $null }

function Blocks-Text($c) {
  if ($null -eq $c) { return '' }
  if ($c -is [string]) { return $c }
  $parts = New-Object System.Collections.Generic.List[string]
  foreach ($b in $c) {
    if ($b -is [string]) { $parts.Add($b); continue }
    if ((Get-K $b 'type') -eq 'text') { $parts.Add([string](Get-K $b 'text')) }
  }
  return ($parts -join "`n")
}

function Clean-Schema($s) {
  if ($s -is [System.Collections.IDictionary]) {
    $o = @{}
    foreach ($k in @($s.Keys)) { if ($k -ne '$schema') { $o[$k] = Clean-Schema $s[$k] } }
    return $o
  }
  if ($s -is [System.Collections.IEnumerable] -and -not ($s -is [string])) {
    $l = New-Object System.Collections.ArrayList
    foreach ($x in $s) { [void]$l.Add((Clean-Schema $x)) }
    return , $l
  }
  return $s
}

function To-OpenAI($req, $slot) {
  $msgs = New-Object System.Collections.ArrayList
  $sys = Blocks-Text (Get-K $req 'system')
  if ($sys) { [void]$msgs.Add(@{ role = 'system'; content = $sys }) }
  foreach ($m in (Get-K $req 'messages')) {
    $role = Get-K $m 'role'; $c = Get-K $m 'content'
    if ($c -is [string]) { [void]$msgs.Add(@{ role = $role; content = $c }); continue }
    if ($role -eq 'assistant') {
      $text = New-Object System.Collections.Generic.List[string]
      $calls = New-Object System.Collections.ArrayList
      foreach ($b in $c) {
        $t = Get-K $b 'type'
        if ($t -eq 'text') { $text.Add([string](Get-K $b 'text')) }
        elseif ($t -eq 'tool_use') {
          $id = [string](Get-K $b 'id'); $inp = Get-K $b 'input'; if ($null -eq $inp) { $inp = @{} }
          $call = @{ id = $id; type = 'function'; function = @{ name = (Get-K $b 'name'); arguments = (Ser $inp) } }
          if ($slot.name -eq 'gemini') {
            $sig = $sigCache[$id]; if (-not $sig) { $sig = 'skip_thought_signature_validator' }
            $call.extra_content = @{ google = @{ thought_signature = $sig } }
          }
          [void]$calls.Add($call)
        }
      }
      $am = @{ role = 'assistant'; content = ($text -join "`n") }
      if ($calls.Count -gt 0) { $am.tool_calls = $calls; if (-not $am.content) { $am.content = $null } }
      [void]$msgs.Add($am)
    }
    else {
      $parts = New-Object System.Collections.ArrayList
      foreach ($b in $c) {
        $t = Get-K $b 'type'
        if ($t -eq 'tool_result') {
          $rc = Get-K $b 'content'; $rt = Blocks-Text $rc
          if ((Get-K $b 'is_error') -eq $true) { $rt = "ERROR: $rt" }
          if (-not $rt) { $rt = '(empty)' }
          [void]$msgs.Add(@{ role = 'tool'; tool_call_id = [string](Get-K $b 'tool_use_id'); content = $rt })
        }
        elseif ($t -eq 'text') { [void]$parts.Add(@{ type = 'text'; text = [string](Get-K $b 'text') }) }
        elseif ($t -eq 'image') {
          $src = Get-K $b 'source'
          if ((Get-K $src 'type') -eq 'base64') { [void]$parts.Add(@{ type = 'image_url'; image_url = @{ url = "data:$(Get-K $src 'media_type');base64,$(Get-K $src 'data')" } }) }
          elseif (Get-K $src 'url') { [void]$parts.Add(@{ type = 'image_url'; image_url = @{ url = (Get-K $src 'url') } }) }
        }
      }
      if ($parts.Count -gt 0) {
        if ($slot.name -eq 'groq') { [void]$msgs.Add(@{ role = 'user'; content = (($parts | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }) -join "`n") }) }
        else { [void]$msgs.Add(@{ role = 'user'; content = $parts }) }
      }
    }
  }
  $o = @{ model = $slot.model; messages = $msgs; stream = $false }
  $mt = Get-K $req 'max_tokens'; if (-not $mt) { $mt = 4096 }
  $o.max_tokens = [Math]::Min([int]$mt, [int]$slot.maxTok)
  foreach ($k in 'temperature', 'top_p') { $v = Get-K $req $k; if ($null -ne $v) { $o[$k] = $v } }
  $ss = Get-K $req 'stop_sequences'; if ($ss) { $o.stop = $ss }
  $tools = New-Object System.Collections.ArrayList
  foreach ($t in (Get-K $req 'tools')) {
    $sch = Get-K $t 'input_schema'; if ($null -eq $sch) { continue }
    $fn = @{ name = (Get-K $t 'name'); parameters = (Clean-Schema $sch) }
    $d = Get-K $t 'description'; if ($d) { $fn.description = $d }
    [void]$tools.Add(@{ type = 'function'; function = $fn })
  }
  if ($tools.Count -gt 0) {
    $o.tools = $tools
    $tc = Get-K $req 'tool_choice'
    switch ((Get-K $tc 'type')) {
      'any' { $o.tool_choice = 'required' }
      'tool' { $o.tool_choice = @{ type = 'function'; function = @{ name = (Get-K $tc 'name') } } }
      'none' { $o.tool_choice = 'none' }
      default { $o.tool_choice = 'auto' }
    }
  }
  return $o
}

function From-OpenAI($resp, $slot) {
  $ch = (Get-K $resp 'choices')[0]; $m = Get-K $ch 'message'
  $content = New-Object System.Collections.ArrayList
  $txt = [string](Get-K $m 'content')
  if ($txt) { [void]$content.Add(@{ type = 'text'; text = $txt }) }
  foreach ($tc in (Get-K $m 'tool_calls')) {
    $id = [string](Get-K $tc 'id'); if (-not $id) { $id = 'toolu_' + [guid]::NewGuid().ToString('N').Substring(0, 24) }
    $id = $id -replace '[^a-zA-Z0-9_-]', '_'
    $f = Get-K $tc 'function'; $fa = [string](Get-K $f 'arguments'); $inp = @{}
    if ($fa) { try { $inp = $json.DeserializeObject($fa) } catch { $inp = @{} } }
    if (-not ($inp -is [System.Collections.IDictionary])) { $inp = @{} }
    $sig = Get-K (Get-K (Get-K $tc 'extra_content') 'google') 'thought_signature'
    if ($sig) { $sigCache[$id] = $sig }
    [void]$content.Add(@{ type = 'tool_use'; id = $id; name = (Get-K $f 'name'); input = $inp })
  }
  if ($content.Count -eq 0) { [void]$content.Add(@{ type = 'text'; text = '' }) }
  $fr = Get-K $ch 'finish_reason'
  $stop = switch ($fr) { 'length' { 'max_tokens' } 'tool_calls' { 'tool_use' } default { 'end_turn' } }
  if (($content | Where-Object { $_.type -eq 'tool_use' }).Count -gt 0) { $stop = 'tool_use' }
  $u = Get-K $resp 'usage'
  $id = [string](Get-K $resp 'id'); if (-not $id) { $id = [guid]::NewGuid().ToString('N') }
  return @{
    id = 'msg_' + ($id -replace '[^a-zA-Z0-9_-]', ''); type = 'message'; role = 'assistant'
    model = "$($slot.name)/$($slot.model)"; content = $content; stop_reason = $stop; stop_sequence = $null
    usage = @{ input_tokens = [int](Get-K $u 'prompt_tokens'); output_tokens = [int](Get-K $u 'completion_tokens') }
  }
}

function To-Sse($msg) {
  $sb = New-Object System.Text.StringBuilder
  function Ev($t, $d) { [void]$sb.Append("event: $t`ndata: " + (Ser $d) + "`n`n") }
  $start = @{ id = $msg.id; type = 'message'; role = 'assistant'; model = $msg.model; content = @(); stop_reason = $null; stop_sequence = $null; usage = @{ input_tokens = $msg.usage.input_tokens; output_tokens = 1 } }
  Ev 'message_start' @{ type = 'message_start'; message = $start }
  $i = 0
  foreach ($b in $msg.content) {
    if ($b.type -eq 'text') {
      Ev 'content_block_start' @{ type = 'content_block_start'; index = $i; content_block = @{ type = 'text'; text = '' } }
      Ev 'content_block_delta' @{ type = 'content_block_delta'; index = $i; delta = @{ type = 'text_delta'; text = $b.text } }
    }
    else {
      Ev 'content_block_start' @{ type = 'content_block_start'; index = $i; content_block = @{ type = 'tool_use'; id = $b.id; name = $b.name; input = @{} } }
      Ev 'content_block_delta' @{ type = 'content_block_delta'; index = $i; delta = @{ type = 'input_json_delta'; partial_json = (Ser $b.input) } }
    }
    Ev 'content_block_stop' @{ type = 'content_block_stop'; index = $i }
    $i++
  }
  Ev 'message_delta' @{ type = 'message_delta'; delta = @{ stop_reason = $msg.stop_reason; stop_sequence = $null }; usage = @{ output_tokens = $msg.usage.output_tokens } }
  Ev 'message_stop' @{ type = 'message_stop' }
  return $sb.ToString()
}

function Cool-For([int]$code) {
  if ($code -eq 402) { return 21600 } if ($code -eq 429) { return 90 } if ($code -eq 401 -or $code -eq 403) { return 900 }
  if ($code -ge 500 -or $code -eq 0) { return 45 } if ($code -eq 404) { return 3600 }
  return 0
}

while ($listener.IsListening) {
  $ctx = $listener.GetContext()
  $path = $ctx.Request.Url.AbsolutePath.TrimEnd('/')
  $method = $ctx.Request.HttpMethod
  try {
    if ($method -eq 'GET' -and ($path -eq '' -or $path -eq '/health')) {
      $now = Get-Date; $cd = @{}
      foreach ($k in @($cool.Keys)) { $s = [int]($cool[$k] - $now).TotalSeconds; if ($s -gt 0) { $cd[$k] = $s } }
      Reply $ctx 200 ((Ser @{ ok = $true; cooldowns = $cd })); continue
    }
    if ($method -eq 'GET' -and $path -eq '/v1/models') { Reply $ctx 200 '{"data":[{"id":"openrouter/free","object":"model"}]}'; continue }
    if ($method -eq 'POST' -and $path -like '*count_tokens*') { Reply $ctx 200 '{"input_tokens":1000}'; continue }
    if ($method -eq 'POST' -and ($path -eq '/v1/messages' -or $path -eq '/messages')) {
      $reader = New-Object IO.StreamReader($ctx.Request.InputStream, [Text.Encoding]::UTF8)
      $body = $reader.ReadToEnd(); $reader.Close()
      $force = $ctx.Request.Headers['x-bridge-provider']; $fmodel = $ctx.Request.Headers['x-bridge-model']
      $req = $null; try { $req = $json.DeserializeObject($body) } catch {}
      $stream = ((Get-K $req 'stream') -eq $true)
      Log ("REQ bytes=$($body.Length) stream=$stream force=$force")
      $state.busy = $true; $state.since = Get-Date
      $last = ''; $done = $false
      foreach ($slot in $slots) {
        if (-not $slot.key) { continue }
        if ($force -and $slot.name -ne $force) { continue }
        if ($fmodel -and $slot.model -ne $fmodel) { continue }
        $ck = "$($slot.name)|$($slot.model)"
        if (-not $force -and $cool.ContainsKey($ck) -and $cool[$ck] -gt (Get-Date)) { continue }
        if ($slot.kind -eq 'anth') {
          $b2 = [regex]::Replace($body, '"model"\s*:\s*"[^"]*"', '"model":"' + $slot.model + '"', 1)
          $ah = if ($slot.auth -eq 'xkey') { @{ 'x-api-key' = $slot.key; 'anthropic-version' = '2023-06-01' } } else { @{ Authorization = "Bearer $($slot.key)"; 'anthropic-version' = '2023-06-01'; 'HTTP-Referer' = 'https://github.com/anthropics/claude-code'; 'X-Title' = 'AHOS-Claude-Bridge' } }
          $to = if ($slot.timeout) { [int]$slot.timeout } else { 180 }
          $r = Post-Iwr $slot.url $ah $b2 $to
          Log "$ck code=$($r.code) ok=$($r.ok) head=$(Head $r.text)"
          if ($r.ok -and $r.text -notmatch '^\s*\{\s*"error"') {
            $ct = if ($r.text.TrimStart().StartsWith('event:') -or $r.text.TrimStart().StartsWith('data:') -or $r.text.TrimStart().StartsWith(':')) { 'text/event-stream; charset=utf-8' } else { 'application/json; charset=utf-8' }
            Reply $ctx 200 $r.text $ct; $done = $true; break
          }
        }
        else {
          if ($null -eq $req) { continue }
          $oreq = To-OpenAI $req $slot
          $r = Post-Iwr $slot.url @{ Authorization = "Bearer $($slot.key)" } ((Ser $oreq)) 100
          Log "$ck code=$($r.code) ok=$($r.ok) head=$(Head $r.text 200)"
          if ($r.ok) {
            $o = $null; try { $o = $json.DeserializeObject($r.text) } catch {}
            if ((Get-K $o 'choices')) {
              $am = From-OpenAI $o $slot
              if ($stream) { Reply $ctx 200 (To-Sse $am) 'text/event-stream; charset=utf-8' }
              else { Reply $ctx 200 ((Ser $am)) }
              $done = $true; break
            }
            $r.code = 502
          }
        }
        $last = "$ck $($r.code) $(Head $r.text 200)"
        if ($r.text -match '"1113"|Insufficient balance|no remaining credits') { $r.code = 402 }
        $secs = Cool-For $r.code
        if ($r.ok) { $secs = 30 }
        if ($r.code -eq 0 -and $slot.dropCool) { $secs = [int]$slot.dropCool }
        if ($secs -gt 0 -and -not $force) { $cool[$ck] = (Get-Date).AddSeconds($secs); Log "COOL $ck ${secs}s" }
        if ($r.code -eq 402 -and -not $force) { foreach ($s2 in $slots) { if ($s2.name -eq $slot.name) { $cool["$($s2.name)|$($s2.model)"] = (Get-Date).AddSeconds($secs) } }; Log "COOL all $($slot.name) (402 no credits)" }
      }
      $state.busy = $false
      if (-not $done) {
        Reply $ctx 529 ((Ser @{ type = 'error'; error = @{ type = 'overloaded_error'; message = "all providers failed/cooling: $last" } }))
      }
      continue
    }
    Reply $ctx 404 '{"error":"not found"}'
  }
  catch {
    $em = $_.Exception.Message
    $state.busy = $false
    Log "ERR $em"
    try { Reply $ctx 500 ((Ser @{ type = 'error'; error = @{ type = 'api_error'; message = $em } })) } catch {}
  }
}
