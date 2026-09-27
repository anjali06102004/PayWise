'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface DashboardData {
  monthly_income: number;
  fixed_expenses: number;
  savings_goal: number;
  flexible_budget: number;
  variable_expenses: number;
  remaining_flexible_budget: number;
  today_spending: number;
  daily_budget: number;
  weekly_budget: number;
  budget_utilization: number;
  spending_velocity: number;
  projected_month_end_balance: number;
  remaining_days: number;
  days_passed: number;
  category_breakdown: Record<string, number>;
  health_status: string;
  currency: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expenseAmount, setExpenseAmount] = useState('');
  const [expenseCategory, setExpenseCategory] = useState('Food');
  const [expenseDescription, setExpenseDescription] = useState('');
  const [addingExpense, setAddingExpense] = useState(false);
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [parsingExpense, setParsingExpense] = useState(false);
  const [insights, setInsights] = useState<string[]>([]);
  const [chatMessages, setChatMessages] = useState<{role: string, content: string}[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => {
    fetchDashboard();
    fetchInsights();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/api/v1/financial/dashboard');
      setData(response.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/auth/login');
      } else {
        setError('Failed to load dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await api.get('/api/v1/ai/insights');
      setInsights(response.data.insights);
    } catch (err) {
      // Insights are optional, don't show error
    }
  };

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddingExpense(true);
    setError('');

    try {
      await api.post('/api/v1/expenses/', {
        amount: parseFloat(expenseAmount),
        category: expenseCategory,
        description: expenseDescription || undefined,
      });
      setExpenseAmount('');
      setExpenseDescription('');
      fetchDashboard();
      fetchInsights();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add expense');
    } finally {
      setAddingExpense(false);
    }
  };

  const handleNaturalLanguageExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!naturalLanguageInput.trim()) return;

    setParsingExpense(true);
    setError('');

    try {
      const response = await api.post('/api/v1/ai/parse-expense', {
        text: naturalLanguageInput
      });

      const parsed = response.data;
      setExpenseAmount(parsed.amount.toString());
      setExpenseCategory(parsed.category);
      setExpenseDescription(parsed.description || '');
      setNaturalLanguageInput('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to parse expense');
    } finally {
      setParsingExpense(false);
    }
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    setSendingChat(true);
    const userMessage = chatInput;
    setChatInput('');

    // Add user message
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await api.post('/api/v1/ai/chat', {
        message: userMessage
      });

      // Add AI response
      setChatMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (err: any) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
    } finally {
      setSendingChat(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/auth/login');
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'on_track':
        return 'text-green-600 bg-green-50';
      case 'caution':
        return 'text-yellow-600 bg-yellow-50';
      case 'high_spending':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getHealthStatusText = (status: string) => {
    switch (status) {
      case 'on_track':
        return '🟢 On Track';
      case 'caution':
        return '🟡 Watch Spending';
      case 'high_spending':
        return '🔴 High Spending';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={() => router.push('/onboarding')} className="w-full">
              Complete Setup
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const formatCurrency = (amount: number) => {
    return `₹${amount.toFixed(0)}`;
  };

  const dailyDifference = data.today_spending - data.daily_budget;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">PayWise</h1>
            <p className="text-gray-600">AI Personal Spending Agent</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        {/* Greeting */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900">
            Good morning 👋
          </h2>
        </div>

        {/* Main Balance Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardDescription>Remaining this month</CardDescription>
            <CardTitle className="text-4xl font-bold">
              {formatCurrency(data.remaining_flexible_budget)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <Button onClick={() => router.push('/expenses/add')}>
                + Add Expense
              </Button>
              <Button variant="outline" onClick={() => router.push('/check-purchase')}>
                Can I afford this?
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Today's Spending */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardDescription>Today's Spending</CardDescription>
              <CardTitle className="text-2xl">
                {formatCurrency(data.today_spending)}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Daily Target</CardDescription>
              <CardTitle className="text-2xl">
                {formatCurrency(data.daily_budget)}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Daily Difference Alert */}
        {dailyDifference > 0 && (
          <Card className="mb-6 border-yellow-200 bg-yellow-50">
            <CardContent className="pt-6">
              <p className="text-yellow-800">
                ⚠️ {formatCurrency(dailyDifference)} above today's target
              </p>
            </CardContent>
          </Card>
        )}

        {/* Health Status */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className={`inline-block px-4 py-2 rounded-full ${getHealthStatusColor(data.health_status)}`}>
              <span className="font-semibold">{getHealthStatusText(data.health_status)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Natural Language Expense Entry */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>💬 Add Expense with Natural Language</CardTitle>
            <CardDescription>
              Type like "₹150 lunch" or "spent 80 on auto"
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleNaturalLanguageExpense} className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="₹150 lunch at cafe"
                  value={naturalLanguageInput}
                  onChange={(e) => setNaturalLanguageInput(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" disabled={parsingExpense}>
                  {parsingExpense ? 'Parsing...' : 'Parse'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Manual Expense Entry */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Manual Expense Entry</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAddExpense} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount (₹)</Label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="150"
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(e.target.value)}
                    required
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    value={expenseCategory}
                    onChange={(e) => setExpenseCategory(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="Food">Food</option>
                    <option value="Transport">Transport</option>
                    <option value="Shopping">Shopping</option>
                    <option value="Bills">Bills</option>
                    <option value="Entertainment">Entertainment</option>
                    <option value="Health">Health</option>
                    <option value="Education">Education</option>
                    <option value="Subscriptions">Subscriptions</option>
                    <option value="Personal">Personal</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  placeholder="Lunch, snacks, etc."
                  value={expenseDescription}
                  onChange={(e) => setExpenseDescription(e.target.value)}
                />
              </div>
              {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                  {error}
                </div>
              )}
              <Button type="submit" disabled={addingExpense}>
                {addingExpense ? 'Adding...' : 'Add Expense'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* AI Insights */}
        {insights.length > 0 && (
          <Card className="mb-6 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-900">💡 AI Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {insights.map((insight, index) => (
                  <p key={index} className="text-blue-800">{insight}</p>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Category Breakdown */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Monthly Spending by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data.category_breakdown).map(([category, amount]) => (
                <div key={category} className="flex justify-between items-center">
                  <span className="text-gray-700">{category}</span>
                  <span className="font-semibold">{formatCurrency(amount)}</span>
                </div>
              ))}
              {Object.keys(data.category_breakdown).length === 0 && (
                <p className="text-gray-500">No expenses recorded yet this month.</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* AI Chat */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>🤖 AI Financial Assistant</CardTitle>
            <CardDescription>
              Ask questions about your spending
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!showChat ? (
              <Button onClick={() => setShowChat(true)} className="w-full">
                Open Chat
              </Button>
            ) : (
              <div className="space-y-4">
                <div className="h-64 overflow-y-auto border rounded-md p-4 space-y-2">
                  {chatMessages.length === 0 && (
                    <p className="text-gray-500 text-center">
                      Ask me anything about your finances!
                    </p>
                  )}
                  {chatMessages.map((msg, index) => (
                    <div
                      key={index}
                      className={`p-2 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-blue-100 ml-8'
                          : 'bg-gray-100 mr-8'
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  ))}
                </div>
                <form onSubmit={handleSendChat} className="flex gap-2">
                  <Input
                    placeholder="How much did I spend on food?"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={sendingChat}>
                    {sendingChat ? '...' : 'Send'}
                  </Button>
                </form>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowChat(false)}
                >
                  Close Chat
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardDescription>Monthly Income</CardDescription>
              <CardTitle>{formatCurrency(data.monthly_income)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Savings Goal</CardDescription>
              <CardTitle>{formatCurrency(data.savings_goal)}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Days Remaining</CardDescription>
              <CardTitle>{data.remaining_days}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      </div>
    </div>
  );
}
