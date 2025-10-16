import { useState, useEffect } from 'react';
import { Bot, fetchBots } from '../services/api';

export const useBots = () => {
    const [bots, setBots] = useState<Bot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchBotsData = async () => {
            try {
                setLoading(true);
                const botsData = await fetchBots();
                setBots(botsData);
            } catch (error) {
                setError(error as string);
            } finally {
                setLoading(false);
            }
        }
        fetchBotsData();
    }, []);

    return bots;
}