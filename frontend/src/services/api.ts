import axios from 'axios';

export interface Bot {
    id: string;
    name: string;
    instruction: string;
    success_criteria: string;
    scriptUnmodified: string;
    script: string;
    status: string;
    error?: string;
}

const API_BASE_URL = "http://localhost:8000/api";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    }
})

export const fetchBots = async (): Promise<Bot[]> => {
    try {
        const response = await api.get("/bots");
        return response.data;
    } catch (error) {
        console.error("Error fetching bots:", error);
        throw error;
    }
}