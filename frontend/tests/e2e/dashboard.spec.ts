import { test, expect } from '@playwright/test';

test.describe('Dashboard Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('http://localhost:3000/auth/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for navigation
    await page.waitForURL(/(onboarding|dashboard)/);
    
    // If on onboarding, complete it
    if (page.url().includes('onboarding')) {
      await page.fill('input[name="monthlyIncome"]', '20000');
      await page.fill('input[name="savingsGoal"]', '5000');
      await page.click('button:has-text("Next")');
      
      await page.fill('input[name="fixedExpenseName"]', 'Rent');
      await page.fill('input[name="fixedExpenseAmount"]', '8000');
      await page.click('button:has-text("Add Fixed Expense")');
      
      await page.click('button:has-text("Complete setup")');
    }
    
    await page.waitForURL(/.*dashboard/);
  });

  test('should display dashboard with financial data', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('text=Remaining Budget')).toBeVisible();
    await expect(page.locator('text=Daily Budget')).toBeVisible();
  });

  test('should add an expense manually', async ({ page }) => {
    // Fill expense form
    await page.fill('input[name="amount"]', '150');
    await page.selectOption('select[name="category"]', 'Food');
    await page.fill('input[name="description"]', 'Lunch');
    
    // Submit
    await page.click('button:has-text("Add Expense")');
    
    // Should show success (no error message)
    await expect(page.locator('text=Failed to add expense')).not.toBeVisible();
  });

  test('should parse natural language expense', async ({ page }) => {
    // Fill natural language input
    await page.fill('input[placeholder*="₹150 lunch"]', '₹200 dinner');
    await page.click('button:has-text("Parse")');
    
    // Should auto-fill manual form
    await expect(page.locator('input[name="amount"]')).toHaveValue('200');
    await expect(page.locator('select[name="category"]')).toHaveValue('Food');
  });

  test('should open AI chat', async ({ page }) => {
    await page.click('button:has-text("Open Chat")');
    
    await expect(page.locator('text=AI Financial Assistant')).toBeVisible();
    await expect(page.locator('input[placeholder*="How much"]')).toBeVisible();
  });

  test('should send chat message', async ({ page }) => {
    await page.click('button:has-text("Open Chat")');
    await page.fill('input[placeholder*="How much"]', 'How much did I spend today?');
    await page.click('button:has-text("Send")');
    
    // Should show response (may take a moment)
    await page.waitForTimeout(2000);
    await expect(page.locator('text=Sorry, I encountered an error')).not.toBeVisible();
  });

  test('should navigate to purchase check', async ({ page }) => {
    await page.click('button:has-text("Can I afford this?")');
    
    await expect(page).toHaveURL(/.*check-purchase/);
    await expect(page.locator('text=Can I afford this?')).toBeVisible();
  });
});
