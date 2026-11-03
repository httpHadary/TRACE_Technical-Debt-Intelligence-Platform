"""Use the already installed Playwright/browser; no downloads or product edits."""
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

ROOT=Path(sys.argv[2]).resolve()
base=sys.argv[1]
cases=json.loads((ROOT/'cases.json').read_text())
receipts=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport=dict(width=1365,height=1000))
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/*',lambda route:route.continue_() if urlsplit(route.request.url).netloc==urlsplit(base).netloc else route.abort())
    page.goto(base,wait_until='networkidle')
    expect(page.locator('#status')).to_contain_text('verified persistence endpoint',timeout=30000)
    for case in cases:
        if page.locator('#bundle').input_value()!=case['bundle_id']:
            page.select_option('#bundle',case['bundle_id'])
        expected_label='Maintainability SQALE' if case['target']=='native_sqale_index_minutes' else 'Total principal'
        expect(page.locator('#target-label')).to_contain_text(expected_label,timeout=30000)
        expect(page.locator('#status')).to_contain_text('verified persistence endpoint',timeout=30000)
        page.wait_for_load_state('networkidle')
        assert page.locator('#status').get_attribute('class')!='error'
        assert 'SOFTWARE_VALIDATION_ONLY' in page.locator('#provenance').inner_text()
        coverage=page.locator('#coverage').inner_text()
        for lang,value in case['languages'].items():assert f'{lang}: {value} NCLOC' in coverage
        assert 'domain' in coverage and 'scope' in coverage and 'analysis' in coverage
        stock=page.locator('#metrics article strong').first.inner_text()
        assert stock==('Unavailable' if case['expected_minutes'] is None else str(case['expected_minutes'])),(case,stock)
        assert page.locator('#history tr').count()==3
        assert page.locator('#horizon option').count()==6
        assert 'Pending' in page.locator('#metrics').inner_text() if case['expected_minutes'] is not None else 'UNAVAILABLE' in page.locator('#metrics').inner_text()
        page.select_option('#horizon','elapsed_day:30')
        expect(page.locator('#status')).to_contain_text('Exact elapsed UTC days',timeout=30000)
        page.wait_for_load_state('networkidle')
        assert page.locator('#metrics article strong').first.inner_text()==stock
        filename=case['case']+'-'+('sqale' if case['target']=='native_sqale_index_minutes' else 'principal')+'.png'
        page.screenshot(path=str(ROOT/filename),full_page=True)
        receipts.append(dict(case=case['case'],target=case['target'],origin_stock_display=stock,languages=case['languages'],clocks_checked=['revision_step:3','elapsed_day:30'],history_rows=3,screenshot=filename,status='PASS'))
    assert not errors,errors
    (ROOT/'browser_receipt.json').write_text(json.dumps(dict(status='PASS_RENDERED_BROWSER_E2E',browser_version=browser.version,receipts=receipts,page_errors=errors,external_requests_allowed=False),indent=2)+'\n')
    browser.close()
print('PASS: six fixture-backed dashboard targets rendered in cached Chromium')
