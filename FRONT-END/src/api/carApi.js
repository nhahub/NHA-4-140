const API_BASE_URL = 'http://localhost:5000/api';

export const fetchCars = async (page = 1, limit = 20) => {
  const response = await fetch(`${API_BASE_URL}/cars?page=${page}&limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch cars');
  return response.json();
};

export const fetchCar = async (id) => {
  const response = await fetch(`${API_BASE_URL}/cars/${id}`);
  if (!response.ok) throw new Error('Failed to fetch car');
  return response.json();
};

export const searchCars = async (params) => {
  const queryParams = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/cars/search?${queryParams}`);
  if (!response.ok) throw new Error('Failed to search cars');
  return response.json();
};

export const fetchBrands = async () => {
  const response = await fetch(`${API_BASE_URL}/cars/brands`);
  if (!response.ok) throw new Error('Failed to fetch brands');
  return response.json();
};