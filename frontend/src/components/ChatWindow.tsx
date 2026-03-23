import { useState } from 'react';
import { streamChat } from '../api/conversations';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface Step {
  step: number;
  agent_name: string;
}

export default function ChatWindow({ conversationId, onNewMessage }: { conversationId: string; onNewMessage: () => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStep, setCurrentStep] = useState<Step | null>(null);
  const [currentResponse, setCurrentResponse] = useState('');

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = input;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsStreaming(true);
    setCurrentResponse('');
    setCurrentStep(null);

    let assistantMessage = '';
    const unsubscribe = streamChat(conversationId, userMessage, (event) => {
      if (event.event === 'token') {
        const token = event.data.text;
        assistantMessage += token;
        setCurrentResponse(assistantMessage);
      } else if (event.event === 'step_start') {
        setCurrentStep({ step: event.data.step, agent_name: event.data.agent_name });
      } else if (event.event === 'step_end') {
        setCurrentStep(null);
      } else if (event.event === 'done') {
        setIsStreaming(false);
        setMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }]);
        setCurrentResponse('');
        onNewMessage();
      } else if (event.event === 'error') {
        setIsStreaming(false);
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${event.data.error}` }]);
        setCurrentResponse('');
      }
    });

    return unsubscribe;
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-lg px-4 py-2 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-900'
            }`}>
              <div className="text-sm font-medium mb-1 capitalize">{msg.role}</div>
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
        {isStreaming && currentStep && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-2">
            <div className="text-sm font-medium text-purple-700">
              Step {currentStep.step}: {currentStep.agent_name}
            </div>
          </div>
        )}
        {isStreaming && currentResponse && (
          <div className="flex justify-start">
            <div className="max-w-2xl rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
              <div className="text-sm font-medium mb-1">Assistant</div>
              <div className="whitespace-pre-wrap">{currentResponse}</div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 border rounded-lg px-4 py-2 text-sm"
            placeholder="Type your message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && handleSend()}
            disabled={isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 text-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
