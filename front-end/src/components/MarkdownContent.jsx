import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw';
import "./MarkdownContent.scss";

const MarkdownContent = ({ content, className = "", maxHeight = 300, showAll = false}) => {
  const [expanded, setExpanded] = useState(false);
  const [showToggle, setShowToggle] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current && !showAll) {
      const scrollHeight = contentRef.current.scrollHeight;
      setShowToggle(scrollHeight > maxHeight);
    }
  }, [content, maxHeight]);

  const toggleExpand = () => {
    setExpanded(!expanded);
  };

  return (
    <div className={`markdown-content-wrapper ${className}`}>
      <div
        ref={contentRef}
        className={`markdown-content ${expanded ? "expanded" : "collapsed"} ${showAll ? "no-collapse" : ""}`}
        style={{ maxHeight: expanded ? "none" : `${maxHeight}px` }}
      >
        <ReactMarkdown remarkPlugins={[[remarkGfm, {singleTilde: false}]]} rehypePlugins={[rehypeRaw]}>{content || ""}</ReactMarkdown>
      </div>

      {showToggle && (
        <button className="toggle-expand-btn" onClick={toggleExpand}>
          <span className={`arrow ${expanded ? "up" : "down"}`}></span>
        </button>
      )}
    </div>
  );
};

export default MarkdownContent;
