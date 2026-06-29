#Requires -Version 5.0
# install.ps1 — install / update the Agent Skills library on Windows (no git clone needed).
#
# Installs ONLY the skills this library provides (top-level directories that contain a
# SKILL.md) into your agent skills directory. Each of THOSE skills is clean-replaced;
# any other skill you already have is left fully untouched.
#
# Usage:
#   irm https://raw.githubusercontent.com/duysqubix/skills/main/install.ps1 | iex
#
# Env overrides: $env:AGENTS_SKILLS_DIR, $env:SKILLS_REPO, $env:SKILLS_BRANCH
$ErrorActionPreference = 'Stop'

$Repo   = if ($env:SKILLS_REPO)       { $env:SKILLS_REPO }       else { 'duysqubix/skills' }
$Branch = if ($env:SKILLS_BRANCH)     { $env:SKILLS_BRANCH }     else { 'main' }
$Dest   = if ($env:AGENTS_SKILLS_DIR) { $env:AGENTS_SKILLS_DIR } else { Join-Path $env:USERPROFILE '.agents\skills' }
$Url    = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"

$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('skills-' + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
try {
    $Zip = Join-Path $Tmp 'skills.zip'
    Write-Host "Downloading $Repo@$Branch ..."
    Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing
    Expand-Archive -Path $Zip -DestinationPath $Tmp -Force

    $Src = Get-ChildItem -Path $Tmp -Directory | Where-Object { $_.Name -like 'skills-*' } | Select-Object -First 1
    if (-not $Src) { throw 'could not locate the extracted repository' }

    New-Item -ItemType Directory -Force -Path $Dest | Out-Null

    $installed = 0
    Get-ChildItem -Path $Src.FullName -Directory | ForEach-Object {
        if (Test-Path (Join-Path $_.FullName 'SKILL.md')) {
            $target = Join-Path $Dest $_.Name
            if (Test-Path $target) { Remove-Item -Recurse -Force $target }   # clean-replace ONLY this repo's skill
            Copy-Item -Recurse -Force -Path $_.FullName -Destination $target
            $installed++
            Write-Host "  + $($_.Name)"
        }
    }
    if ($installed -eq 0) { throw "no skills (SKILL.md directories) found in $Repo@$Branch" }

    Write-Host ''
    Write-Host "Installed/updated $installed skill(s) into $Dest"
    Write-Host "Your other skills in $Dest were left untouched."
    Write-Host 'Start a new agent session to pick them up.'
}
finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}
