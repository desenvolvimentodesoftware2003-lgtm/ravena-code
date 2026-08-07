param(
    [int]$Port = 8765,
    [float]$DelayMin = 300.0,
    [float]$DelayMax = 900.0,
    [switch]$Verbose,
    [switch]$NoTor,
    [string]$SocksHost = "127.0.0.1",
    [int]$SocksPort = 9050,
    [int]$ControlPort = 9051
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

python -c "import sys; sys.path.insert(0, '$ProjectDir'); from desktop.cli import main; main()" -- `
    --port $Port `
    --delay-min $DelayMin `
    --delay-max $DelayMax `
    $(if ($Verbose) { "--verbose" }) `
    --socks-host $SocksHost `
    --socks-port $SocksPort `
    --control-port $ControlPort
