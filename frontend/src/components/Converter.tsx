import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/converter';
import type { ConversionFormat } from '../api/converter';
import './Converter.css';

type ConversionType = 'pdf_to_word' | 'word_to_pdf' | 'word_to_excel' | 'excel_to_word';

const FILE_EXTENSIONS: Record<ConversionType, string[]> = {
  pdf_to_word: ['.pdf'],
  word_to_pdf: ['.docx', '.doc'],
  word_to_excel: ['.docx', '.doc'],
  excel_to_word: ['.xlsx', '.xls'],
};

const OUTPUT_EXTENSIONS: Record<ConversionType, string> = {
  pdf_to_word: '.docx',
  word_to_pdf: '.pdf',
  word_to_excel: '.xlsx',
  excel_to_word: '.docx',
};

type EngineType = 'auto' | 'marker' | 'pdf2docx' | 'doctr';

const ENGINE_OPTIONS: { value: EngineType; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Automatically select best engine' },
  { value: 'marker', label: 'Marker (Professional)', description: 'Best quality, ML-based conversion' },
  { value: 'pdf2docx', label: 'PDF2DOCX', description: 'Fast, good for text PDFs' },
  { value: 'doctr', label: 'DocTR (OCR)', description: 'For scanned documents' },
];

export function Converter() {
  const [formats, setFormats] = useState<ConversionFormat[]>([]);
  const [selectedType, setSelectedType] = useState<ConversionType>('pdf_to_word');
  const [selectedEngine, setSelectedEngine] = useState<EngineType>('auto');
  const [file, setFile] = useState<File | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [serverStatus, setServerStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check server status
  useEffect(() => {
    const checkServer = async () => {
      const isHealthy = await api.healthCheck();
      setServerStatus(isHealthy ? 'online' : 'offline');
    };
    checkServer();
    const interval = setInterval(checkServer, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load conversion formats
  useEffect(() => {
    const loadFormats = async () => {
      try {
        const data = await api.getFormats();
        setFormats(data);
      } catch (err) {
        console.error('Failed to load formats:', err);
      }
    };
    loadFormats();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const ext = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'));
      const validExtensions = FILE_EXTENSIONS[selectedType];

      if (!validExtensions.includes(ext)) {
        setError(`Invalid file type. Expected: ${validExtensions.join(', ')}`);
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  const handleTypeChange = (type: ConversionType) => {
    setSelectedType(type);
    setFile(null);
    setError(null);
    setSuccess(null);
  };

  const handleConvert = useCallback(async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsConverting(true);
    setError(null);
    setSuccess(null);

    try {
      // Use sync endpoint (no Redis required)
      const blob = await api.convertSync(file, selectedType, selectedEngine);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate output filename
      const baseName = file.name.slice(0, file.name.lastIndexOf('.'));
      const outputExt = OUTPUT_EXTENSIONS[selectedType];
      link.download = `${baseName}_converted${outputExt}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(`Successfully converted ${file.name}!`);
      setFile(null);

      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Conversion failed. Please try again.');
      }
    } finally {
      setIsConverting(false);
    }
  }, [file, selectedType, selectedEngine]);

  const selectedFormat = formats.find(f => f.type === selectedType);

  return (
    <div className="converter">
      <header className="converter-header">
        <h1>Document Converter</h1>
        <p>Convert documents between PDF, Word, and Excel formats</p>
        <div className={`server-status ${serverStatus}`}>
          <span className="status-dot"></span>
          Server: {serverStatus === 'checking' ? 'Checking...' : serverStatus}
        </div>
      </header>

      <div className="converter-body">
        {/* Conversion Type Selection */}
        <section className="conversion-types">
          <h2>Select Conversion Type</h2>
          <div className="type-grid">
            {formats.map((format) => (
              <button
                key={format.type}
                className={`type-card ${selectedType === format.type ? 'selected' : ''}`}
                onClick={() => handleTypeChange(format.type as ConversionType)}
              >
                <div className="type-arrow">
                  <span className="from">{format.from.split(' ')[0]}</span>
                  <span className="arrow">→</span>
                  <span className="to">{format.to.split(' ')[0]}</span>
                </div>
                <p className="type-description">{format.description}</p>
              </button>
            ))}
          </div>
        </section>

        {/* File Upload */}
        <section className="file-upload">
          <h2>Upload File</h2>
          {selectedFormat && (
            <p className="accepted-files">
              Accepted formats: {FILE_EXTENSIONS[selectedType].join(', ')}
            </p>
          )}

          <div className="upload-area">
            <input
              id="file-input"
              type="file"
              accept={FILE_EXTENSIONS[selectedType].join(',')}
              onChange={handleFileChange}
              disabled={isConverting || serverStatus === 'offline'}
            />
            <label htmlFor="file-input" className="upload-label">
              {file ? (
                <div className="file-info">
                  <span className="file-icon">📄</span>
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
              ) : (
                <div className="upload-prompt">
                  <span className="upload-icon">📁</span>
                  <span>Click to select a file or drag and drop</span>
                </div>
              )}
            </label>
          </div>
        </section>

        {/* Engine Selection (for PDF to Word only) */}
        {selectedType === 'pdf_to_word' && (
          <section className="engine-selection">
            <h2>Conversion Engine</h2>
            <div className="engine-grid">
              {ENGINE_OPTIONS.map((engine) => (
                <button
                  key={engine.value}
                  className={`engine-card ${selectedEngine === engine.value ? 'selected' : ''}`}
                  onClick={() => setSelectedEngine(engine.value)}
                >
                  <span className="engine-label">{engine.label}</span>
                  <span className="engine-description">{engine.description}</span>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Convert Button */}
        <section className="convert-action">
          <button
            className="convert-button"
            onClick={handleConvert}
            disabled={!file || isConverting || serverStatus === 'offline'}
          >
            {isConverting ? (
              <>
                <span className="spinner"></span>
                Converting...
              </>
            ) : (
              <>Convert & Download</>
            )}
          </button>
        </section>

        {/* Status Messages */}
        {error && (
          <div className="message error">
            <span className="icon">❌</span>
            {error}
          </div>
        )}
        {success && (
          <div className="message success">
            <span className="icon">✅</span>
            {success}
          </div>
        )}
      </div>

      <footer className="converter-footer">
        <p>
          Powered by FastAPI + pdf2docx + python-docx + openpyxl
        </p>
      </footer>
    </div>
  );
}
