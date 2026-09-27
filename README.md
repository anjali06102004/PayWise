# AI Personal Spending Agent

A personal financial decision assistant that helps users track, understand, and control everyday discretionary spending.

## Core Purpose

**Track → Understand → Predict → Warn → Help the user make better spending decisions.**

### Key Feature: "Can I afford this?"

Users can ask questions like:
- "Can I spend ₹500 on clothes?"
- "Can I order food for ₹250?"
- "Can I afford ₹1,000 this weekend?"

The system provides reasoned spending recommendations based on actual financial state.

## Architecture

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts
- React Hook Form
- Zod

### Backend
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis

### AI/ML
- LLM API (configurable provider)
- LangGraph (for multi-step workflows)
- Jev AI API (decision layer)

## Getting Started

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (optional, for AI features)
- Jev API key (optional, for enhanced decisions)

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/paywise.git
cd paywise
```

2. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys (optional):
```env
LLM_API_KEY=your-openai-api-key
JEV_API_KEY=your-jev-api-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
```

3. **Start all services**
```bash
docker compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Setup

See [RUNNING.md](RUNNING.md) for detailed manual setup instructions.

## Testing

### Backend Tests
```bash
docker exec paywise-backend pytest tests/test_finance_engine.py -v
```

### Frontend E2E Tests
```bash
cd frontend
npm install
npm run test:e2e
```

### Project Structure

```
ai-spending-agent/
├── frontend/          # Next.js application
├── backend/           # FastAPI application
├── docker-compose.yml # Multi-container setup
└── .env.example      # Environment variables template
```

## Features

### Phase 1: Core Infrastructure ✅
- User authentication (JWT)
- Onboarding flow
- PostgreSQL database with Alembic migrations
- Expense CRUD operations
- Dashboard with financial overview
- Deterministic finance engine

### Phase 2: AI-Powered Features ✅
- Natural language expense parsing
- LLM structured extraction
- AI chat with tool calling
- Spending insights generation

### Phase 3: Decision Layer ✅
- Jev AI integration
- "Can I afford this?" purchase evaluation
- Spending risk assessment
- Anomaly detection
- Decision logging

### Phase 4: Production Features ✅
- Structured JSON logging
- Rate limiting middleware
- Langfuse observability integration
- Enhanced health checks
- Backend tests (Pytest)
- Frontend E2E tests (Playwright)

## Philosophy

This application NEVER shames users. It provides context, not control.

Instead of: "You waste too much money."
Say: "Your current spending pace is above your monthly target."

The user always makes the final decision.

## Safety Notice

This product does NOT provide:
- Investment advice
- Tax advice
- Loan recommendations
- Professional financial advice
- Guaranteed financial outcomes

Scope: Personal budgeting and spending awareness based on user-provided information.

## License

MIT
