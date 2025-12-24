# Kaaj Frontend

A modern, beautiful React + TypeScript frontend for the Kaaj loan management system.

## Features

- 📄 **Lender Policy Management** - Upload and manage lending policy documents
- 📋 **Loan Application Management** - Upload loan applications and view matching results
- 🎨 **Modern UI** - Built with React, TypeScript, and Tailwind CSS
- 🔄 **Real-time Updates** - Auto-refresh to show processing status
- 📊 **Match Visualization** - View loan-to-lender match scores and analysis

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **TanStack Query** - Data fetching and caching
- **Axios** - HTTP client
- **React Dropzone** - File upload
- **Lucide React** - Icons
- **date-fns** - Date formatting

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Update .env with your API URL if different
# VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Build for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Layout.tsx      # Main layout with navigation
│   │   ├── FileUpload.tsx  # Drag & drop file upload
│   │   ├── StatusBadge.tsx # Status indicator
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
│   ├── pages/              # Page components
│   │   ├── Lenders.tsx     # Lender management page
│   │   └── LoanApplications.tsx # Loan application page
│   ├── services/           # API services
│   │   └── api.ts          # API client and methods
│   ├── types/              # TypeScript types
│   │   └── index.ts        # Type definitions
│   ├── config.ts           # Configuration
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── index.html              # HTML template
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
└── tsconfig.json           # TypeScript configuration
```

## Pages

### Lenders (`/lenders`)

Upload and manage lending policy documents:
- Upload PDF documents with lender information
- View all lenders in a table
- Filter by status (uploaded, processing, completed, failed)
- View processing results
- Delete lenders

### Loan Applications (`/loan-applications`)

Upload and manage loan applications:
- Upload PDF loan applications
- View all applications in a table
- Filter by status
- View match results with lenders
- See match scores and analysis
- Delete applications

## API Integration

The frontend communicates with the FastAPI backend:

- `POST /api/lenders/upload` - Upload lender PDF
- `GET /api/lenders/` - List all lenders
- `GET /api/lenders/{id}` - Get lender details
- `DELETE /api/lenders/{id}` - Delete lender

- `POST /api/loan-applications/upload` - Upload loan application PDF
- `GET /api/loan-applications/` - List all applications
- `GET /api/loan-applications/{id}` - Get application details with matches
- `DELETE /api/loan-applications/{id}` - Delete application

## Features

### Auto-refresh

Both pages automatically refresh every 5 seconds to show the latest processing status.

### File Upload

Drag & drop or click to upload PDF files. The component validates file types and shows file information.

### Status Badges

Color-coded badges show the processing status:
- 🔵 **Uploaded** - File uploaded, waiting for processing
- 🟡 **Processing** - Currently being processed
- 🟢 **Completed** - Processing completed successfully
- 🔴 **Failed** - Processing failed

### Match Visualization

For loan applications, view:
- Match scores (0-100) for each lender
- Match analysis and criteria
- Sorted by match score (highest first)

## Environment Variables

- `VITE_API_BASE_URL` - Backend API URL (default: `http://localhost:8000`)

## Development

### Code Style

The project uses ESLint for code quality. Run:

```bash
npm run lint
```

### Type Checking

TypeScript is configured for strict type checking:

```bash
npm run type-check
```

## Deployment

Build the production bundle:

```bash
npm run build
```

The built files will be in the `dist/` directory. Deploy this directory to any static hosting service (Vercel, Netlify, AWS S3, etc.).

## License

Copyright © 2025 Kaaj. All rights reserved.
