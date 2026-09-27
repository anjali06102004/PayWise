import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should navigate to registration page', async ({ page }) => {
    await page.click('text=Get Started');
    await expect(page).toHaveURL(/.*register/);
    await expect(page.locator('h1')).toContainText('Register');
  });

  test('should register a new user', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/register');
    
    // Fill registration form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="fullName"]', 'Test User');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to onboarding
    await expect(page).toHaveURL(/.*onboarding/);
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard or onboarding
    await expect(page.url()).toMatch(/(onboarding|dashboard)/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/auth/login');
    
    // Fill with invalid credentials
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});
