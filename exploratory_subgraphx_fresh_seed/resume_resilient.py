"""Resume the frozen audit with bounded retries for Windows file sharing locks.

Only JSON persistence and deterministic report generation are wrapped. The
original audit source, manifest, targets, seeds, computations and cases remain
unchanged. Each invocation records the recovery code and pre-resume evidence.
"""
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def retry_io(operation, *args, attempts=40, delay=.25, **kwargs):
    for attempt in range(attempts):
        try:
            return operation(*args, **kwargs)
        except PermissionError as error:
            if attempt + 1 == attempts:
                raise
            print('IO_RETRY', operation.__name__, attempt + 1, str(error), flush=True)
            time.sleep(min(delay * 2**min(attempt, 3), 2.))


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('frozen_subgraphx_seed_audit', ROOT/'run.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    original_save, original_report = audit.save, audit.report
    audit.save = lambda *args, **kwargs: retry_io(original_save, *args, **kwargs)
    audit.report = lambda *args, **kwargs: retry_io(original_report, *args, **kwargs)

    manifest_path = audit.OUT/'manifest.json'
    manifest = audit.read(manifest_path)
    for relative, expected in manifest['sources'].items():
        assert sha(audit.STUDY/relative) == expected, ('frozen source changed', relative)
    stamp = datetime.now(timezone(timedelta(hours=8)))
    record = dict(
        recorded_at_perth=stamp.isoformat(), pid=os.getpid(),
        action='Resume unchanged scientific code with PermissionError retries for JSON saves and deterministic reports.',
        frozen_manifest_sha256=sha(manifest_path), recovery_wrapper_sha256=sha(__file__),
        recovery_document_sha256=sha(ROOT/'RECOVERY.md'),
        frozen_sources_verified=True,
        prior_status=audit.read(audit.OUT/'status.json'),
        completed_case_sha256={p.name: sha(p) for p in sorted((audit.OUT/'cases').glob('*.json'))},
        progress_sha256={p.name: sha(p) for p in sorted((audit.OUT/'progress').glob('*.json'))},
        retry_policy=dict(exception='PermissionError', attempts=40, initial_delay_seconds=.25, maximum_delay_seconds=2.))
    evidence=audit.OUT/'recoveries'/f'{stamp.strftime("%Y%m%d_%H%M%S")}_{os.getpid()}.json'
    audit.save(evidence, record)
    print('RECOVERY_PROVENANCE', evidence, flush=True)
    # The original main routine re-verifies every input hash and retains its
    # exclusive controller lock, technical gate and seed-level resume checks.
    audit.main()


if __name__ == '__main__':
    main()
