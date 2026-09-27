'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function CheckPurchasePage() {
  const router = useRouter();
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Shopping');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await api.post('/api/v1/decision/evaluate-purchase', {
        amount: parseFloat(amount),
        category,
        description: description || undefined,
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to evaluate purchase');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'ALLOW':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'CAUTION':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'REVIEW':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'ALLOW':
        return '✅';
      case 'CAUTION':
        return '⚠️';
      case 'REVIEW':
        return '🔴';
      default:
        return '❓';
    }
  };

  const formatCurrency = (value: number) => {
    return `₹${value.toFixed(0)}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">PayWise</h1>
            <p className="text-gray-600">Can I afford this?</p>
          </div>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>

        <div className="max-w-2xl mx-auto">
          {/* Purchase Check Form */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>💭 Check if you can afford a purchase</CardTitle>
              <CardDescription>
                Enter the purchase details to get a recommendation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCheck} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount (₹)</Label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="700"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
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
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Input
                    id="description"
                    placeholder="Clothes, shoes, etc."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                {error && (
                  <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                    {error}
                  </div>
                )}
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Evaluating...' : 'Check Purchase'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Result */}
          {result && (
            <Card className={`border-2 ${getDecisionColor(result.decision)}`}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-2xl">{getDecisionIcon(result.decision)}</span>
                  <span>{result.decision}</span>
                </CardTitle>
                <CardDescription>
                  Confidence: {(result.confidence * 100).toFixed(0)}%
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Reasoning</h3>
                  <p className="text-gray-700">{result.reasoning}</p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Financial Facts</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white p-3 rounded-md">
                      <p className="text-sm text-gray-600">Remaining Budget</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(result.facts.remaining_flexible_budget)}
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded-md">
                      <p className="text-sm text-gray-600">Daily Budget</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(result.facts.daily_budget)}
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded-md">
                      <p className="text-sm text-gray-600">Days Remaining</p>
                      <p className="text-lg font-semibold">
                        {result.facts.remaining_days}
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded-md">
                      <p className="text-sm text-gray-600">Budget Utilization</p>
                      <p className="text-lg font-semibold">
                        {result.facts.budget_utilization.toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => router.push('/dashboard')}
                    variant="outline"
                    className="flex-1"
                  >
                    Back to Dashboard
                  </Button>
                  <Button
                    onClick={() => {
                      setAmount('');
                      setDescription('');
                      setResult(null);
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    Check Another
                  </Button>
                </div>

                <div className="text-xs text-gray-500 text-center pt-4 border-t">
                  This is a budgeting recommendation based on your financial information.
                  Not financial advice. The final decision is yours.
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
