# Medical Expert - AI-Powered Medical Record Interpreter

## Project Overview

Medical Expert is an innovative AI-driven application designed to help users understand complex medical reports. It leverages advanced machine learning technology to translate professional medical terminology into easy-to-understand explanations, enabling patients to better comprehend their health conditions.

## Key Features

### 📄 Medical Record Upload & Analysis
- Supports medical reports in PDF, JPG, and PNG formats
- Quickly processes and extracts key information from reports
- Handles files up to 10MB in size

### 📊 Key Health Metrics Visualization
- Intuitively displays key health indicators (such as cholesterol, blood glucose, etc.)
- Uses a color-coding system (green, yellow, red) to mark normal, borderline, and abnormal values
- Clearly shows the normal range and current value for each indicator

### 📝 AI Interpretation Engine
- Translates complex medical terminology into easy-to-understand explanations
- Provides context and meaning for health data
- Highlights abnormal values that need attention

### 🌐 Multi-language Support
- Offers translation of medical explanations into multiple languages
- Currently supports English, Chinese, and Spanish
- Caches translation results for improved performance

### 💬 Intelligent Medical Assistant
- Interactive chatbot answers questions about medical reports
- Supports RAG (Retrieval-Augmented Generation) mode for more accurate answers
- Includes reference sources to enhance credibility

### 🔒 Privacy & Security
- HIPAA-compliant data encryption and security measures
- Protects users' sensitive medical information

## Technical Architecture

- Frontend: React + Vite
- UI Components: Custom Card, MatricCard, Markdown rendering components
- API Integration: Use RESTful API services provided by the [backend services](https://github.com/zysea23/medical-report-interpreter)
- AI Technology: Large language models for text analysis and Q&A

## Installation & Setup

```bash
# Clone the repository
git clone https://github.com/fyZhang66/medicalExpert.git

# Navigate to the project directory
cd medicalExpert

# Install dependencies
npm install

# Start the development server
npm run dev

# Build for production
npm run build
```

## Usage Flow

1. Upload your medical report file on the homepage
2. Wait for AI processing and analysis of the report content
3. View the generated key metrics, medical report summary, and AI interpretation
4. Use the language selector to switch between different language interpretations
5. Ask specific questions about the report through the chatbot

## Contribution Guidelines

Contributions of code, issues, or suggestions are welcome! Please fork the repository and submit a pull request.

## License

MIT License

## Contact

For questions or suggestions, please contact us through [project issues](https://github.com/yourusername/medicalExpert/issues).

---

**Medical Disclaimer**: The information provided by Medical Expert is for reference only and does not constitute medical advice. Important health decisions should always be made in consultation with qualified healthcare professionals.