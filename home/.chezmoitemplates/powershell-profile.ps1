function DockerCompose { docker compose @args }
New-Alias c DockerCompose -Force

function SkopeoRun { docker run --rm quay.io/skopeo/stable @args }
New-Alias skopeo SkopeoRun -Force

$Env:DOTNET_WATCH_RESTART_ON_RUDE_EDIT = "true"
