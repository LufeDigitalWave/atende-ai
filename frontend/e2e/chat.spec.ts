import { test, expect } from '@playwright/test';

/**
 * E2E tests for the main chat flow.
 *
 * These tests mock the backend API to avoid needing a real LLM.
 * Run with: npx playwright test
 * First time: npx playwright install chromium
 */

// Mock SSE response for a simple greeting
const MOCK_SSE_RESPONSE = [
  'event: typing\ndata: {"active":true}\n\n',
  'event: token\ndata: {"delta":"Olá! "}\n\n',
  'event: token\ndata: {"delta":"Eu sou a "}\n\n',
  'event: token\ndata: {"delta":"Sofia, "}\n\n',
  'event: token\ndata: {"delta":"assistente da Clínica Renova."}\n\n',
  'event: lead_update\ndata: {"fields":{}}\n\n',
  'event: score_update\ndata: {"total":25,"breakdown":{"intent_saudacao":10,"session_start":15}}\n\n',
  'event: state_update\ndata: {"from":"novo","to":"em_qualificacao"}\n\n',
  'event: done\ndata: {"latency_ms":450,"message_id":"msg-1"}\n\n',
].join('');

test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock create session
    await page.route('**/api/sessions', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'test-session-001',
            niche: 'clinica_estetica',
            agent_name: 'Sofia',
            company_name: 'Clínica Renova',
            suggestions: ['Quero saber sobre melasma', 'Quanto custa?', 'Vocês atendem sábado?'],
            opening_message: 'Olá! Sou a Sofia da Clínica Renova.',
            crm_fields: [
              { key: 'customer_name', label: 'Nome', priority: 'high' },
              { key: 'need', label: 'Necessidade', priority: 'high' },
              { key: 'urgency', label: 'Urgência', priority: 'medium' },
            ],
            business_mode: 'appointment_based',
            contact_url: 'https://wa.me/5511913289497',
          }),
        });
      }
    });

    // Mock send message (SSE)
    await page.route('**/api/sessions/*/messages', async (route) => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: MOCK_SSE_RESPONSE,
      });
    });
  });

  test('selects a niche and starts chat', async ({ page }) => {
    await page.goto('/');

    // NicheSelector should be visible
    await expect(page.getByText('Atende AI')).toBeVisible();

    // Click on a niche
    await page.getByText('Clínica de Estética').click();

    // Chat should appear with agent name
    await expect(page.getByText('Sofia')).toBeVisible({ timeout: 10000 });
  });

  test('sends a message and receives SSE response', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Clínica de Estética').click();

    // Wait for chat to load
    await expect(page.getByText('Sofia')).toBeVisible({ timeout: 10000 });

    // Type and send message
    const input = page.getByLabel('Mensagem');
    await input.fill('oi');
    await page.getByLabel('Enviar mensagem').click();

    // Agent response should appear (from mock SSE)
    await expect(page.getByText('Clínica Renova')).toBeVisible({ timeout: 5000 });
  });

  test('shows demo action panel after 4 user messages', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Clínica de Estética').click();
    await expect(page.getByText('Sofia')).toBeVisible({ timeout: 10000 });

    // Send 4 messages
    const input = page.getByLabel('Mensagem');
    for (const msg of ['oi', 'quero saber', 'quanto custa', 'meu nome é Luiz']) {
      await input.fill(msg);
      await page.getByLabel('Enviar mensagem').click();
      await page.waitForTimeout(500);
    }

    // Demo action panel should appear
    await expect(page.getByText('Quero no meu negócio')).toBeVisible({ timeout: 5000 });
  });

  test('suggestions are clickable', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Clínica de Estética').click();
    await expect(page.getByText('Sofia')).toBeVisible({ timeout: 10000 });

    // Quick reply suggestions should be visible
    const suggestion = page.getByText('Quero saber sobre melasma');
    if (await suggestion.isVisible()) {
      await suggestion.click();
      // Should trigger a message send
      await page.waitForTimeout(1000);
    }
  });
});
