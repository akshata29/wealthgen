<#
    deploy.ps1 — Build and deploy WealthGen (frontend + backend) as a SINGLE
    Azure App Service (Linux container).

    - Builds the multi-stage Docker image IN AZURE via `az acr build`
      (no local Docker required).
    - Creates/uses an ACR, a Linux App Service Plan, and a Web App for Containers.
    - Copies backend/.env into the Web App's application settings.
    - Registers the site URL as an MSAL SPA redirect URI so sign-in works.

    Usage (from the repo root):
        pwsh ./deploy.ps1
        pwsh ./deploy.ps1 -App my-unique-name -Acr myuniqueacr

    Requires: Azure CLI logged in to the target tenant/subscription, and the
    backend virtualenv at backend/.venv (used only to parse .env).
#>
[CmdletBinding()]
param(
    [string]$Subscription = "cb8c7354-e2e7-4ce0-9f6c-5752d3bf9fc9",
    [string]$ResourceGroup = "hackathon",
    [string]$Location = "centralus",
    [string]$Acr = "wgenhackacr",
    [string]$Plan = "wgenhack-plan",
    [string]$App = "wgenhack-app",
    [string]$Sku = "B1",
    [string]$ImageTag = "wealthgen:latest",
    # SPA app registration (MSAL) — used to add the prod redirect URI.
    [string]$SpaAppId = "e16291f8-52df-408d-9373-90d53fae489d"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Run an `az ... show/list` lookup that may legitimately fail (resource absent)
# without aborting the script under $ErrorActionPreference = 'Stop'.
function Get-OrNull {
    param([scriptblock]$Script)
    try { return (& $Script 2>$null) } catch { return $null }
}

Write-Host "==> Subscription" -ForegroundColor Cyan
az account set --subscription $Subscription

# --- 1. Azure Container Registry -------------------------------------------
Write-Host "==> Container registry ($Acr)" -ForegroundColor Cyan
$acrExists = Get-OrNull { az acr show -n $Acr -g $ResourceGroup --query name -o tsv }
if (-not $acrExists) {
    az acr create -n $Acr -g $ResourceGroup --sku Basic --admin-enabled false -o none
}
$acrLoginServer = az acr show -n $Acr --query loginServer -o tsv
$fullImage = "$acrLoginServer/$ImageTag"

# --- 2. Build the image in the cloud (runs the Dockerfile in Azure) --------
Write-Host "==> Building image via ACR Tasks: $fullImage" -ForegroundColor Cyan
az acr build -r $Acr -t $ImageTag -f (Join-Path $root "Dockerfile") $root
if ($LASTEXITCODE -ne 0) { throw "ACR image build failed (exit $LASTEXITCODE). Aborting deploy." }

# --- 3. App Service Plan (Linux) -------------------------------------------
Write-Host "==> App Service plan ($Plan, $Sku)" -ForegroundColor Cyan
$planExists = Get-OrNull { az appservice plan show -n $Plan -g $ResourceGroup --query name -o tsv }
if (-not $planExists) {
    az appservice plan create -n $Plan -g $ResourceGroup --is-linux --sku $Sku -o none
}

# --- 4. Web App for Containers ---------------------------------------------
Write-Host "==> Web App ($App)" -ForegroundColor Cyan
$appExists = Get-OrNull { az webapp show -n $App -g $ResourceGroup --query name -o tsv }
if (-not $appExists) {
    az webapp create -g $ResourceGroup -p $Plan -n $App `
        --deployment-container-image-name $fullImage -o none
}

# --- 5. Managed identity -> ACR pull ---------------------------------------
Write-Host "==> Managed identity + AcrPull" -ForegroundColor Cyan
az webapp identity assign -g $ResourceGroup -n $App -o none | Out-Null
$principalId = az webapp identity show -g $ResourceGroup -n $App --query principalId -o tsv
$acrId = az acr show -n $Acr --query id -o tsv
$hasPull = Get-OrNull { az role assignment list --assignee $principalId --scope $acrId --query "[?roleDefinitionName=='AcrPull'] | length(@)" -o tsv }
if ($hasPull -ne "1") {
    az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal `
        --role AcrPull --scope $acrId -o none
}
az webapp config set -g $ResourceGroup -n $App --generic-configurations '{\"acrUseManagedIdentityCreds\": true}' -o none
az webapp config container set -g $ResourceGroup -n $App `
    --container-image-name $fullImage `
    --container-registry-url "https://$acrLoginServer" -o none

# --- 6. Application settings from backend/.env -----------------------------
Write-Host "==> Application settings (from backend/.env)" -ForegroundColor Cyan
$appUrl = "https://$App.azurewebsites.net"
$settingsFile = Join-Path $root "appsettings.generated.json"
& $py -c @"
import json
from dotenv import dotenv_values
v = {k: val for k, val in dotenv_values(r'backend/.env').items() if val is not None}
# Platform / prod overrides
v['WEBSITES_PORT'] = '8000'
v['APP_ENV'] = 'prod'
v['CORS_ORIGINS'] = '$appUrl'
items = [{'name': k, 'value': val} for k, val in v.items()]
open(r'$settingsFile', 'w', encoding='utf-8').write(json.dumps(items))
print(f'{len(items)} settings written')
"@
az webapp config appsettings set -g $ResourceGroup -n $App --settings "@$settingsFile" -o none
Remove-Item $settingsFile -ErrorAction SilentlyContinue

# --- 7. Register the prod URL as an MSAL SPA redirect URI ------------------
Write-Host "==> MSAL SPA redirect URI ($appUrl)" -ForegroundColor Cyan
$spaObj = az ad app show --id $SpaAppId --query id -o tsv
$current = az ad app show --id $SpaAppId --query "spa.redirectUris" -o json | ConvertFrom-Json
if ($current -notcontains $appUrl) {
    $uris = @()
    if ($current) { $uris += $current }
    $uris += $appUrl
    $spaBody = @{ spa = @{ redirectUris = $uris } } | ConvertTo-Json -Depth 5
    $spaFile = Join-Path $root "spa.generated.json"
    $spaBody | Out-File -Encoding utf8 $spaFile
    az rest --method patch --url "https://graph.microsoft.com/v1.0/applications/$spaObj" `
        --headers "Content-Type=application/json" --body "@$spaFile" -o none
    Remove-Item $spaFile -ErrorAction SilentlyContinue
}

# --- 8. Restart & report ---------------------------------------------------
Write-Host "==> Restarting" -ForegroundColor Cyan
az webapp restart -g $ResourceGroup -n $App -o none

Write-Host ""
Write-Host "Deployed: $appUrl" -ForegroundColor Green
Write-Host "Logs:     az webapp log tail -g $ResourceGroup -n $App"
