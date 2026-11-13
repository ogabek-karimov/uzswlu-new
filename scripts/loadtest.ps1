<#
  Yuk sinovi: ko'p parallel so'rov yuborib, necha soniya ketganini, tezlikni va kesh holatini (X-Cache) ko'rsatadi.
  PowerShell 7+ kerak (Windows'dagi eski "powershell" emas, `pwsh`):  winget install Microsoft.PowerShell

  Misollar (loyiha papkasidan):
    pwsh scripts/loadtest.ps1                                   # 10 000 so'rov, 100 parallel, bosh sahifa
    pwsh scripts/loadtest.ps1 -Total 10000 -Concurrency 200
    pwsh scripts/loadtest.ps1 -Urls http://localhost:8080/,http://localhost:8080/ru,http://localhost:8080/en,http://localhost:8080/zh
    pwsh scripts/loadtest.ps1 -Warmup                           # avval keshni isitadi (faqat HIT ni o'lchash uchun)

  Eslatma: bu skript kesh va xatolarni TEKSHIRISH uchun (PowerShell o'zi sekin: ~150–250 so'rov/s dan oshmaydi). Serverning haqiqiy
  tezligini o'lchash uchun docs/10-server.md dagi `ab` (Docker) buyrug'idan foydalaning.
  Faqat o'z serveringizga yuboring.
#>
param(
  [string[]]$Urls = @('http://localhost:8080/'),
  [int]$Total = 10000,
  [int]$Concurrency = 100,
  [int]$TimeoutSec = 30,
  [switch]$Warmup
)

# `pwsh scripts/loadtest.ps1 -Urls a,b` buyrug'ida ro'yxat bitta qator bo'lib keladi — vergul bo'yicha ajratamiz
$Urls = @($Urls | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

if ($PSVersionTable.PSVersion.Major -lt 7) {
  Write-Error 'PowerShell 7+ kerak. O''rnatish: winget install Microsoft.PowerShell, keyin `pwsh scripts/loadtest.ps1` bilan ishga tushiring.'
  exit 1
}

$handler = [System.Net.Http.SocketsHttpHandler]::new()
$handler.MaxConnectionsPerServer = $Concurrency
$handler.AutomaticDecompression = [System.Net.DecompressionMethods]::All
$client = [System.Net.Http.HttpClient]::new($handler)
$client.Timeout = [TimeSpan]::FromSeconds($TimeoutSec)

if ($Warmup) {
  foreach ($u in $Urls) { try { $null = $client.GetAsync($u).GetAwaiter().GetResult() } catch { } }
  Write-Host 'Kesh isitildi.'
}

Write-Host ("{0} ta so'rov, {1} ta parallel, manzillar: {2}" -f $Total, $Concurrency, ($Urls -join ', '))
$sw = [System.Diagnostics.Stopwatch]::StartNew()

$results = 1..$Total | ForEach-Object -ThrottleLimit $Concurrency -Parallel {
  $c = $using:client
  $urls = $using:Urls
  $url = $urls[$_ % $urls.Count]
  $t = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $r = $c.GetAsync($url).GetAwaiter().GetResult()
    $cache = ''
    $v = $null
    if ($r.Headers.TryGetValues('X-Cache', [ref]$v)) { $cache = @($v)[0] }
    $status = [int]$r.StatusCode
    $r.Dispose()
    [pscustomobject]@{ Status = $status; Cache = $cache; Ms = $t.Elapsed.TotalMilliseconds }
  }
  catch {
    [pscustomobject]@{ Status = 0; Cache = ''; Ms = $t.Elapsed.TotalMilliseconds }
  }
}

$sw.Stop()
$secs = $sw.Elapsed.TotalSeconds
$n = @($results).Count
$ms = @($results | ForEach-Object { $_.Ms } | Sort-Object)

function Pct([double]$p) { if ($n -eq 0) { return 0 } ; return [math]::Round($ms[[math]::Min($n - 1, [int][math]::Floor($n * $p))], 1) }

Write-Host ''
Write-Host '=== NATIJA ==='
Write-Host ("Jami vaqt:        {0:N2} soniya" -f $secs)
Write-Host ("Tezlik:           {0:N0} so'rov/soniya" -f ($n / $secs))
Write-Host ("Yuborildi:        {0}" -f $n)
Write-Host ("Kechikish (ms):   o'rtacha {0:N1} | p50 {1} | p95 {2} | p99 {3} | eng sekin {4}" -f ($ms | Measure-Object -Average).Average, (Pct 0.5), (Pct 0.95), (Pct 0.99), (Pct 1.0))
Write-Host ''
Write-Host 'HTTP holatlari (0 = ulanish xatosi yoki vaqt tugadi):'
$results | Group-Object Status | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
Write-Host ''
Write-Host 'Kesh (X-Cache):'
$results | Group-Object { if ($_.Cache) { $_.Cache } else { '(yo''q)' } } | Sort-Object Count -Descending | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
$bad = @($results | Where-Object { $_.Status -ne 200 }).Count
Write-Host ''
if ($bad -eq 0) { Write-Host "Xatosiz: barcha so'rov 200 qaytardi." } else { Write-Host "DIQQAT: $bad ta so'rov 200 emas." }
