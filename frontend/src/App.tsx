import React from 'react';
import { BotSelector } from './components/BotSelector/BotSelector';
import { BotDetails } from './components/BotDetails/BotDetails';
import { BotScript } from './components/BotScript/BotScript';

import { useBots } from './hooks/useBots';
import { Bot, generateBotScript } from './services/api';

function App() {
    const [selectedBot, setSelectedBot] = React.useState<Bot | null>(null);
    const [isNewBot, setIsNewBot] = React.useState(false);
    const [instruction, setInstruction] = React.useState('');
    const [successCriteria, setSuccessCriteria] = React.useState('');
    const [botName, setBotName] = React.useState('');
    const [botScript, setBotScript] = React.useState('');

    const bots = useBots();

    const handleBotSelect = (bot: Bot | null) => {
        console.log('Selected bot:', bot);
        setSelectedBot(bot);
        setIsNewBot(false);
        if (bot) {
            setBotName(bot.name);
            setInstruction(bot.instruction);
            setSuccessCriteria(bot.success_criteria);
            setBotScript(bot.scriptUnmodified);
        }
    };

    const handleGenerateScript = async (name: string, instruction: string, successCriteria: string) => {
        try {
            const newBot = await generateBotScript(name, instruction, successCriteria);
            setSelectedBot(newBot);
            setBotName(newBot.name);
            setInstruction(newBot.instruction);
            setSuccessCriteria(newBot.success_criteria);
            setBotScript(newBot.scriptUnmodified);
            setIsNewBot(false);
            return newBot;
        } catch (error) {
            console.error('Error generating script:', error);
            throw error;
        }
    };

    return (
        <div className='min-h-screen bg-gray-50'>
            <header className='bg-white shadow'>
                <div className='max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8'>
                    <h1 className='text-2xl font-bold leading-9 tracking-tight text-gray-900'>RPA Bot Dashboard</h1>
                </div>
            </header>
            <main className='max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8'>
                <div className='bg-white shadow overflow-hidden sm:rounded-lg mb-8 p-6'>
                    <div className="flex flex-col sm:flex-row items-center gap-4">
                        <div className="flex-1 w-full sm:w-auto">
                        <BotSelector 
                            bots={bots} 
                            onBotSelect={handleBotSelect} 
                            onNewBot={() => {
                            setIsNewBot(true);
                            setSelectedBot(null);
                            setInstruction("");
                            setSuccessCriteria("");
                            }}
                        />
                        </div>
                        <div className="text-gray-500">Or</div>
                        <button
                        className='bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded whitespace-nowrap'
                        onClick={() => {
                            setIsNewBot(true);
                            setSelectedBot(null);
                            setInstruction("");
                            setSuccessCriteria("");
                            setBotName("");
                            setBotScript("");
                        }}
                        >
                        Create New Bot
                        </button>
                    </div>
                </div>

                <div className='flex flex-col md:flex-row flex-wrap gap-4'>
                    <BotDetails 
                        bot={selectedBot} 
                        isNewBot={isNewBot}
                        botName={botName}
                        instruction={instruction}
                        successCriteria={successCriteria}
                        onBotNameChange={setBotName}
                        onInstructionChange={setInstruction}
                        onSuccessCriteriaChange={setSuccessCriteria}
                        onGenerateScript={handleGenerateScript}
                    />

                    <BotScript 
                        botScript={botScript}
                        onBotScriptChange={setBotScript}
                        isNewBot={isNewBot}
                    />
                    
                    <div className="flex-1 min-w-[300px] bg-white shadow overflow-hidden sm:rounded-lg p-6">
                        <h2 className="text-lg font-medium text-gray-900 mb-4">Preview</h2>
                        <div className="bg-gray-50 p-4 rounded-md h-64 flex items-center justify-center text-gray-400">
                            Preview panel
                        </div>
                    </div>                    
                </div>            
            </main>
        </div>
    )

}

export default App;