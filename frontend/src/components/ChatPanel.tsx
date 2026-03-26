import { useState, useRef, useEffect } from 'react';
import { naturalLanguageSimulate } from '../api/client';
import type { ChatMessage, GateStep, SimulationResponse } from '../types/quantum';

interface Props {
  onCircuitGenerated: (nQubits: number, steps: GateStep[]) => void;
  onSimulationResult: (result: SimulationResponse) => void;
}

export default function ChatPanel({ onCircuitGenerated, onSimulationResult }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = input.trim();
    if (!prompt || loading) return;

    setInput('');
    const userMsg: ChatMessage = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const result = await naturalLanguageSimulate(prompt, sessionId);
      setSessionId(result.session_id);

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: result.explanation,
        circuit: result.circuit,
        simulation: result.simulation,
      };
      setMessages(prev => [...prev, assistantMsg]);

      // If circuit was generated, load it into the editor
      if (result.circuit) {
        onCircuitGenerated(result.circuit.n_qubits, result.circuit.steps);
      }

      // If simulation ran, show results
      if (result.simulation) {
        onSimulationResult(result.simulation);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Request failed';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${errorMsg}. Make sure the backend is running and ANTHROPIC_API_KEY is set.`,
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const suggestions = [
    'Create a Bell state',
    'Make a 3-qubit GHZ state',
    'What is superposition?',
    'Build a quantum teleportation circuit',
    "Show me Grover's search for 2 qubits",
  ];

  return (
    <div
      className="flex flex-col rounded-lg overflow-hidden"
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        height: '100%',
        minHeight: '300px',
      }}
    >
      {/* Header */}
      <div
        className="px-3 py-2 flex items-center gap-2"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <span style={{ fontSize: '16px' }}>&#x1F9E0;</span>
        <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
          QuantumLens AI
        </span>
        <span className="text-xs ml-auto" style={{ color: 'var(--text-secondary)' }}>
          Powered by Claude
        </span>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 flex flex-col gap-3"
        style={{ minHeight: 0 }}
      >
        {messages.length === 0 && (
          <div className="flex flex-col gap-3 py-4">
            <p className="text-sm text-center" style={{ color: 'var(--text-secondary)' }}>
              Describe a quantum circuit in plain English and I'll build it for you.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); inputRef.current?.focus(); }}
                  className="px-3 py-1.5 rounded-full text-xs transition-colors cursor-pointer"
                  style={{
                    background: 'var(--bg-tertiary)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-secondary)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--accent)';
                    e.currentTarget.style.color = 'var(--accent)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border)';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className="max-w-[85%] px-3 py-2 rounded-lg text-sm"
              style={{
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)',
                color: msg.role === 'user' ? '#000' : 'var(--text-primary)',
                borderBottomRightRadius: msg.role === 'user' ? '4px' : undefined,
                borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : undefined,
              }}
            >
              {/* Message text */}
              <div className="whitespace-pre-wrap break-words leading-relaxed">
                {msg.content}
              </div>

              {/* Circuit badge */}
              {msg.circuit && (
                <div
                  className="mt-2 px-2 py-1 rounded text-xs inline-flex items-center gap-1"
                  style={{
                    background: 'var(--success)',
                    color: '#000',
                  }}
                >
                  <span>&#x2713;</span>
                  Circuit loaded ({msg.circuit.n_qubits} qubit{msg.circuit.n_qubits > 1 ? 's' : ''}, {msg.circuit.steps.length} gate{msg.circuit.steps.length > 1 ? 's' : ''})
                </div>
              )}

              {/* Simulation badge */}
              {msg.simulation && (
                <div
                  className="mt-1 px-2 py-1 rounded text-xs inline-flex items-center gap-1"
                  style={{
                    background: 'var(--accent)',
                    color: '#000',
                  }}
                >
                  <span>&#x26A1;</span>
                  Simulated — see results below
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div
              className="px-3 py-2 rounded-lg text-sm"
              style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
            >
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="p-2 flex gap-2"
        style={{ borderTop: '1px solid var(--border)' }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Describe a quantum circuit..."
          disabled={loading}
          className="flex-1 px-3 py-2 rounded text-sm outline-none"
          style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
          }}
          onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent)'; }}
          onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded text-sm font-bold transition-opacity cursor-pointer"
          style={{
            background: 'var(--accent)',
            color: '#000',
            opacity: loading || !input.trim() ? 0.5 : 1,
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
