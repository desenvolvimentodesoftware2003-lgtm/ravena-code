# VERIFICAR_PENDRIVE.ps1 - Conferencia pos-gravacao RV10 (requer admin)
# Le setores fisicos do SanDisk (Disco 1) e compara com o ISO original:
#   1) MBR (setor 0) + assinatura 55AA
#   2) Bloco do boot isohybrid (offset 0, 1MB) - hash vs ISO
#   3) Bloco do squashfs (offset 8MB, 4MB) - hash vs ISO
#   4) Final do disco (ultimos 2MB) - hash vs ISO
$ErrorActionPreference = "Stop"

$ISO = "C:\Users\DELL\OneDrive\Documentos\RAVENA-RV7\ravena-remaster-RV10.iso"
$DISK = 1
$DEV = "\\.\PHYSICALDRIVE$DISK"
$OUTLOG = "C:\Users\DELL\OneDrive\Documentos\RAVENA-RV7\VERIFICAR_PENDRIVE_resultado.txt"
Remove-Item $OUTLOG -ErrorAction SilentlyContinue

function Log($msg) {
    $ts = "[$(Get-Date -Format HH:mm:ss)] $msg"
    Write-Host $ts
    Add-Content -Path $OUTLOG -Value $ts
}

function Read-Raw([long]$offset, [int]$len, $fs) {
    $buf = New-Object byte[] $len
    $fs.Seek($offset, [System.IO.SeekOrigin]::Begin) | Out-Null
    $read = $fs.Read($buf, 0, $len)
    if ($read -ne $len) { throw "Leitura curta em offset $offset ($read/$len)" }
    return $buf
}

function Hash-Buf($buf) {
    $sha = [System.Security.Cryptography.SHA512]::Create()
    return [BitConverter]::ToString($sha.ComputeHash($buf)).Replace("-","").ToLower()
}

# pre-condicoes
if (-not (Test-Path $ISO)) { Log "ERRO: ISO nao encontrado"; exit 1 }
$d = Get-Disk -Number $DISK
if ($d.FriendlyName -notmatch "SanDisk|Cruzer") { Log "ERRO: Disco $DISK nao e SanDisk"; exit 1 }
$isoLen = (Get-Item $ISO).Length

Log "=== VERIFICACAO POS-GRAVACAO RV10 ==="
Log "Alvo: $($d.FriendlyName) / Disco $DISK / ISO $isoLen bytes"

$fs = [System.IO.File]::Open($DEV, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
try {
    # 1) MBR
    $mbr = Read-Raw 0 512 $fs
    $sig = [BitConverter]::ToString($mbr, 510, 2).Replace("-","")
    Log "MBR assinatura 55AA: $sig"
    if ($sig -ne "55AA") { Log "ERRO: MBR invalido"; exit 1 }

    # 2) boot isohybrid (1MB inicial)
    $b1 = Read-Raw 0 1048576 $fs
    $h1 = Hash-Buf $b1
    $isoFs = [System.IO.File]::Open($ISO, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $b1i = Read-Raw 0 1048576 $isoFs
        $h1i = Hash-Buf $b1i
    } finally { $isoFs.Close() }
    $ok1 = ($h1 -eq $h1i)
    Log "Boot 1MB pendrive=$h1"
    Log "        iso     =$h1i"
    if ($ok1) { Log "BOOT OK - confere com o ISO" } else { Log "ERRO: boot diverge do ISO!" }

    # 3) squashfs (8MB -> 12MB)
    $b2 = Read-Raw 8388608 4194304 $fs
    $h2 = Hash-Buf $b2
    $isoFs = [System.IO.File]::Open($ISO, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $b2i = Read-Raw 8388608 4194304 $isoFs
        $h2i = Hash-Buf $b2i
    } finally { $isoFs.Close() }
    $ok2 = ($h2 -eq $h2i)
    Log "Squashfs 4MB@8MB pendrive=$h2"
    Log "               iso    =$h2i"
    if ($ok2) { Log "SQUASHFS OK - confere com o ISO" } else { Log "ERRO: squashfs diverge do ISO!" }

    # 4) final do disco (ultimos 2MB do ISO)
    $last = $isoLen - 2097152
    $b3 = Read-Raw $last 2097152 $fs
    $h3 = Hash-Buf $b3
    $isoFs = [System.IO.File]::Open($ISO, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    try {
        $b3i = Read-Raw $last 2097152 $isoFs
        $h3i = Hash-Buf $b3i
    } finally { $isoFs.Close() }
    $ok3 = ($h3 -eq $h3i)
    Log "Final 2MB pendrive=$h3"
    Log "         iso    =$h3i"
    if ($ok3) { Log "FINAL OK - confere com o ISO" } else { Log "ERRO: final diverge do ISO!" }

    $total = @($ok1, $ok2, $ok3) | Where-Object { $_ }
    Log ""
    if ($total.Count -eq 3) {
        Log "RESULTADO: GRAVACAO INTEGRA - todos os blocos conferem com o ISO."
    } else {
        Log "RESULTADO: INCONSISTENTE ($($total.Count)/3 blocos OK) - refazer a gravacao."
    }
} finally { $fs.Close() }
Log "FIM"
