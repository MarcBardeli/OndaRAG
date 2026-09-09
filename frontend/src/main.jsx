import React, { useEffect, useId, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const newId = () => crypto.randomUUID();

function App() {
  const [conversationId, setConversationId] = useState(() => localStorage.getItem('omni_conversation') || newId());
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState('');
  const [sources, setSources] = useState([]);
  const [autoTts, setAutoTts] = useState(() => localStorage.getItem('omni_auto_tts') === 'true');
  const inputRef = useRef(null);

  useEffect(() => localStorage.setItem('omni_conversation', conversationId), [conversationId]);
  useEffect(() => localStorage.setItem('omni_auto_tts', String(autoTts)), [autoTts]);

  const startNewChat = () => {
    setConversationId(newId());
    setMessages([]);
    setNotice('New conversation ready');
    inputRef.current?.focus();
  };

  const sendMessage = async (event) => {
    event?.preventDefault();
    const message = draft.trim();
    if (!message || busy) return;
    setDraft('');
    setMessages((current) => [...current, { role: 'user', content: message }]);
    setBusy(true);
    setNotice('OmniCar is thinking...');
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      });
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      const data = await response.json();
      setMessages((current) => [...current, { role: 'assistant', content: data.text, audio: data.audio }]);
      setNotice('Ready');
    } catch (error) {
      setMessages((current) => [...current, { role: 'error', content: error.message }]);
      setNotice('Could not reach the local model');
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const uploadFile = async () => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    setNotice('Indexing document...');
    try {
      const response = await fetch('/upload', { method: 'POST', body: form });
      if (!response.ok) throw new Error('Upload failed');
      setNotice(`${file.name} added to knowledge`);
      setFile(null);
    } catch (error) {
      setNotice(error.message);
    }
  };

  const inspectKnowledge = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    try {
      const response = await fetch(`/debug/retrieve?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSources(data.results || []);
    } catch {
      setSources([]);
    }
  };

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Workspace navigation">
        <div className="brand"><span className="brand-mark">O</span><span>OMNICAR</span><span className="brand-dot" /></div>
        <div className="sidebar-section">
          <div className="section-label">Workspace</div>
          <button className="nav-item active" type="button" aria-current="page"><span className="nav-icon" aria-hidden="true">✦</span> Assistant <span className="nav-count">1</span></button>
          <button className="nav-item" type="button" onClick={startNewChat}><span className="nav-icon" aria-hidden="true">＋</span> New conversation</button>
        </div>
        <div className="sidebar-section knowledge-section">
          <div className="section-label">Knowledge base</div>
          <label className="upload-drop">
            <input type="file" accept=".txt,.md" onChange={(event) => setFile(event.target.files?.[0] || null)} />
            <span className="upload-icon">↑</span>
            <strong>{file ? file.name : 'Add a document'}</strong>
            <small>{file ? 'Ready to index' : 'TXT or Markdown'}</small>
          </label>
          {file && <button className="index-button" type="button" onClick={uploadFile}>Index document <span aria-hidden="true">→</span></button>}
        </div>
        <div className="sidebar-footer"><span className="status-dot" /> Local model online <span className="version">v1.0</span></div>
      </aside>

      <section className="workspace">
        <header className="topbar"><div><span className="eyebrow">LOCAL INTELLIGENCE</span><h1>OmniCar assistant</h1></div><div className="topbar-actions"><label className="tts-toggle"><input type="checkbox" checked={autoTts} onChange={(event) => setAutoTts(event.target.checked)} /> <span>Auto-play responses</span></label><button className="new-chat" type="button" onClick={startNewChat}><span aria-hidden="true">＋</span> <span>New chat</span></button></div></header>
        <div className="chat-stage">
          {messages.length === 0 ? <div className="welcome"><div className="welcome-symbol" aria-hidden="true">✦</div><p className="eyebrow">YOUR PRIVATE COPILOT</p><h2>What can I help you<br /><em>understand?</em></h2><p className="welcome-copy">Ask about your indexed knowledge, explore a topic, or bring in a new document to give OmniCar more context.</p><div className="prompt-grid"><button type="button" onClick={() => setDraft('Summarize the key points in my knowledge base')}>Summarize my knowledge base <span aria-hidden="true">↗</span></button><button type="button" onClick={() => setDraft('What documents are available?')}>What is in my workspace? <span aria-hidden="true">↗</span></button></div></div> : <div className="messages" role="log" aria-label="Conversation messages" aria-live="off">{messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} autoTts={autoTts} />)}{busy && <div className="message assistant" role="status" aria-label="OmniCar is thinking"><div className="avatar" aria-hidden="true">O</div><div className="bubble thinking" aria-hidden="true"><span /><span /><span /></div></div>}</div>}
        </div>
        <div className="composer-wrap"><form className="composer" onSubmit={sendMessage}><textarea ref={inputRef} aria-label="Message OmniCar" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(event); } }} placeholder="Ask OmniCar anything..." rows="1" disabled={busy} /><button className="send-button" type="submit" aria-label="Send message" disabled={!draft.trim() || busy}>↑</button></form><div className="composer-meta"><span aria-live="polite">{notice || 'Enter to send · Shift + Enter for a new line'}</span><span>Responses use your local knowledge</span></div></div>
      </section>

      <aside className="inspector" aria-label="Knowledge inspector"><div className="inspector-heading"><div><span className="eyebrow">CONTEXT</span><h2>Knowledge inspector</h2></div><span className="live-pill"><span aria-hidden="true" /> LIVE</span></div><p className="inspector-copy">Search the indexed documents directly and see the context available to your assistant.</p><form className="search-box" onSubmit={inspectKnowledge}><span aria-hidden="true">⌕</span><input aria-label="Search knowledge" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search knowledge..." /><button type="submit" aria-label="Search knowledge">↵</button></form><div className="source-list">{sources.length ? sources.map((source, index) => <article className="source-card" key={`${source.source}-${index}`}><div className="source-top"><span className="file-badge">TXT</span><strong>{source.source}</strong><span className="score">{Math.round((source.score || 0) * 100)}%</span></div><p>{source.content}</p></article>) : <div className="empty-sources"><div aria-hidden="true">⌁</div><strong>No context loaded</strong><span>Search above to inspect relevant passages.</span></div>}</div><div className="inspector-note"><span aria-hidden="true">i</span><p>OmniCar runs locally. Your documents stay on this machine.</p></div></aside>
    </main>
  );
}

function Message({ message, autoTts }) {
  if (message.role === 'error') return <div className="error-message" role="alert">{message.content}</div>;
  const assistant = message.role === 'assistant';
  return <article className={`message ${assistant ? 'assistant' : 'user'}`}><div className="avatar" aria-hidden="true">{assistant ? 'O' : 'Y'}</div><div className="message-body"><span className="message-label">{assistant ? 'OMNICAR' : 'YOU'}</span><div className="bubble">{message.content}</div>{assistant && message.audio && <TtsControls src={message.audio} autoPlay={autoTts} />}</div></article>;
}

function TtsControls({ src, autoPlay }) {
  const audioRef = useRef(null);
  const statusId = useId();
  const [status, setStatus] = useState('Ready to play');
  const [speed, setSpeed] = useState(1);

  const play = async () => {
    try {
      await audioRef.current.play();
      setStatus('Playing response');
    } catch {
      setStatus('Playback unavailable. The text response is still available above.');
    }
  };

  useEffect(() => {
    if (autoPlay) play();
  }, [autoPlay]);

  const pause = () => {
    audioRef.current?.pause();
    setStatus('Playback paused');
  };

  const stop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setStatus('Playback stopped');
  };

  const changeSpeed = (event) => {
    const nextSpeed = Number(event.target.value);
    setSpeed(nextSpeed);
    if (audioRef.current) audioRef.current.playbackRate = nextSpeed;
  };

  return <div className="tts-controls" role="group" aria-label="Text to speech controls"><audio ref={audioRef} className="tts-audio" src={src} aria-hidden="true" onEnded={() => setStatus('Playback finished')} onError={() => setStatus('Playback unavailable. The text response is still available above.')} /><div className="tts-buttons"><button type="button" onClick={play} aria-describedby={statusId}>Play</button><button type="button" onClick={pause} aria-describedby={statusId}>Pause</button><button type="button" onClick={stop} aria-describedby={statusId}>Stop</button><label>Speed <select value={speed} onChange={changeSpeed} aria-label="Playback speed"><option value="0.75">0.75x</option><option value="1">1x</option><option value="1.25">1.25x</option><option value="1.5">1.5x</option><option value="2">2x</option></select></label></div><span className="tts-status" id={statusId} aria-live="polite">{status}</span></div>;
}

createRoot(document.getElementById('root')).render(<App />);