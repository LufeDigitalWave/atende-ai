import { test, expect } from '@playwright/test';

test.describe('Marketing pages', () => {
  test('home explains WhatsApp Agents and links to demo', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: /Agentes de IA para WhatsApp/ })).toBeVisible();
    await expect(page.getByText('SDR Agent').first()).toBeVisible();
    await expect(page.getByText('Support Agent').first()).toBeVisible();

    await page.getByRole('link', { name: /Testar demo SDR/ }).first().click();
    await expect(page).toHaveURL(/\/demo$/);
    await expect(page.getByRole('heading', { name: 'Atende AI' })).toBeVisible();
  });

  test('agents catalog lists all six offers', async ({ page }) => {
    await page.goto('/agentes');

    for (const name of ['SDR Agent', 'Support Agent', 'Appointment Agent', 'FAQ/RAG Agent', 'Civic Agent', 'Collections Agent']) {
      await expect(page.getByRole('heading', { name }).first()).toBeVisible();
    }
  });

  test('pricing page shows packages and simulator', async ({ page }) => {
    await page.goto('/pricing');

    await expect(page.getByRole('heading', { name: 'Starter', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Pro', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Business', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Simulador/ })).toBeVisible();

    const slider = page.getByRole('slider', { name: /conversas/i });
    await expect(slider).toBeVisible();
    await slider.fill('2000');
    await expect(page.getByText('2.000', { exact: true })).toBeVisible();
  });
});
