import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { FaUser, FaRobot, FaPaperPlane } from 'react-icons/fa';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showSubHeading, setShowSubHeading] = useState(true);

  useEffect(() => {
    if (messages.length > 0) {
      setShowSubHeading(false);
    }
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();

    if (input.trim() === '') return;

    const newMessage = { message: input };

    try {
      const response = await axios.post('http://35.160.120.126:5000/chat', newMessage, {
        headers: { 'Content-Type': 'application/json' },
      });

      const reply = response.data.reply;

      setMessages([...messages, { type: 'user', text: input }, { type: 'bot', text: reply }]);
      setInput('');
    } catch (error) {
      setMessages([...messages, { type: 'user', text: input }, { type: 'bot', text: 'Error occurred' }]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1 className="main-heading">Say Hello to <span className="highlight">HomeGenie !</span></h1>
        {showSubHeading && <h2 className="sub-heading">Your Digital Fairy Godparent Who’s Just a Text Away!</h2>}
      </header>
      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={msg.type === 'user' ? 'user-message' : 'bot-message'}>
              {msg.type === 'user' && <FaUser className="message-icon" id='user-message-align' />}
              <div className="message-text">{msg.text}</div>
              {msg.type === 'bot' && <FaRobot className="message-icon" id='bot-messsage-align' />}
            </div>
          ))}
        </div>
      </div>
      <form onSubmit={sendMessage} className="chat-form">
        <textarea
          id="message"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter your message"
          rows="1"
        />
        <button type="submit" className="send-button">
          <FaPaperPlane />
        </button>
      </form>
    </div>
  );
};

export default App;
