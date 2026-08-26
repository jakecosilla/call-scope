import { expect, test } from '@playwright/test';

test.describe('CallScope E2E Batch Workflow', () => {
  test('evaluator happy path: login, batch upload, analysis, and result review', async ({ page }) => {
    await page.goto('http://localhost:3000');

    await expect(page.getByText('CallScope AI')).toBeVisible();

    await page.getByRole('button', { name: /Auto-fill Evaluator Credentials/i }).click();
    await page.getByRole('button', { name: /Authenticate & Access Dashboard/i }).click();

    await expect(page.getByText('Upload Evaluation Batch')).toBeVisible();
    await expect(page.getByText('evaluator@callscope.ai')).toBeVisible();
  });
});
