export interface ScriptOutputProps {
    botId: string | undefined;
    output: string;
    error: string;
    isRunning: boolean;
    onRepair: (botId: string) => void;
}