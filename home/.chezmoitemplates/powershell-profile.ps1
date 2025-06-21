{{- if eq .chezmoi.os "windows" }}
# only use on Windows because pwsh on linux and macos inherit from .bashrc
$Env:XDG_CONFIG_HOME = "{{ .chezmoi.homeDir }}/.config"
$Env:XDG_DATA_HOME = "{{ .chezmoi.homeDir }}/.local/share"
$Env:XDG_CACHE_HOME = "{{ .chezmoi.homeDir }}/.cache"
$Env:XDG_STATE_HOME = "{{ .chezmoi.homeDir }}/.local/state"
{{- end }}

function DockerCompose { docker compose @args }
New-Alias c DockerCompose -Force

function ChezmoiAlias { chezmoi @args }
New-Alias cm ChezmoiAlias -Force

function SkopeoRun { docker run --rm quay.io/skopeo/stable @args }
New-Alias skopeo SkopeoRun -Force

$Env:DOTNET_WATCH_RESTART_ON_RUDE_EDIT = "true"
