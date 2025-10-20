import React, { useState } from "react";
import { BotScriptProps } from "./types";
import { runBotScript } from "../../services/api";

export const BotScript: React.FC<BotScriptProps> = ({
    botScript,
    isNewBot,
    botId,
    onRunScript,
    isRunning,
    isRepairing
}) => {
    const handleRunClick = async () => {
        if (!botId) return;
        await onRunScript(botId);
    };

    return (
         <div className="flex-1 min-w-[300px] bg-white shadow overflow-hidden sm:rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-gray-900">Generated Script</h2>
                {!isRepairing && botScript && (
                    <button
                        onClick={handleRunClick}
                        disabled={isRunning || isRepairing}
                        className={`px-4 py-2 rounded-md text-sm ${
                            isRunning || isRepairing
                                ? 'bg-gray-400 cursor-not-allowed' 
                                : 'bg-blue-600 hover:bg-blue-700 text-white'
                        }`}
                    >
                        {isRunning ? 'Running...' : 'Run Script'}
                    </button>
                )}
            </div>
            <div key={`script-${botScript?.substring(0, 20)}`} className="bg-gray-50 p-4 rounded-md font-mono text-sm h-full overflow-auto">
                {!isNewBot && (
                    <pre className="whitespace-pre-wrap">
                        {isRepairing && 'Script is being repaired...'}
                        {!isRepairing && botScript}
                    </pre>
                )}
                {isNewBot && (
                    <p className="text-gray-500">Click "Generate Script" to create a new script</p>
                )}
            </div>
        </div>
    )
};