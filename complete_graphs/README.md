# Complete graphs / all eligible targets

Separate expanded experiment. Read PROTOCOL.md for exact graph definitions and eligibility. The original sampled study remains in the parent directory.

Main Python: C:\habib dissertation\Projects\defence\.venv\Scripts\python.exe

Stages: prepare.py reconstructs full graphs, retrains Elliptic/HI-Small and fits five PG networks; validate_core.py checks numerical correctness; continue_study.py runs the three-dataset pilot then ALL eligible test targets; paper_report.py generates paper-layout tables with adapted metrics labelled.

Cases save atomically. Summaries update every25 cases and at dataset/phase completion. Check results/preparation_status.json and results/pipeline_status.json. Logs: results/prepare.log, results/pilot_continued.log, results/full_continued.log. Do not launch concurrent controllers. Eligibility excludes unknown labels, incorrect predictions and oversized/tiny contexts.

The copied report.py is the legacy formatter; the controller uses paper_report.py.
