import React from "react";
import { BotSelectorProps } from "./types";

export const BotSelector: React.FC<BotSelectorProps> = ({ bots, selectedBotId, onBotSelect }) => {
    return (
        <div>
            <label htmlFor="botSelector">Select a bot:</label>
            <select id="botSelector" value={selectedBotId} onChange={(e) => onBotSelect(e.target.value)}>
            {bots.length === 0 && <option value="">No bots available</option>}
            {bots.length > 0 && bots.map((bot) => (
                <option key={bot.id} value={bot.id}>
                    {bot.name}
                </option>
            ))}
            </select>
        </div>
    );
};