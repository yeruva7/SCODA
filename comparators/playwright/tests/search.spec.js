// Structural assertions over the functional workload, matching the
// assertion set the SCODA side applies in workloads/workload.py.

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const workloadPath =
  process.env.WORKLOAD || path.join(__dirname, '..', '..', '..', 'workloads', 'functional_500.json');
const workload = JSON.parse(fs.readFileSync(workloadPath, 'utf-8'));

for (const testCase of workload.cases) {
  test(`search: ${testCase.id}`, async ({ request }, testInfo) => {
    const response = await request.post('/search', {
      data: { query: testCase.query, tenant: testInfo.project.name },
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
    expect(Array.isArray(body.results)).toBe(true);
    expect(body.results.length).toBeGreaterThan(0);
    expect(body.page.size).toBe(10);
  });
}
