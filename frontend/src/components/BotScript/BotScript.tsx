import React from "react";

import { BotScriptProps } from "./types";

export const BotScript: React.FC<BotScriptProps> = ({
    botScript,
    onBotScriptChange,
    isNewBot
}) => {

    return (
         <div className="flex-1 min-w-[300px] bg-white shadow overflow-hidden sm:rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Generated Script</h2>
            <div key={`script-${botScript?.substring(0, 20)}`} className="bg-gray-50 p-4 rounded-md font-mono text-sm h-full overflow-auto">
                {!isNewBot && (
                <pre className="whitespace-pre-wrap">
                    {botScript}
                </pre>
                )}
                {isNewBot && (
                <p className="text-gray-500">Click "Generate Script" to create a new script</p>
                )}
            </div>
        </div>
    )
};