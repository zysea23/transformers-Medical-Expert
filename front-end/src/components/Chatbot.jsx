import { askQuestion } from "../api/index";
import React, { useEffect, useState, useRef } from "react";
import MarkdownContent from "./MarkdownContent";

import "./Chatbot.css";

const presetQuestions = [
  { id: 1, value: "What is your name?" },
  { id: 2, value: "How old are you?" },
  { id: 3, value: "What is your age?" },
  { id: 4, value: "What is your age?" },
];

const Chatbot = ({ reportContent }) => {
  const [messages, setMessages] = useState([
    { sender: "bot", message: "Hello! How can I help you?" },
  ]);
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [ragEnabled, setRagEnabled] = useState(false);
  const handleRagToggle = (e) => {
    setRagEnabled(e.target.checked);
  };

  const msgEndRef = useRef(null);

  useEffect(() => {
    // there's one message already
    if(messages.length === 1) return;
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    msgEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const formatReferencesToMarkdown = (references) => {
    if (!references || !Array.isArray(references) || references.length === 0) {
      return "";
    }

    let markdown = "\n\n### References\n\n";

    references.forEach((ref, index) => {
      markdown += `- **${ref.title}**\n\n`;
      markdown += `<details>\n<summary>View content</summary>\n\n${ref.content}\n\n</details>\n\n`;
    });

    return markdown;
  };

  const sendBotMessage = (message) => {
    setMessages((prev) =>
      prev
        .filter((msg) => msg.sender !== "loading")
        .concat({ sender: "bot", message })
    );
  };
  const sendUserMessage = (message) => {
    if (!message.trim()) return;
    setMessages((prev) => [...prev, { sender: "user", message }]);
  };
  const handleSend = async (presetMsg) => {
    const message = (presetMsg || input).trim();
    if (!message) return;

    sendUserMessage(message);
    setInput("");
    setIsLoading(true);

    setMessages((prev) => [...prev, { sender: "loading", message: "" }]);
    // backend logic
    try {
      const response = await askQuestion(reportContent, message, ragEnabled);
      if (response.success) {
        let fullMessage = response.answer;

        if (
          ragEnabled &&
          response.references &&
          Array.isArray(response.references)
        ) {
          const referencesMarkdown = formatReferencesToMarkdown(
            response.references
          );
          fullMessage = response.enhanced_explanation + referencesMarkdown;
        } else if (ragEnabled && response.enhanced_explanation) {
          fullMessage = response.enhanced_explanation;
        }

        sendBotMessage(fullMessage);
      } else {
        sendBotMessage("Sorry, I cannot understand your question.");
      }
    } catch (err) {
      console.log(err);
      sendBotMessage("Sorry, I cannot understand your question.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    setMessages([{ sender: "bot", message: "Hello! How can I help you?" }]);
    setSelectedQuestion("");
    setInput("");
  };

  const handledropdown = (e) => {
    if (e.target.classList.contains("dropdown-item")) {
      e.preventDefault();
      const selectedQuestion = e.target.textContent;
      setSelectedQuestion(selectedQuestion);
      handleSend(selectedQuestion);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <h1 className="header-text">Ask Questions About Your Results</h1>
        <div className="header-controls">
          <div className="form-check form-switch">
            <input
              className="form-check-input"
              type="checkbox"
              role="switch"
              id="ragToggle"
              checked={ragEnabled}
              onChange={handleRagToggle}
            />
            <label className="form-check-label" htmlFor="ragToggle">
              Use RAG
            </label>
          </div>
          <div className="dropdown" onClick={handledropdown}>
            <button
              className="btn btn-light btn-sm dropdown-toggle"
              type="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Select Your Question
            </button>
            <ul className="dropdown-menu">
              {presetQuestions.map((question) => (
                <li key={question.id}>
                  <a className="dropdown-item" href="#">
                    {question.value}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div className="new-chat" onClick={() => handleRefresh()}>
            <button type="button" className="btn btn-light btn-sm">
              <i className="bi bi-arrow-clockwise"></i> New Chat
            </button>
          </div>
        </div>
      </div>
      <div className="chatbot-window">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            {message.sender === "bot" && (
              <i className="bi bi-robot" style={{ fontSize: "1.75rem" }}></i>
            )}
            {message.sender === "loading" ? (
              <div className="loading-indicator">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            ) : (
              <div className={`message-content ${message.sender}`}>
                <MarkdownContent
                  content={message.message}
                  showAll={true}
                  maxHeight={"none"}
                />
              </div>
            )}
            {message.sender === "user" && (
              <i
                className="bi bi-person-fill"
                style={{ fontSize: "1.75rem" }}
              ></i>
            )}
          </div>
        ))}
        <div ref={msgEndRef} />
      </div>
      <div className="chatbot-input">
        <input
          type="text"
          className="form-control"
          placeholder="Type your question here..."
          aria-label="User message"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !isLoading) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button
          className="btn btn-primary btn-sm"
          onClick={() => handleSend()}
          disabled={isLoading}
        >
          <i className="bi bi-send"></i> Send
        </button>
      </div>
    </div>
  );
};

export default Chatbot;
