# GRAVAR_RV10.ps1 - Gravação final do Ravena RV10 no pendrive SanDisk (Disco 1)
# Controle corrigido: hash ISO antes -> Rufus DD -> conferência pós-gravação
# Executar:  powershell -ExecutionPolicy Bypass -File GRAVAR_RV10.ps1
$ErrorActionPreference = "Stop"

$ISO  = "C:\Users\DELL\OneDrive\Documentos\RAVENA-RV7\ravena-remaster-RV10.iso"
$SHA  = "3b99d52dfdce205ad2992723714189e3579fbb0992df5a709d5cdf8e915813a636fe80297aa8bbd19395f5b5f008564cda69750d1a4c358c877aea234c9f7d10"
$RUFUS = "C:\Users\DELL\OneDrive\Documentos\rufus.exe"
$DISK = 1

function Write-Step($msg) { Write-Host ""; Write-Host "=== $msg ===" -ForegroundColor Cyan }

Write-Step "GRAVACAO FINAL RAVENA RV10 - CONTROLE"
Write-Host "Pendrive alvo: Disco $DISK (SanDisk Cruzer Blade, ~114.6GB)" -ForegroundColor Yellow

# 0. Sanidade: ISO existe
if (-not (Test-Path $ISO)) { Write-Host "ERRO: ISO nao encontrado em $ISO" -ForegroundColor Red; exit 1 }
if (-not (Test-Path $RUFUS)) { Write-Host "ERRO: rufus.exe nao encontrado" -ForegroundColor Red; exit 1 }

# 1. Confirmar que o Disco 1 e mesmo o SanDisk
$d = Get-Disk -Number $DISK
if ($d.FriendlyName -notmatch "SanDisk|Cruzer") { Write-Host "ERRO: Disco $DISK NAO e SanDisk! ($($d.FriendlyName))" -ForegroundColor Red; exit 1 }

# 2. Hash do ISO ANTES de gravar
Write-Step "1/4 HASH DO ISO (antes)"
$h = (Get-FileHash -Algorithm SHA512 $ISO).Hash.ToLower()
if ($h -ne $SHA) {
    Write-Host "ERRO: hash NAO confere!" -ForegroundColor Red
    Write-Host "  esperado: $SHA" -ForegroundColor Red
    Write-Host "  obtido:   $h" -ForegroundColor Red
    exit 1
}
Write-Host "Hash OK: $h" -ForegroundColor Green

# 3. Confirmação final (anti-erro: apaga o pendrive inteiro)
Write-Step "2/4 CONFIRMACAO"
Write-Host "ATENCAO: todo o conteudo do Disco $DISK ($($d.FriendlyName)) sera APAGADO!" -ForegroundColor Red
$resp = Read-Host "Digite SIM para confirmar a gravacao (ou ENTER para cancelar)"
if ($resp -ne "SIM") { Write-Host "Cancelado."; exit 0 }

# 4. Rufus DD
Write-Step "3/4 GRAVANDO COM RUFUS (modo DD)"
Write-Host "Rufus vai abrir o dialogo de UAC - confirme para prosseguir." -ForegroundColor Yellow
Start-Process $RUFUS -ArgumentList "-i", "`"$ISO`"", "-d", "$DISK", "-a", "1" -Verb RunAs -Wait
Write-Host "Rufus terminou." -ForegroundColor Green

# 5. Conferência pós-gravação
Write-Step "4/4 CONFERENCIA POS-GRAVACAO"
Start-Sleep -Seconds 3
$disk = Get-Disk -Number $DISK
Write-Host "Disco: $($disk.FriendlyName) / $([math]::Round($disk.Size/1GB,2))GB / $($disk.PartitionStyle)"
$isoSize = (Get-Item $ISO).Length
Write-Host "Tamanho ISO: $isoSize bytes"
$parts = Get-Partition -DiskNumber $DISK | Select-Object -First 1
if ($parts) {
    $end = $parts.Offset + $parts.Size
    Write-Host "Particao 1: offset=$($parts.Offset) size=$($parts.Size) fim=$end"
    $diff = [math]::Abs($end - $isoSize)
    $tolerancia = 100MB
    if ($diff -le $tolerancia) {
        Write-Host "CONFERENCIA OK: fim da particao (~=$end) ≈ tamanho do ISO." -ForegroundColor Green
    } else {
        Write-Host "AVISO: fim da particao difere do ISO por $diff bytes - verifique." -ForegroundColor Yellow
    }
} else {
    Write-Host "AVISO: nenhuma particao enumerada (modo DD isohybrid nao cria particoes visiveis - normal em alguns casos)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "GRAVACAO CONCLUIDA. Proximo passo: bootar o pendrive no PC real (F12 > SanDisk)." -ForegroundColor Green
