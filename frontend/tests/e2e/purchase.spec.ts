import { test, expect } from '@playwright/test';

test.describe('Purchase Evaluation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to purchase check
    await page.goto('http://localhost:3000/auth/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await page.waitForURL(/(onboarding|dashboard)/);
    
    // Skip onboarding if needed
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
    await page.click('button:has-text("Can I afford this?")');
    await page.waitForURL(/.*check-purchase/);
  });

  test('should display purchase check form', async ({ page }) => {
    await expect(page.locator('text=Can I afford this?')).toBeVisible();
    await expect(page.locator('input[name="amount"]')).toBeVisible();
    await expect(page.locator('select[name="category"]')).toBeVisible();
  });

  test('should evaluate a purchase', async ({ page }) => {
    // Fill purchase form
    await page.fill('input[name="amount"]', '700');
    await page.selectOption('select[name="category"]', 'Shopping');
    await page.fill('input[name="description"]', 'Clothes');
    
    // Submit
    await page.click('button:has-text("Check Purchase")');
    
    // Should show decision
    await expect(page.locator('text=ALLOW|CAUTION|REVIEW')).toBeVisible();
    await expect(page.locator('text=Reasoning')).toBeVisible();
    await expect(page.locator('text=Financial Facts')).toBeVisible();
  });

  test('should show financial facts after evaluation', async ({ page }) => {
    await page.fill('input[name="amount"]', '700');
    await page.selectOption('select[name="category"]', 'Shopping');
    await page.click('button:has-text("Check Purchase")');
    
    await expect(page.locator('text=Remaining Budget')).toBeVisible();
    await expect(page.locator('text=Daily Budget')).toBeVisible();
    await expect(page.locator('text=Days Remaining')).toBeVisible();
  });

  test('should allow checking another purchase', async ({ page }) => {
    await page.fill('input[name="amount"]', '700');
    await page.selectOption('select[name="category"]', 'Shopping');
    await page.click('button:has-text("Check Purchase")');
    
    await page.click('button:has-text("Check Another")');
    
    // Form should be cleared
    await expect(page.locator('input[name="amount"]')).toHaveValue('');
  });

  test('should navigate back to dashboard', async ({ page }) => {
    await page.click('button:has-text("Back to Dashboard")');
    
    await expect(page).toHaveURL(/.*dashboard/);
  });
});
