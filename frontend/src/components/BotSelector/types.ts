import { Bot } from "../../services/api";

export interface BotSelectorProps {
    bots: Bot[];
    selectedBotId: string;
    onBotSelect: (botId: string) => void;
}