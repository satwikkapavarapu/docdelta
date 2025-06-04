import React, { useState } from 'react';
import './App.css';

function App() {
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [diffResult, setDiffResult] = useState('');
  const [error, setError] = useState('');

  const handleCompare = async () => {
    if (!file1 || !file2) {
      setError('Both files must be selected.');
      return;
    }

    const formData = new FormData();
    formData.append('file1', file1);
    formData.append('file2', file2);

    try {
      const response = await fetch('http://127.0.0.1:8000/compare', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setDiffResult(data.result);
        setError('');
      } else {
        setError(data.detail);
        setDiffResult('');
      }
    } catch (err) {
      setError('Error connecting to API: ' + err.message);
      setDiffResult('');
    }
  };

  const downloadDiff = () => {
    const blob = new Blob([diffResult], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'diff_result.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6 flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-4">DocDelta Compare</h1>
      <input type="file" onChange={(e) => setFile1(e.target.files[0])} />
      <input type="file" onChange={(e) => setFile2(e.target.files[0])} className="ml-2" />
      <button onClick={handleCompare} className="block mt-4 bg-blue-500 text-white px-4 py-2 rounded">Compare</button>
      {error && <div className="mt-4 bg-red-100 text-red-700 p-2 rounded">{error}</div>}
      {diffResult && (
        <>
          <div className="mt-6 max-h-[32rem] w-full max-w-6xl overflow-auto border rounded-lg bg-gray-900 text-white p-4 text-sm font-mono whitespace-pre-wrap">
            {diffResult.split('\n').map((line, idx) => (
              <div
                key={idx}
                className={
                  line.startsWith('+')
                    ? 'text-green-400'
                    : line.startsWith('-')
                    ? 'text-red-400'
                    : line.startsWith('@')
                    ? 'text-yellow-400'
                    : 'text-white'
                }
              >
                {line}
              </div>
            ))}
          </div>
          <button onClick={downloadDiff} className="mt-2 bg-green-600 hover:bg-green-700 transition px-4 py-2 rounded text-white">
            Download Diff
          </button>
        </>
      )}
    </div>
  );
}

export default App;