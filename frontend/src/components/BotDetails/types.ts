import { Bot } from "../../services/api";

export interface BotDetailsProps {
    bot: Bot | null;
    isNewBot: boolean;
    botName: string;
    instruction: string;
    successCriteria: string;
    onBotNameChange: (value: string) => void;
    onInstructionChange: (value: string) => void;
    onSuccessCriteriaChange: (value: string) => void;
    onGenerateScript: (name: string, instruction: string, successCriteria: string) => void;
}