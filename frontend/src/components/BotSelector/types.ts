import { Bot } from "../../services/api";

export interface BotSelectorProps {
    bots: Bot[];
    selectedBotId?: string;
    onBotSelect: (bot: Bot | null) => void;
    onNewBot: () => void;
}