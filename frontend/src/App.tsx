import React from 'react';
import { BotSelector } from './components/BotSelector/BotSelector';
import { BotDetails } from './components/BotDetails/BotDetails';
import { useBots } from './hooks/useBots';
import { Bot } from './services/api';

function App() {
  const { bots, loading, error } = useBots();
  const [selectedBotId, setSelectedBotId] = React.useState('');

  const selectedBot = bots.find(bot => bot.id === selectedBotId);

  return (
    <div className="app">
      <h1>RPA Bot Dashboard</h1>
      <BotSelector 
        bots={bots} 
        selectedBotId={selectedBotId} 
        onBotSelect={setSelectedBotId} 
      />
      {selectedBot && <BotDetails bot={selectedBot} />}
    </div>
  );
}

export default App;