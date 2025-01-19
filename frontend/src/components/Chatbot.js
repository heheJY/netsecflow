import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'; // For rendering markdown
import './Chatbot.css';

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const toggleChatbot = () => {
    setIsOpen(!isOpen);
  };

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    const userMessage = { sender: 'user', text: userInput };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setUserInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/chatbot', { question: userInput });
      const botMessage = { sender: 'bot', text: response.data.answer };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      const errorMessage = { sender: 'bot', text: 'Sorry, something went wrong. Please try again later.' };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-circle" onClick={toggleChatbot}>
        💬
      </div>
      {isOpen && (
        <div className="chatbot">
          <div className="chatbot-header">
            <h4>Chat with SDN Assistant</h4>
            <button className="close-button" onClick={toggleChatbot}>✖</button>
          </div>
          <div className="chatbot-messages">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message ${msg.sender}`}
              >
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            ))}
            {isLoading && (
              <div className="message bot">
                <span className="loading-dots">
                  <span>.</span>
                  <span>.</span>
                  <span>.</span>
                </span>
              </div>
            )}
          </div>
          <div className="chatbot-input">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Type your question..."
            />
            <button onClick={sendMessage} disabled={isLoading}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Chatbot;
