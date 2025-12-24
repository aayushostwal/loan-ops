# Kaaj Frontend Documentation

## Overview

The Kaaj frontend is a modern, responsive web application built with React and TypeScript. It provides a beautiful, intuitive interface for managing lender policies and loan applications.

## Architecture

### Technology Stack

- **React 18** - Modern UI library with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v7** - Client-side routing
- **TanStack Query (React Query)** - Server state management
- **Axios** - HTTP client
- **React Dropzone** - File upload with drag & drop
- **Lucide React** - Beautiful icon library
- **date-fns** - Date formatting

### Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # Main layout with header/footer
│   │   ├── FileUpload.tsx   # Drag & drop file upload
│   │   ├── StatusBadge.tsx  # Status indicator badges
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
│   ├── pages/               # Page components
│   │   ├── Lenders.tsx      # Lender management page
│   │   └── LoanApplications.tsx
│   ├── services/            # API services
│   │   └── api.ts           # API client and methods
│   ├── types/               # TypeScript definitions
│   │   └── index.ts
│   ├── config.ts            # Configuration
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite config
├── tailwind.config.js       # Tailwind config
├── tsconfig.json            # TypeScript config
└── package.json             # Dependencies
```

## Features

### 1. Lender Policy Management (`/lenders`)

**Upload Form:**
- Lender name input (required)
- Created by input (optional)
- PDF file upload with drag & drop
- File validation (PDF only)
- Real-time upload progress

**Lender List:**
- Paginated table view
- Status filtering (uploaded, processing, completed, failed)
- Auto-refresh every 5 seconds
- Columns:
  - Lender Name
  - Document filename
  - Status badge
  - Processing time
  - Created timestamp
  - Actions (view, delete)

**Detail Modal:**
- Full lender information
- Processing status
- Processed data (JSON view)

### 2. Loan Application Management (`/loan-applications`)

**Upload Form:**
- Applicant name (required)
- Email (optional)
- Phone (optional)
- Created by (optional)
- PDF file upload with drag & drop

**Application List:**
- Paginated table view
- Status filtering
- Auto-refresh every 5 seconds
- Columns:
  - Applicant name & email
  - Document filename
  - Status badge
  - Processing time
  - Created timestamp
  - Actions (view, delete)

**Detail Modal:**
- Full application information
- Contact details
- Match results with lenders
  - Match scores (0-100)
  - Match analysis
  - Sorted by score (highest first)
- Processed data (JSON view)

## Components

### Layout Component

Provides consistent page structure:
- Header with navigation
- Active route highlighting
- Responsive design
- Footer

### FileUpload Component

Drag & drop file upload:
- Click or drag to upload
- File type validation
- File preview with size
- Clear/remove functionality
- Disabled state support

### StatusBadge Component

Color-coded status indicators:
- 🔵 **Uploaded** - Blue badge
- 🟡 **Processing** - Yellow badge
- 🟢 **Completed** - Green badge
- 🔴 **Failed** - Red badge

### LoadingSpinner Component

Animated loading indicator:
- Three sizes: sm, md, lg
- Primary color theme
- Centered by default

### ErrorMessage Component

Error display with retry:
- Red alert styling
- Error icon
- Optional retry button
- Clear error message

## API Integration

### Configuration

API base URL is configured via environment variable:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### API Client

The `api.ts` service provides typed methods for all backend endpoints:

**Lender API:**
- `lenderApi.list()` - Get all lenders
- `lenderApi.get(id)` - Get single lender
- `lenderApi.upload(data)` - Upload PDF
- `lenderApi.delete(id)` - Delete lender

**Loan Application API:**
- `loanApplicationApi.list()` - Get all applications
- `loanApplicationApi.get(id)` - Get single application
- `loanApplicationApi.upload(data)` - Upload PDF
- `loanApplicationApi.getMatches(id)` - Get matches
- `loanApplicationApi.delete(id)` - Delete application

### Error Handling

Centralized error handling:
- Axios error parsing
- User-friendly error messages
- Retry functionality
- Toast notifications (future enhancement)

## State Management

### TanStack Query (React Query)

Used for server state management:

**Benefits:**
- Automatic caching
- Background refetching
- Optimistic updates
- Loading/error states
- Automatic retries

**Configuration:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000, // 30 seconds
    },
  },
});
```

**Query Keys:**
- `['lenders', statusFilter]` - Lender list
- `['lenders', id]` - Single lender
- `['loanApplications', statusFilter]` - Application list
- `['loanApplications', id]` - Single application

### Local State

React hooks for UI state:
- Form inputs
- Modal visibility
- File selection
- Error messages

## Styling

### Tailwind CSS

Utility-first CSS framework:

**Custom Theme:**
```javascript
theme: {
  extend: {
    colors: {
      primary: {
        50: '#f0f9ff',
        // ... full color scale
        900: '#0c4a6e',
      },
    },
  },
}
```

**Custom Components:**
- `.btn-primary` - Primary button
- `.btn-secondary` - Secondary button
- `.card` - Card container
- `.input` - Form input
- `.label` - Form label
- `.badge` - Status badge

### Responsive Design

Mobile-first approach:
- Breakpoints: sm, md, lg, xl, 2xl
- Responsive grid layouts
- Mobile-optimized tables
- Touch-friendly buttons

## Development

### Getting Started

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Development Server

Vite dev server features:
- Hot Module Replacement (HMR)
- Fast refresh
- Instant server start
- Optimized dependencies

### Type Checking

TypeScript strict mode enabled:
- Type safety
- IntelliSense support
- Compile-time error detection

### Code Quality

ESLint configuration:
- React hooks rules
- TypeScript rules
- Import sorting
- Code style enforcement

## Performance

### Optimizations

1. **Code Splitting**
   - Route-based splitting
   - Lazy loading components

2. **Caching**
   - React Query caching
   - Browser caching
   - Service worker (future)

3. **Bundle Size**
   - Tree shaking
   - Minification
   - Gzip compression

4. **Rendering**
   - React.memo for components
   - useMemo/useCallback hooks
   - Virtual scrolling (future)

### Monitoring

Future enhancements:
- Performance metrics
- Error tracking (Sentry)
- Analytics (Google Analytics)
- User behavior tracking

## Deployment

### Build Process

```bash
npm run build
```

Outputs to `dist/` directory:
- Minified JavaScript
- Optimized CSS
- Static assets
- HTML files

### Hosting Options

**Static Hosting:**
- Vercel (recommended)
- Netlify
- AWS S3 + CloudFront
- GitHub Pages
- Azure Static Web Apps

**Configuration:**

For Vercel:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

### Environment Variables

Production environment:
```env
VITE_API_BASE_URL=https://api.kaaj.com
```

## Testing

### Future Testing Strategy

1. **Unit Tests**
   - Component testing with React Testing Library
   - Hook testing
   - Utility function testing

2. **Integration Tests**
   - API integration tests
   - Form submission tests
   - Navigation tests

3. **E2E Tests**
   - Playwright or Cypress
   - User flow testing
   - Cross-browser testing

## Accessibility

### Current Features

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus management

### Future Enhancements

- Screen reader testing
- WCAG 2.1 AA compliance
- High contrast mode
- Reduced motion support

## Browser Support

**Supported Browsers:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Mobile:**
- iOS Safari 12+
- Chrome Android (latest)

## Future Enhancements

### Planned Features

1. **User Authentication**
   - Login/logout
   - Role-based access
   - JWT tokens

2. **Advanced Filtering**
   - Date range filters
   - Search functionality
   - Saved filters

3. **Batch Operations**
   - Bulk upload
   - Bulk delete
   - Export data

4. **Notifications**
   - Toast notifications
   - Email notifications
   - Push notifications

5. **Dashboard**
   - Statistics
   - Charts and graphs
   - Recent activity

6. **Dark Mode**
   - Theme toggle
   - System preference detection
   - Persistent preference

7. **Internationalization**
   - Multi-language support
   - Date/time localization
   - Currency formatting

## Troubleshooting

### Common Issues

**1. API Connection Failed**
- Check backend is running
- Verify API URL in `.env`
- Check CORS configuration

**2. File Upload Failed**
- Verify file is PDF
- Check file size limits
- Ensure backend is accessible

**3. Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear cache: `rm -rf .vite`
- Update dependencies: `npm update`

**4. TypeScript Errors**
- Run type check: `npm run type-check`
- Update type definitions
- Check tsconfig.json

## Contributing

### Code Style

- Use TypeScript for all new code
- Follow ESLint rules
- Use functional components
- Prefer hooks over classes
- Write descriptive comments

### Git Workflow

1. Create feature branch
2. Make changes
3. Run linter: `npm run lint`
4. Test locally
5. Commit with descriptive message
6. Create pull request

## Support

For issues or questions:
- Check documentation
- Review error logs
- Contact development team

## License

Copyright © 2025 Kaaj. All rights reserved.

