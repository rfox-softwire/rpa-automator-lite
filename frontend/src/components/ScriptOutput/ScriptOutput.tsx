import React from "react";
import { ScriptOutputProps } from "./types";

export const ScriptOutput: React.FC<ScriptOutputProps> = ({ output, error, isRunning }) => {
    if (isRunning) {
        return (
            <div className="mt-4 space-y-4">
                <div>
                    <h3 className="font-medium text-gray-900 mb-2">Loading...</h3>
                </div>
            </div>
        );
    }

    return (
        <div className="mt-4 space-y-4">
            {output && (
                <div>
                    <h3 className="font-medium text-gray-900 mb-2">Output:</h3>
                    <pre className="bg-gray-100 p-3 rounded-md overflow-auto max-h-40">
                        {output}
                    </pre>
                </div>
            )}
            {error && (
                <div>
                    <h3 className="font-medium text-red-700 mb-2">Error:</h3>
                    <pre className="bg-red-50 text-red-700 p-3 rounded-md overflow-auto max-h-40">
                        {error}
                    </pre>
                </div>
            )}
        </div>
    );
};