import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { askQuestion, translateExplanation } from "../api/index";
import { checkNull, convertDate } from "../utils/filters.js";
import MarkdownContent from "../components/MarkdownContent";
import Card from "../components/Card";
import Chatbot from "../components/Chatbot";
import MatricCard from "../components/MatricCard";

import "./ResultPage.scss";


const ResultPage = () => {
  const location = useLocation();
  const result = location.state?.result;

  const [question, setQuestion] = useState("");
  const [qaHistory, setQaHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // interpreter card
  const [translationLoading, setTranslationLoading] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState("English");
  const [translatedExplanation, setTranslatedExplanation] = useState("");
  const [translationCache, setTranslationCache] = useState({
    English: "",
  });

  const handleLanguageChange = async (language) => {
    if (currentLanguage === language || !result?.explanation) return;

    setTranslationLoading(true);
    setCurrentLanguage(language);

    try {
      if (translationCache[language]) {
        setTranslatedExplanation(translationCache[language]);
      } else {
        if (language === "English") {
          setTranslatedExplanation(result.explanation);
          setTranslationCache((prev) => ({
            ...prev,
            English: result.explanation,
          }));
        } else {
          const response = await translateExplanation(
            result.explanation,
            language
          );
          if (response.success) {
            setTranslatedExplanation(response.translated_text);
            setTranslationCache((prev) => ({
              ...prev,
              [language]: response.translated_text,
            }));
          } else {
            console.error("Translation failed:", response.message);
            setTranslatedExplanation(result.explanation);
          }
        }
      }
    } catch (error) {
      console.error("Translation error:", error);
      setTranslatedExplanation(result.explanation);
    } finally {
      setTranslationLoading(false);
    }
  };

  useEffect(() => {
    if (result) {
      setQaHistory([
        {
          type: "info",
          text: "Hello! I'm your medical AI assistant. I can help explain your test results or answer any questions you might have about them.",
        },
      ]);
    }
    const englishExplanation = result?.explanation || "";
    setTranslatedExplanation(englishExplanation);
    setTranslationCache({
      English: englishExplanation,
    });
  }, [result]);

  const handleQuestionSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      alert("Please enter a question");
      return;
    }

    setIsLoading(true);
    setQaHistory([...qaHistory, { type: "question", text: question }]);
    setQuestion("");

    try {
      const response = await askQuestion(
        result?.original_content || "",
        question
      );
      if (response.success) {
        setQaHistory((prev) => [
          ...prev,
          { type: "answer", text: response.answer },
        ]);
      } else {
        setQaHistory((prev) => [
          ...prev,
          { type: "error", text: `Error: ${response.message}` },
        ]);
      }
    } catch (error) {
      setQaHistory((prev) => [
        ...prev,
        { type: "error", text: `Error: ${error.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderField = (label, value, filter) => (
    <div className="detail-item flex-col">
      <span className="label label-txt">{label}:</span>
      <span className="value">{filter ? filter(value) : checkNull(value)}</span>
    </div>
  );

  if (!result) {
    return (
      <div className="result-page">
        <div className="container">
          <h1>Unable to display results</h1>
          <p>
            No analysis results found. Please upload a medical report first.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="result-page">
      <div className="container">
        <Card
          title="Key Matrics"
          className="report-summary"
        >
          {result?.indicators ? (
            <div className="indicators-grid">
              {Object.entries(result.indicators).map(([name, values]) => (
                <div key={name} className="test-item">
                  <MatricCard
                    matricName={name}
                    marks={values}
                    formatMark={(value) => value.toFixed(1)}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p>No test results available.</p>
          )}
        </Card>

        <Card
          className="test-results"
          title="Medical Summary"
          titleRight={
            <span className="results-date">
              Results as of {convertDate(result?.report_date)}
            </span>
          }
        >
          <div>
            <MarkdownContent content={result?.original_content} />
          </div>
        </Card>

        <Card
          title="AI Interpretation"
          titleRight={
            <div className="language-selector">
              <div className="ai-badge">AI Powered</div>
              <div className="dropdown">
                <button
                  className="dropdown-toggle"
                  type="button"
                  id="languageDropdown"
                  disabled={translationLoading}
                >
                  {translationLoading ? "Translating..." : currentLanguage}
                  {/* <span className="caret"></span> */}
                </button>
                <ul className="dropdown-menu">
                  <li>
                    <button onClick={() => handleLanguageChange("English")}>
                      English
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleLanguageChange("Chinese")}>
                      中文
                    </button>
                  </li>
                  <li>
                    <button onClick={() => handleLanguageChange("Spanish")}>
                      Español
                    </button>
                  </li>
                </ul>
              </div>
            </div>
          }
        >
          <div className={translationLoading ? "content-loading" : ""}>
            {translationLoading && <div className="loading-spinner"></div>}
            <MarkdownContent content={translatedExplanation} />
          </div>
        </Card>

        <Chatbot reportContent={result.original_content} />
      </div>
    </div>
  );
};

export default ResultPage;
