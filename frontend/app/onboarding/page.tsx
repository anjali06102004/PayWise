'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Financial profile state
  const [monthlyIncome, setMonthlyIncome] = useState('');
  const [savingsGoal, setSavingsGoal] = useState('');

  // Fixed expenses state
  const [fixedExpenses, setFixedExpenses] = useState([
    { name: 'Rent', amount: '', category: 'Housing' },
    { name: 'Food', amount: '', category: 'Food' },
    { name: 'Transport', amount: '', category: 'Transport' },
  ]);

  useEffect(() => {
    // Check if user already has a profile
    const checkProfile = async () => {
      try {
        await api.get('/api/v1/financial/profile');
        router.push('/dashboard');
      } catch (err) {
        // Profile doesn't exist, continue with onboarding
      }
    };
    checkProfile();
  }, [router]);

  const handleFixedExpenseChange = (index: number, field: 'name' | 'amount' | 'category', value: string) => {
    const updated = [...fixedExpenses];
    updated[index][field] = value;
    setFixedExpenses(updated);
  };

  const addFixedExpense = () => {
    setFixedExpenses([...fixedExpenses, { name: '', amount: '', category: 'Other' }]);
  };

  const removeFixedExpense = (index: number) => {
    if (fixedExpenses.length > 1) {
      setFixedExpenses(fixedExpenses.filter((_, i) => i !== index));
    }
  };

  const handleSubmitStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/api/v1/financial/profile', {
        monthly_income: parseFloat(monthlyIncome),
        savings_goal: parseFloat(savingsGoal),
        currency: 'INR',
      });
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitStep2 = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Save all fixed expenses
      for (const expense of fixedExpenses) {
        if (expense.name && expense.amount) {
          await api.post('/api/v1/financial/fixed-expenses', {
            name: expense.name,
            amount: parseFloat(expense.amount),
            category: expense.category,
          });
        }
      }
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save expenses. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (step === 1) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">Set up your budget</CardTitle>
            <CardDescription className="text-center">
              Step 1 of 2: Income and savings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitStep1} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="monthlyIncome">Monthly Income (₹)</Label>
                <Input
                  id="monthlyIncome"
                  type="number"
                  placeholder="20000"
                  value={monthlyIncome}
                  onChange={(e) => setMonthlyIncome(e.target.value)}
                  required
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="savingsGoal">Monthly Savings Goal (₹)</Label>
                <Input
                  id="savingsGoal"
                  type="number"
                  placeholder="5000"
                  value={savingsGoal}
                  onChange={(e) => setSavingsGoal(e.target.value)}
                  required
                  min="0"
                  step="0.01"
                />
              </div>
              {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                  {error}
                </div>
              )}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Saving...' : 'Continue'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-8">
      <Card className="w-full max-w-2xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Add fixed expenses</CardTitle>
          <CardDescription className="text-center">
            Step 2 of 2: Regular monthly expenses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmitStep2} className="space-y-4">
            {fixedExpenses.map((expense, index) => (
              <div key={index} className="grid grid-cols-3 gap-2 items-end">
                <div className="space-y-2">
                  <Label htmlFor={`name-${index}`}>Name</Label>
                  <Input
                    id={`name-${index}`}
                    placeholder="Rent"
                    value={expense.name}
                    onChange={(e) => handleFixedExpenseChange(index, 'name', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`amount-${index}`}>Amount (₹)</Label>
                  <Input
                    id={`amount-${index}`}
                    type="number"
                    placeholder="5000"
                    value={expense.amount}
                    onChange={(e) => handleFixedExpenseChange(index, 'amount', e.target.value)}
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor={`category-${index}`}>Category</Label>
                  <div className="flex gap-2">
                    <Input
                      id={`category-${index}`}
                      placeholder="Housing"
                      value={expense.category}
                      onChange={(e) => handleFixedExpenseChange(index, 'category', e.target.value)}
                    />
                    {fixedExpenses.length > 1 && (
                      <Button
                        type="button"
                        variant="destructive"
                        size="icon"
                        onClick={() => removeFixedExpense(index)}
                      >
                        ×
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              onClick={addFixedExpense}
              className="w-full"
            >
              + Add another expense
            </Button>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Saving...' : 'Complete setup'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
