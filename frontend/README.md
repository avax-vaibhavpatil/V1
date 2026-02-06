# Analytics Studio Frontend

React + TypeScript frontend for Analytics Studio.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn/pnpm
- Backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   ├── pages/          # Page components
│   ├── services/       # API service layer
│   ├── types/          # TypeScript type definitions
│   ├── context/        # React Context providers
│   ├── hooks/          # Custom React hooks
│   └── utils/          # Utility functions
├── public/             # Static assets
└── package.json
```

## 🔌 API Integration

All API calls are handled through service modules in `src/services/`:
- `projects.ts` - Project management
- `datasets.ts` - Dataset operations
- `dashboards.ts` - Dashboard operations
- `semantic.ts` - Semantic layer
- `query.ts` - Query execution
- `files.ts` - File uploads
- `databaseConnections.ts` - Database connections
- `calculations.ts` - Calculation validation
- `dependencySafety.ts` - Dependency checks

## 🎨 Features

- ✅ Project workspace management
- ✅ Dataset explorer
- ✅ Dashboard management
- 🔄 File upload (UI ready, needs implementation)
- 🔄 Visual builder (coming soon)
- 🔄 Calculation builder (coming soon)

## 🔧 Configuration

Create `.env` file:
```
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Analytics Studio
```

## 📚 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## 🚧 Next Steps

1. Implement file upload UI
2. Build visual builder components
3. Add calculation builder
4. Implement dashboard canvas with drag & drop
5. Add authentication


