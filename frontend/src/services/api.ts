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

        while (bot.status === 'pending') {
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

export const getBotOutputs = async (botId: string): Promise<{
    output: string;
    error: string;
}> => {
    try {
        const response = await api.get(`/bots/${botId}/outputs`);
        return response.data;
    } catch (error) {
        console.error("Error fetching bot outputs:", error);
        throw error;
    }
};

export const repairBotScript = async (botId: string): Promise<Bot> => {
    try {
        console.log(`Attempting to repair bot ${botId}...`);
        const response = await api.post(`/bots/${botId}/repair`, {}, {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
        console.log('Repair request initiated, response:', response.data);
        
        const bot = await pollBotStatus(botId);
        if (bot?.status !== 'ready') {
            throw new Error(bot?.error || "Repair failed");
        }
        
        return bot;
    } catch (error) {
        console.error("Error repairing bot script:", error);
        if (axios.isAxiosError(error)) {
            console.error('Response data:', error.response?.data);
            console.error('Status code:', error.response?.status);
            console.error('Headers:', error.response?.headers);
        }
        throw error;
    }
};

export const pollBotStatus = async (botId: string, maxAttempts: number = 1200, interval: number = 1000): Promise<Bot | null> => {
    let attempts = 0;
    let bot: Bot | null = null;
    
    while (attempts < maxAttempts) {
        try {
            const response = await api.get(`/bots/${botId}`);
            bot = response.data;
            
            if (bot?.status !== 'pending') {
                return bot;
            }
            
            await new Promise(resolve => setTimeout(resolve, interval));
            attempts++;
        } catch (error) {
            console.error(`Error polling bot status (attempt ${attempts + 1}):`, error);
            throw error;
        }
    }
    
    return null;
};