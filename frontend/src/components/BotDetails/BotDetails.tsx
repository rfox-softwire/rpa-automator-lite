import React from "react";
import { BotDetailsProps } from "./types";

export const BotDetails: React.FC<BotDetailsProps> = ({
    bot,
    isNewBot,
    botName,
    instruction,
    successCriteria,
    onBotNameChange,
    onInstructionChange,
    onSuccessCriteriaChange,
    onGenerateScript
}) => {
    
    const [isGenerating, setIsGenerating] = React.useState(false);

    const handleGenerateClick = async () => {
        if (!botName || !instruction || !successCriteria) return;
        try {
            setIsGenerating(true);
            await onGenerateScript(botName, instruction, successCriteria);
        } catch (error) {
            console.error('Error generating script:', error);
        } finally {
            setIsGenerating(false);
        }
    };

    return (
         <div className="flex-1 min-w-[300px] bg-white shadow overflow-hidden sm:rounded-lg p-6">
            <h2 className='text-lg font-medium text-gray-900 mb-4'>
                {isNewBot ? "New Bot" : "Bot Details"}
            </h2>
            <div className='space-y-4'>
                <label className='block text-sm font-medium text-gray-700 mb-1'>Bot name</label>
                {isNewBot && (
                    <input
                        className="w-full border border-gray-300 rounded-md p-2"
                        value={botName}
                        onChange={(e) => onBotNameChange(e.target.value)}
                        placeholder='Enter bot name'
                    />
                )}
                {!isNewBot && (
                    <div className='p-2 bg-gray-100 rounded-md'>
                        {bot?.name}
                    </div>
                )}
            </div>
            <div className='space-y-4 mt-4'>
                <label className='block text-sm font-medium text-gray-700 mb-1'>Instructions</label>
                {isNewBot && (
                    <textarea
                        className="w-full border border-gray-300 rounded-md p-2 h-32"
                        value={instruction}
                        onChange={(e) => onInstructionChange(e.target.value)}
                        placeholder='Enter bot instruction'
                    />
                )}
                {!isNewBot && (
                    <div className='p-2 bg-gray-100 rounded-md min-h-32'>
                        {bot?.instruction}
                    </div>
                )}
            </div>
            <div className='space-y-4 mt-4'>
                <label className='block text-sm font-medium text-gray-700 mb-1'>Success Criteria</label>
                {isNewBot && (
                    <textarea
                        className="w-full border border-gray-300 rounded-md p-2 h-32"
                        value={successCriteria}
                        onChange={(e) => onSuccessCriteriaChange(e.target.value)}
                        placeholder='Enter bot success criteria'
                    />
                )}
                {!isNewBot && (
                    <div className='p-2 bg-gray-100 rounded-md min-h-32'>
                        {bot?.success_criteria}
                    </div>
                )}
            </div>
            {isNewBot && (
                <div className="mt-4">
                    <button
                        onClick={handleGenerateClick}
                        disabled={!botName || !instruction || !successCriteria || isGenerating}
                        className={`w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors ${
                            (!botName || !instruction || !successCriteria || isGenerating) 
                                ? 'opacity-50 cursor-not-allowed' 
                                : ''
                        }`}
                    >
                        {isGenerating ? 'Generating Script...' : 'Generate Script'}
                    </button>
                </div>
            )}
        </div>
    )
};