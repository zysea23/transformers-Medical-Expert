import React, { useState } from "react";
import { TypeAnimation } from "react-type-animation";
import { useNavigate } from "react-router-dom";
import { uploadMedicalReport } from "../api/index";
import "./HomePage.scss";
import upload from "../assets/upload.png";

const HomePage = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      alert("Please select a medical report file");
      return;
    }
    
    setLoading(true);
    
    try {
      const result = await uploadMedicalReport(file);
      
      if (result.success) {
        // Navigate to results page on success
        navigate('/results', { state: { result } });
      } else {
        alert(`Processing failed: ${result.message}`);
      }
    } catch (error) {
      alert(`Request failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <main className="main">
        <section className="hero">
          <h2>
            <TypeAnimation
              sequence={["Understand Your Medical Records with Clarity", 1000]}
              wrapper="span"
              speed={50}
              style={{ display: "inline-block" }}
              repeat={1}
            />
          </h2>
          <p>
            Transform complex medical terminology into clear, easy-to-understand
            explanations. Upload your medical records and get instant
            interpretations.
          </p>
        </section>

        <section className="upload-section">
          <div className="upload-box">
            <h3>Upload Your Medical Record</h3>
            <p>Supported formats: JPG, PNG (Max size: 10MB)</p>
            <form onSubmit={handleUpload}>
              <input
                type="file"
                id="file-upload"
                className="file-input"
                onChange={handleFileChange}
              />
              <img src={upload} alt="Upload" className="upload-icon" />
              <label htmlFor="file-upload" className="file-label">
                Choose File
              </label>
              {file && <p className="file-name">{file.name}</p>}
              
              {file && (
                <button type="submit" className="upload-button" disabled={loading}>
                  {loading ? 'processing...' : 'upload and analyze'}
                </button>
              )}
            </form>
          </div>
        </section>

        <section className="features">
          <h3>Smart Features for Better Understanding</h3>
          <div className="feature-list">
            <div className="feature-item">
              <div className="icon">🔍</div>
              <h4>AI-Powered Analysis</h4>
              <p>
                Advanced machine learning algorithms for accurate interpretation
              </p>
            </div>
            <div className="feature-item">
              <div className="icon">🔒</div>
              <h4>Privacy First</h4>
              <p>Your data is encrypted and secure with HIPAA compliance</p>
            </div>
            <div className="feature-item">
              <div className="icon">⚡</div>
              <h4>Instant Results</h4>
              <p>Get explanations within seconds of uploading</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default HomePage;