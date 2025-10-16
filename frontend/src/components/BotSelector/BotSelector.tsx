import React from "react";
import { BotSelectorProps } from "./types";

export const BotSelector: React.FC<BotSelectorProps> = ({ 
    bots, 
    selectedBotId, 
    onBotSelect,
}) => {
    return (
        <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 items-center">
                <div className="w-full">
                    <label htmlFor="botSelector" className="block text-sm font-medium text-gray-700 mb-1">
                        Select a bot
                    </label>
                    <select
                        id="botSelector"
                        value={selectedBotId || ''}
                        onChange={(e) => {
                            const selected = bots.find(bot => bot.id === e.target.value) || null;
                            onBotSelect(selected);
                        }}
                        className="w-full border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        <option value="">Select a bot...</option>
                        {bots.map((bot) => (
                            <option key={bot.id} value={bot.id}>
                                {bot.name}
                            </option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
};