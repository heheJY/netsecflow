// src/services/api.js
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export const fetchTopology = async () => {
    try {
        const response = await axios.get(`${API_URL}/topology`);
        return response.data;
    } catch (error) {
        console.error('Error fetching topology:', error);
        throw error;
    }
};
