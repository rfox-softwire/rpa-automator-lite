import React from "react";
import { BotDetailsProps } from "./types";

export const BotDetails: React.FC<BotDetailsProps> = ({ bot }) => {
    if (!bot) {
        return <div>Select a bot to view details</div>
    }

    const detailItem = (label: string, value: string | undefined) => {
        if (!value) {
            return null;
        }
        return (
            <div className = "detail-item">
                <div className="detail-label">{label}</div>
                <div className="detail-value">
                    {value}
                </div>
            </div>
        );
    }

    return (
        <div className = "bot-details">
            <h2>Bot Details</h2>
            {detailItem("Name", bot.name)}
            {detailItem("Instruction", bot.instruction)}
            {detailItem("Success Criteria", bot.success_criteria)}
            {detailItem("Status", bot.status)}
        </div>
    );
};