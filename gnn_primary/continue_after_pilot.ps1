$ErrorActionPreference = 'Stop'
$studyRoot = $PSScriptRoot
$studyPython = 'C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe'
$pilotStatus = Join-Path $studyRoot 'results\pilot\status.json'
$pipelineStatus = Join-Path $studyRoot 'results\pipeline_status.json'
$fullLog = Join-Path $studyRoot 'results\full.log'
@{ state = 'waiting_for_pilot'; datasets = @('amlsim', 'hi_small') } | ConvertTo-Json | Set-Content -LiteralPath $pipelineStatus
while ($true) {
    if (Test-Path -LiteralPath $pilotStatus) {
        $pilotState = Get-Content -LiteralPath $pilotStatus -Raw | ConvertFrom-Json
        if ($pilotState.state -eq 'failed') {
            @{ state = 'failed'; stage = 'pilot'; detail = 'Full run not started; inspect pilot/status.json.' } | ConvertTo-Json | Set-Content -LiteralPath $pipelineStatus
            exit 1
        }
        if ($pilotState.state -eq 'complete') { break }
    }
    Start-Sleep -Seconds 10
}
@{ state = 'running'; stage = 'full'; datasets = @('amlsim', 'hi_small'); trials = 5; targets = 'all eligible test targets' } | ConvertTo-Json | Set-Content -LiteralPath $pipelineStatus
& $studyPython -u (Join-Path $studyRoot 'run.py') full --trials 5 --targets 0 *> $fullLog
$studyExit = $LASTEXITCODE
@{ state = $(if ($studyExit -eq 0) { 'complete' } else { 'failed' }); stage = 'full'; exit_code = $studyExit } | ConvertTo-Json | Set-Content -LiteralPath $pipelineStatus
exit $studyExit
