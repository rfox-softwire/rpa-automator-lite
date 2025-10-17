import React, { useState } from "react";
import { BotScriptProps } from "./types";
import { runBotScript } from "../../services/api";

export const BotScript: React.FC<BotScriptProps> = ({
    botScript,
    isNewBot,
    botId
}) => {
    const [isRunning, setIsRunning] = useState(false);

    const handleRunScript = async () => {
        if (!botId) return;
        
        setIsRunning(true);
        
        try {
            await runBotScript(botId);
        } catch (error) {
            console.error("Error running script:", error);
        } finally {
            setIsRunning(false);
        }
    };

    return (
         <div className="flex-1 min-w-[300px] bg-white shadow overflow-hidden sm:rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Generated Script</h2>
            <div key={`script-${botScript?.substring(0, 20)}`} className="bg-gray-50 p-4 rounded-md font-mono text-sm h-full overflow-auto">
                {!isNewBot && (
                    <pre className="whitespace-pre-wrap">
                        {botScript}
                    </pre>
                )}
                {botScript && (
                    <div className="mt-4">
                        <button
                            onClick={handleRunScript}
                            disabled={isRunning}
                            className={`px-4 py-2 rounded-md ${
                                isRunning 
                                    ? 'bg-gray-400 cursor-not-allowed' 
                                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                            }`}
                        >
                            {isRunning ? 'Running...' : 'Run Script'}
                        </button>
                    </div>
                )}
                {isNewBot && (
                    <p className="text-gray-500">Click "Generate Script" to create a new script</p>
                )}
            </div>
        </div>
    )
};