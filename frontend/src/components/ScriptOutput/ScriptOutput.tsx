import React from "react";
import { ScriptOutputProps } from "./types";

export const ScriptOutput: React.FC<ScriptOutputProps> = ({ output, error, botId, isRunning, onRepair }) => {
    if (isRunning) {
        return (
            <div className="space-y-4">
                <div>
                    <h3 className="font-medium text-gray-900 mb-2">Loading...</h3>
                </div>
            </div>
        );
    }

    const handleRepairClick = async () => {
        if (!botId) return;
        await onRepair(botId);
    };

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-medium text-gray-900">Script Output</h2>
                {error && !isRunning && (
                    <button
                        onClick={handleRepairClick}
                        className="px-4 py-2 text-sm bg-yellow-500 hover:bg-yellow-600 text-white rounded-md transition-colors"
                    >
                        Repair Script
                    </button>
                )}
            </div>
            {output && (
                <div>
                    <h3 className="font-medium text-gray-900 mb-2">Output:</h3>
                    <pre className="bg-gray-100 p-3 rounded-md overflow-auto max-h-40">
                        {output}
                    </pre>
                </div>
            )}
            {error && (
                <div className="space-y-2">
                    <h3 className="font-medium text-red-700 mb-2">Error:</h3>
                    <pre className="bg-red-50 text-red-700 p-3 rounded-md overflow-auto max-h-40">
                        {error}
                    </pre>
                </div>
            )}
        </div>
    );
};