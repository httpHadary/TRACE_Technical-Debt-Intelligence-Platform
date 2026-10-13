#!/usr/bin/env python3
"""Collect all exports for an exact pending task, or verify the completed snapshot."""
METRICS = ','.join(['ncloc','lines','statements','functions','classes','complexity',
    'cognitive_complexity','duplicated_lines','duplicated_lines_density','duplicated_blocks',
    'duplicated_files','comment_lines','comment_lines_density','violations','code_smells','bugs',
    'vulnerabilities','reliability_rating','security_rating','sqale_rating','sqale_index',
    'sqale_debt_ratio','coverage','line_coverage','branch_coverage','uncovered_lines',
    'uncovered_conditions','lines_to_cover','conditions_to_cover','tests','test_errors','test_failures',
    'last_commit_date'])

if __name__ == '__main__':
    from sonar_evidence import export_main
    export_main()
