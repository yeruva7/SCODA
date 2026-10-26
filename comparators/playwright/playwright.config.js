// Playwright comparator configuration.
//
// Parallel browser contexts, project-scoped configuration. Multi-tenant
// coordination is left to external tooling, which is the R4 gap recorded
// for this generation in Table 1: a tenant is a project here, so a shared
// default changes by editing every project entry.
//
//   SUT_ENDPOINT=http://127.0.0.1:8080 npx playwright test --repeat-each=5

const { defineConfig } = require('@playwright/test');

const endpoint = process.env.SUT_ENDPOINT;
if (!endpoint) {
  throw new Error('set SUT_ENDPOINT to the base URL of the system under test');
}

// One project per tenant. There is no inheritance between them; each entry
// repeats every setting it needs.
const tenants = ['tenant-0001', 'tenant-0002', 'tenant-0003'];

module.exports = defineConfig({
  testDir: './tests',
  // Matched to the protocol's 16 workers.
  workers: 16,
  fullyParallel: true,
  retries: 0,
  reporter: [['json', { outputFile: 'runs.json' }]],
  use: {
    baseURL: endpoint,
    headless: true,
    actionTimeout: 10000,
  },
  projects: tenants.map((tenant) => ({
    name: tenant,
    use: {
      baseURL: endpoint,
      headless: true,
      actionTimeout: 10000,
      extraHTTPHeaders: { 'X-Tenant': tenant },
    },
  })),
});
