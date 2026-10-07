param(
    [string]$SourceContainer = 'tawos-feasibility',
    [string]$SourceRootPassword
)

$ErrorActionPreference = 'Stop'

function Get-ProjectSetting([string]$Name, [string]$DefaultValue) {
    if (Test-Path -LiteralPath '.env') {
        foreach ($line in Get-Content -LiteralPath '.env') {
            if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.*?)\s*$") {
                return $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }
    return $DefaultValue
}

$postgresUser = Get-ProjectSetting 'POSTGRES_USER' 'tawos'
$postgresDatabase = Get-ProjectSetting 'POSTGRES_DB' 'tawos'
$postgresContainer = (docker compose ps -q db).Trim()
if (-not $postgresContainer) { throw 'PostgreSQL is not running.' }

$tables = @(
    @{ Source = 'Project'; Target = 'project' },
    @{ Source = 'Sprint'; Target = 'sprint' },
    @{ Source = 'Issue'; Target = 'issue' },
    @{ Source = 'Change_Log'; Target = 'change_log' },
    @{ Source = 'Comment'; Target = 'comment' },
    @{ Source = 'Repository'; Target = 'repository' },
    @{ Source = 'User'; Target = 'user' },
    @{ Source = 'Version'; Target = 'version' },
    @{ Source = 'Component'; Target = 'component' },
    @{ Source = 'Affected_Version'; Target = 'affected_version' },
    @{ Source = 'Fix_Version'; Target = 'fix_version' },
    @{ Source = 'Issue_Component'; Target = 'issue_component' },
    @{ Source = 'Issue_Link'; Target = 'issue_link' }
)
$mysqlAuth = @('-uroot')
if ($PSBoundParameters.ContainsKey('SourceRootPassword')) {
    $mysqlRootPassword = $SourceRootPassword
} elseif ($SourceContainer -eq 'tawos-feasibility') {
    $mysqlRootPassword = ''
} else {
    $mysqlRootPassword = Get-ProjectSetting 'MYSQL_ROOT_PASSWORD' 'tawos_mysql_local'
}
if ($mysqlRootPassword) { $mysqlAuth += "-p$mysqlRootPassword" }

$differences = [System.Collections.Generic.List[string]]::new()
foreach ($table in $tables) {
    $mysqlIdentifier = [string][char]96 + $table.Source + [string][char]96
    $sourceSql = "SELECT COUNT(*) FROM TAWOS.$mysqlIdentifier"
    $targetSql = "SELECT COUNT(*) FROM tawos_raw.`"$($table.Target)`""
    $sourceResult = docker exec $SourceContainer mysql @mysqlAuth -Nse $sourceSql
    if ($LASTEXITCODE -ne 0) { throw "Could not count source rows in $($table.Source)." }
    $sourceCount = $sourceResult.Trim()
    $targetCount = (docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc $targetSql).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Could not count target rows in $($table.Target)." }

    if ($sourceCount -ne $targetCount) {
        $differences.Add("$($table.Source): MySQL=$sourceCount PostgreSQL=$targetCount")
    }
    Write-Output ("{0,-20} {1,12} rows" -f $table.Target, $targetCount)
}

if ($differences.Count -gt 0) {
    throw "Row-count mismatches detected:`n$($differences -join "`n")"
}

Write-Output "PASS: row counts match for all $($tables.Count) TAWOS tables."
