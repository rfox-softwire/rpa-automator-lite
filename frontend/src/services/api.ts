import axios, { AxiosError } from 'axios';

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
        console.log('Bots API Response:', response.data);
        return response.data;
    } catch (error) {
        console.error("Error fetching bots:", error);
        throw error;
    }
}

export const generateBotScript = async (botName: string, instruction: string, successCriteria: string): Promise<Bot> => {
    try {
        const createResponse = await api.post('/bots', {
            name: botName.trim(),
            instruction: instruction.trim(),
            success_criteria: successCriteria.trim()
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        const botId = createResponse.data.id;
        let bot = createResponse.data;

        while (bot.status === 'pending' || bot.status === 'processing') {
            await new Promise(resolve => setTimeout(resolve, 100));
            const response = await api.get(`/bots/${botId}`);
            bot = response.data;
        }

         if (bot.status === 'error') {
            throw new Error(bot.error || 'Error generating script');
        }

        return bot;
    } catch (error) {
        console.error("Error creating bot and generating script:", error);
        if (axios.isAxiosError(error)) {
            console.error("Response data:", error.response?.data);
            console.error("Status:", error.response?.status);
        }
        throw error;
    }
}

export const runBotScript = async (botId: string): Promise<{
    status: string;
    exit_code?: number;
    stdout?: string;
    stderr?: string;
    message?: string;
}> => {
    try {
        const response = await api.post(`/bots/${botId}/run`);
        return response.data;
    } catch (error) {
        console.error("Error running bot script:", error);
        throw error;
    }
};