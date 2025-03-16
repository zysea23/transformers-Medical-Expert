import axios from "axios";

const apiClient = axios.create({
  // baseURL: import.meta.env.VITE_API_BASE_URL || "",
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export const uploadMedicalReport = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiClient.post("/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error(" upload error :", error);
    throw error;
  }
};

export const translateExplanation = async (
  text,
  targetLanguage = "Chinese"
) => {
  try {
    const response = await apiClient.post("/translate", {
      text,
      language: targetLanguage,
    });
    return response.data;
  } catch (error) {
    console.error("translate error", error);
    throw error;
  }
};

export const askQuestion = async (reportContent, question, ragEnabled = false) => {
  try {
    if (ragEnabled) {
      return askRAGQuestion(reportContent, question);
    }
    const response = await apiClient.post("/ask", {
      report_content: reportContent,
      question,
    });
    return response.data;
  } catch (error) {
    console.error(" query error", error);
    throw error;
  }
};

export const askRAGQuestion = async (reportContent, question) => {
  try {
    const response = await apiClient.post("/rag-enhance", {
      report_content: reportContent,
      question,
    });
    return response.data;
  } catch (error) {
    console.error(" query error", error);
    throw error;
  }
};
