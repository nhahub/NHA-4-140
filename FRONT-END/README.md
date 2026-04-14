# 🚗 Gencarz - Modern Car Marketplace

Gencarz is a state-of-the-art car marketplace web application built with React and Vite. It offers a premium user experience for browsing, buying, and selling cars, enhanced with AI-powered features.

## ✨ Features

- **🛍️ Marketplace**: Browse a wide selection of cars with advanced filtering.
- **🤖 AI Features**: Leverage AI for car analysis and personalized recommendations.
- **🏷️ Sell Your Car**: Easy-to-use interface for listing your vehicle for sale.
- **👤 User Profiles**: Manage your account, favorites, and listings.
- **🎨 Premium Design**: Modern, responsive UI built with Tailwind CSS and Lucide icons.

## 🛠️ Tech Stack

- **Framework**: [React](https://reactjs.org/) + [Vite](https://vitejs.dev/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Routing**: [React Router DOM](https://reactrouter.com/)

## API Integration

This frontend connects to a Flask backend API at `http://localhost:5000/api`.

### API Client (`src/api/carApi.js`)

```javascript
import { fetchCars, fetchCar, searchCars, fetchBrands } from './api/carApi';

// Fetch paginated car list
const data = await fetchCars(page, limit);

// Search/filter cars
const results = await searchCars({ brand: 'Toyota', min_price: 100000 });

// Fetch all brands
const { brands } = await fetchBrands();
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cars` | Get all cars with pagination |
| GET | `/api/cars/<id>` | Get single car by ID |
| GET | `/api/cars/search` | Search/filter cars |
| GET | `/api/cars/brands` | Get all unique brands |

## Project Structure

```
FRONT-END/
├── src/
│   ├── api/
│   │   └── carApi.js         # API client functions
│   ├── components/
│   │   ├── CarCards.jsx      # Car and Brand card components
│   │   ├── FilterPanel.jsx   # Search/filter panel
│   │   ├── Navbar.jsx        # Navigation bar
│   │   └── ...
│   ├── pages/
│   │   ├── Marketplace.jsx   # Main marketplace (connects to API)
│   │   ├── Login.jsx
│   │   └── ...
│   ├── context/
│   │   ├── AuthContext.jsx
│   │   └── ThemeContext.jsx
│   └── data/
│       └── mockData.js       # Fallback mock data
├── package.json
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

### Running Locally

```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

### Building for Production

```bash
npm run build
```

### Linting

```bash
npm run lint
```

## Environment Variables

No frontend environment variables needed. The API URL is configured in `src/api/carApi.js`:
```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

## Troubleshooting

### CORS Issues
If frontend can't reach backend, ensure Flask has CORS enabled (configured in Backend/app.py).

### API Connection Failed
Check that:
1. Backend is running on port 5000
2. Database has data (`python -m pytest Backend/test_supabase.py`)
3. Connection string in `.env` is correct

## 📝 License

This project is part of the DEPI Final Project.