# Frontend Documentation

## Overview
The frontend is a React 18 application with Vite, Tailwind CSS, and React Router. It connects to the Flask backend API to display car listings.

## Technology Stack
- **Framework**: React 18.3
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 4
- **Routing**: React Router DOM 7
- **Icons**: Lucide React

## Project Structure

```
FRONT-END/
├── src/
│   ├── api/
│   │   └── carApi.js         # API client functions
│   │
│   ├── components/
│   │   ├── CarCards.jsx      # Car and Brand card components
│   │   ├── FilterPanel.jsx   # Search/filter panel
│   │   ├── Navbar.jsx        # Navigation bar
│   │   ├── ChatbotWidget.jsx # AI chatbot
│   │   └── ProtectedRoute.jsx
│   │
│   ├── pages/
│   │   ├── Marketplace.jsx   # Main marketplace page
│   │   ├── Login.jsx         # Login page
│   │   ├── Profile.jsx       # User profile
│   │   ├── SellCar.jsx       # Sell car page
│   │   ├── AIFeatures.jsx    # AI features page
│   │   └── Settings.jsx      # Settings page
│   │
│   ├── context/
│   │   ├── AuthContext.jsx   # Authentication state
│   │   └── ThemeContext.jsx  # Dark/light theme
│   │
│   ├── hooks/
│   │   └── utils.js          # Utility functions
│   │
│   ├── data/
│   │   └── mockData.js       # Mock data (fallback)
│   │
│   ├── App.jsx               # Main app component
│   └── main.jsx              # Entry point
│
├── public/                   # Static assets
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── index.html
```

## API Integration

### API Client (`src/api/carApi.js`)

```javascript
// Fetch paginated car list
const data = await fetchCars(page, limit);

// Fetch single car
const car = await fetchCar(id);

// Search/filter cars
const results = await searchCars({ brand: 'Toyota', min_price: 100000 });

// Fetch all brands
const { brands } = await fetchBrands();
```

### Base URL
```
http://localhost:5000/api
```

## Key Components

### CarCard
Displays individual car listing with:
- Image
- Brand, model, year
- Price
- Fuel type, transmission
- Description (AI insight)
- Action buttons

### BrandCard
Displays brand logo for filtering

### FilterPanel
Search/filter interface with:
- Brand selection
- Price range
- Year range
- And more...

### Marketplace Page
Main page that:
- Fetches cars from API on load
- Displays loading state
- Handles pagination
- Shows error states

## Running the Frontend

### Development
```bash
cd FRONT-END
npm run dev
```

Starts at `http://localhost:5173`

### Build for Production
```bash
cd FRONT-END
npm run build
```

Output in `FRONT-END/dist/`

### Linting
```bash
cd FRONT-END
npm run lint
```

## Environment Variables

No frontend environment variables needed. The API URL is hardcoded in `src/api/carApi.js`:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

To change, edit this line in `carApi.js`.

## State Management

- **AuthContext**: User authentication state
- **ThemeContext**: Dark/light mode
- **Local state**: Page, loading, error states in components

## Adding New Pages

1. Create component in `src/pages/`
2. Add route in `App.jsx`
3. Add navigation in `Navbar.jsx`

## Styling

Uses Tailwind CSS with custom configuration. Key classes:
- `ai-gradient` - Custom gradient
- `glass` - Glass morphism effect
- `ai-text-gradient` - Text gradient
- Dark mode via `dark:` prefix

## Troubleshooting

### CORS Issues
If frontend can't reach backend, ensure Flask has CORS enabled (already configured in `Backend/app.py`).

### API Connection Failed
Check that:
1. Backend is running on port 5000
2. Database has data (`python -m pytest Backend/test_supabase.py`)
3. Connection string in `.env` is correct

### Build Errors
```bash
npm install
npm run build
```