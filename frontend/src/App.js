import React, { useState, useRef, useEffect } from 'react';
import './App.css'; // Assuming you have a CSS file for styles

// --- Helper Components & SVGs ---
const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
    </svg>
);

const BotIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8"></path>
        <rect width="16" height="12" x="4" y="8" rx="2"></rect>
        <path d="M2 14h2"></path>
        <path d="M20 14h2"></path>
        <path d="M15 13v2"></path>
        <path d="M9 13v2"></path>
    </svg>
);

const SendIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m22 2-7 20-4-9-9-4Z"></path>
        <path d="m22 2-11 11"></path>
    </svg>
);

const PlusIcon = () => (
     <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
         <path d="M5 12h14"></path>
         <path d="M12 5v14"></path>
     </svg>
);


// --- Main Application Component ---

export default function App() {
    // --- State Management ---
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [documentId, setDocumentId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);
    const chatEndRef = useRef(null);

    // --- Effects ---
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // --- Core Functions ---
    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setIsLoading(true);
        setError(null);
        setMessages([]);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // NOTE: Replace with your actual API endpoint
            const response = await fetch('http://127.0.0.1:8000/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'File upload failed');
            }

            const data = await response.json();
            setDocumentId(data.document_id);
            setMessages([{ 
                sender: 'bot', 
                text: `File "${data.document_id}" uploaded successfully. How can I help you?` 
            }]);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || !documentId || isLoading) return;

        const userMessage = { sender: 'user', text: inputValue };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);
        setError(null);

        try {
            // NOTE: Replace with your actual API endpoint
            const response = await fetch('http://127.0.0.1:8000/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ document_id: documentId, question: inputValue }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to get an answer');
            }

            const data = await response.json();
            const botMessage = { sender: 'bot', text: data.answer };
            setMessages(prev => [...prev, botMessage]);

        } catch (err) {
            setError(err.message);
            const errorMessage = { sender: 'bot', text: `Sorry, an error occurred: ${err.message}` };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleNewChat = () => {
        setDocumentId(null);
        setMessages([]);
        setError(null);
        if(fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // --- Render Logic ---
    return (
        <div className="appContainer">
            {/* <AppStyles /> */}
            <aside className="sidebar">
                <button onClick={handleNewChat} className="newChatBtn">
                    <PlusIcon />
                    New Chat
                </button>
                <div className="documentInfo">
                     <p>Document: {documentId || "None"}</p>
                </div>
            </aside>

            <main className="mainContent">
                <div className="chatArea">
                    {!documentId ? (
                        <UploadView onFileUpload={handleFileUpload} fileInputRef={fileInputRef} isLoading={isLoading} />
                    ) : (
                        <ChatView messages={messages} isLoading={isLoading} />
                    )}
                    <div ref={chatEndRef} />
                </div>
                
                <div className="inputContainer">
                    {error && <p className="errorText">{error}</p>}
                    <div className="inputWrapper">
                        <textarea
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={documentId ? "Ask a question about the document..." : "Please upload a document first"}
                            className="chatTextarea"
                            rows="1"
                            disabled={!documentId || isLoading}
                        />
                        <button 
                            onClick={handleSendMessage}
                            disabled={!documentId || isLoading || !inputValue.trim()}
                            className="sendButton"
                        >
                            <SendIcon />
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
}

// --- Sub-Components for Clarity ---
const UploadView = ({ onFileUpload, fileInputRef, isLoading }) => (
    <div className="uploadView">
        <h1>Document Q&A</h1>
        <p>Upload a PDF to start asking questions.</p>
        <div className="uploadBox">
            <input 
                type="file" 
                accept=".pdf" 
                onChange={onFileUpload} 
                ref={fileInputRef}
                style={{ display: 'none' }} 
                id="file-upload"
            />
            <label htmlFor="file-upload" className="uploadLabel">
                {isLoading ? "Processing..." : "Select PDF File"}
            </label>
        </div>
    </div>
);

const ChatView = ({ messages, isLoading }) => (
    <div className="chatView">
        {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender === 'user' ? 'user' : 'bot'}`}>
                {msg.sender === 'bot' && <div className="avatar"><BotIcon /></div>}
                <div className="messageText">
                    <p>{msg.text}</p>
                </div>
                {msg.sender === 'user' && <div className="avatar"><UserIcon /></div>}
            </div>
        ))}
        {isLoading && messages.length > 0 && messages[messages.length - 1]?.sender === 'user' && (
             <div className="message bot">
                 <div className="avatar"><BotIcon /></div>
                 <div className="messageText">
                    <div className="loadingContainer">
                        <div className="loadingDot"></div>
                        <div className="loadingDot"></div>
                        <div className="loadingDot"></div>
                    </div>
                 </div>
            </div>
        )}
    </div>
);

