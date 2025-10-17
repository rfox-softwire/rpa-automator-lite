export interface BotScriptProps {
    botScript: string;
    isNewBot: boolean;
    botId: string | undefined;
    onRunScript: (botId: string) => Promise<void>;
    isRunning: boolean;
    isRepairing: boolean;
}