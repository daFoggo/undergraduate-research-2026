param(
    [string]$SourceContainer = 'tawos-feasibility',
    [string]$SourceRootPassword,
    [switch]$SkipTargetEmptyCheck
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
$postgresPassword = Get-ProjectSetting 'POSTGRES_PASSWORD' 'tawos_local_dev'
$postgresDatabase = Get-ProjectSetting 'POSTGRES_DB' 'tawos'
if ($PSBoundParameters.ContainsKey('SourceRootPassword')) {
    $mysqlRootPassword = $SourceRootPassword
} elseif ($SourceContainer -eq 'tawos-feasibility') {
    $mysqlRootPassword = ''
} else {
    $mysqlRootPassword = Get-ProjectSetting 'MYSQL_ROOT_PASSWORD' 'tawos_mysql_local'
}
$mysqlMigrationPassword = 'tawos_local_migration'
$postgresContainer = (docker compose ps -q db).Trim()

if (-not $postgresContainer) {
    throw 'PostgreSQL is not running. Start it with: docker compose up -d db'
}

$sourceState = docker inspect --format '{{.State.Running}}' $SourceContainer 2>$null
if ($LASTEXITCODE -ne 0 -or $sourceState -ne 'true') {
    throw "Source MySQL container '$SourceContainer' is not running."
}

$mysqlAuth = @('-uroot')
if ($mysqlRootPassword) { $mysqlAuth += "-p$mysqlRootPassword" }
$sourceIssueCount = [int](docker exec $SourceContainer mysql @mysqlAuth -Nse 'SELECT COUNT(*) FROM TAWOS.Issue')
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect source Issue table; has the SQL dump finished importing?' }
$sourceProjectCount = [int](docker exec $SourceContainer mysql @mysqlAuth -Nse 'SELECT COUNT(*) FROM TAWOS.Project')
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect source Project table; has the SQL dump finished importing?' }
if ($sourceIssueCount -ne 458232 -or $sourceProjectCount -ne 39) {
    throw "Source import is incomplete or not TAWOS v1.1: found $sourceIssueCount issues and $sourceProjectCount projects; expected 458232 and 39."
}

$network = (docker inspect --format '{{range $name, $config := .NetworkSettings.Networks}}{{$name}}{{end}}' $postgresContainer).Trim()
if (-not $network) {
    throw 'Could not determine the Compose network for PostgreSQL.'
}

$sourceNetworks = (docker inspect --format '{{range $name, $config := .NetworkSettings.Networks}}{{$name}} {{end}}' $SourceContainer).Trim()
if ($sourceNetworks -notmatch [regex]::Escape($network)) {
    docker network connect $network $SourceContainer
    if ($LASTEXITCODE -ne 0) { throw 'Could not connect the MySQL source to the project network.' }
}

if (-not $SkipTargetEmptyCheck) {
    $tableCountSql = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name <> 'alembic_version'"
    $existingTables = [int](docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc $tableCountSql)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the PostgreSQL target.' }
    if ($existingTables -gt 0) {
        throw "Target database already has $existingTables public tables. Migration stopped to avoid overwriting data."
    }
    $rawSchemaCount = [int](docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc "SELECT count(*) FROM information_schema.schemata WHERE schema_name IN ('tawos', 'tawos_raw')")
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the PostgreSQL TAWOS schema.' }
    if ($rawSchemaCount -gt 0) { throw 'A tawos/tawos_raw schema already exists. Migration stopped to avoid overwriting data.' }
}

$grantSql = "CREATE USER IF NOT EXISTS 'tawos_migrator'@'%' IDENTIFIED WITH mysql_native_password BY '$mysqlMigrationPassword'; GRANT SELECT, SHOW VIEW, LOCK TABLES ON TAWOS.* TO 'tawos_migrator'@'%'; FLUSH PRIVILEGES;"
docker exec $SourceContainer mysql @mysqlAuth -e $grantSql
if ($LASTEXITCODE -ne 0) { throw 'Could not create the read-only migration account in MySQL.' }

$sourcePasswordEscaped = [Uri]::EscapeDataString($mysqlMigrationPassword)
$targetPasswordEscaped = [Uri]::EscapeDataString($postgresPassword)
$sourceUrl = "mysql://tawos_migrator:$sourcePasswordEscaped@$SourceContainer`:3306/TAWOS"
$targetUrl = "postgresql://$postgresUser`:$targetPasswordEscaped@db`:5432/$postgresDatabase"

Write-Output 'Starting one-time TAWOS v1.1 migration with pgloader.'
Write-Output "Source container: $SourceContainer"
Write-Output "Destination database: $postgresDatabase"
$loaderOutput = docker run --rm --network $network ghcr.io/dimitri/pgloader@sha256:a1d4a78e78a64e46cd3fc7dfc57d24eb91ffb1a5520f2b1f55631815e3658d6e pgloader --verbose --on-error-stop --dynamic-space-size 8192 --with 'workers = 2' --with 'concurrency = 1' --with 'prefetch rows = 500' --with 'batch rows = 500' --with 'batch size = 8 MB' $sourceUrl $targetUrl 2>&1
$loaderExitCode = $LASTEXITCODE
$loaderOutput | ForEach-Object { Write-Output $_ }
if ($loaderExitCode -ne 0 -or (($loaderOutput -join "`n") -match '(?im)^\s*ERROR\b|MYSQL-UNSUPPORTED-AUTHENTICATION|\bFATAL\b')) {
    throw 'pgloader migration failed; inspect its output before retrying.'
}

$renameSchemaResult = docker exec $postgresContainer psql -v ON_ERROR_STOP=1 -U $postgresUser -d $postgresDatabase -c 'ALTER SCHEMA tawos RENAME TO tawos_raw'
if ($LASTEXITCODE -ne 0) { throw 'Data load completed, but renaming the raw schema tawos -> tawos_raw failed.' }

$zipPath = 'data/raw/TAWOS-v1.1.sql.zip'
if (-not (Test-Path -LiteralPath $zipPath)) { throw "Could not find dataset archive at $zipPath for the import manifest." }
$sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash
$issueCount = [int](docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc 'SELECT COUNT(*) FROM tawos_raw.issue')
if ($LASTEXITCODE -ne 0) { throw 'Migration did not create tawos_raw.issue; import manifest not written.' }
$projectCount = [int](docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc 'SELECT COUNT(*) FROM tawos_raw.project')
if ($LASTEXITCODE -ne 0) { throw 'Migration did not create tawos_raw.project; import manifest not written.' }
$sprintCount = [int](docker exec $postgresContainer psql -U $postgresUser -d $postgresDatabase -Atc 'SELECT COUNT(*) FROM tawos_raw.sprint')
if ($LASTEXITCODE -ne 0) { throw 'Migration did not create tawos_raw.sprint; import manifest not written.' }
if ($issueCount -ne $sourceIssueCount -or $projectCount -ne $sourceProjectCount -or $sprintCount -lt 1) {
    throw "Migrated core table counts do not match source: issues $issueCount/$sourceIssueCount, projects $projectCount/$sourceProjectCount, sprints $sprintCount."
}
$manifestSql = "INSERT INTO research.dataset_imports (dataset_name, dataset_version, source_url, source_sha256, issue_count, project_count, sprint_count) VALUES ('TAWOS', '1.1', 'https://doi.org/10.5522/04/21308124.v1', '$sourceHash', $issueCount, $projectCount, $sprintCount)"
docker exec $postgresContainer psql -v ON_ERROR_STOP=1 -U $postgresUser -d $postgresDatabase -c $manifestSql
if ($LASTEXITCODE -ne 0) { throw 'Data moved, but writing the dataset import manifest failed.' }

Write-Output "Migration recorded: SHA-256 $sourceHash; $issueCount issues; $projectCount projects; $sprintCount sprints."
Write-Output 'Run scripts/validate_tawos_migration.ps1 before using the target.'
