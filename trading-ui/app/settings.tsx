import { useState, useEffect } from "react";

export default function Settings() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [indexName, setIndexName] = useState("");
  const [expiry, setExpiry] = useState("");
  const [lotSize, setLotSize] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setEmail(localStorage.getItem("email") || "");
    setPassword(localStorage.getItem("password") || "");
    setApiKey(localStorage.getItem("apiKey") || "");
    setIndexName(localStorage.getItem("indexName") || "");
    setExpiry(localStorage.getItem("expiry") || "");
    setLotSize(localStorage.getItem("lotSize") || "");
  }, []);

  const handleSave = () => {
    localStorage.setItem("email", email);
    localStorage.setItem("password", password);
    localStorage.setItem("apiKey", apiKey);
    localStorage.setItem("indexName", indexName);
    localStorage.setItem("expiry", expiry);
    localStorage.setItem("lotSize", lotSize);
    setMessage("Settings saved!");
  };

  return (
    <div className="bg-[#0b1220] min-h-screen flex flex-col items-center justify-center text-white">
      <div className="bg-[#111827] p-8 rounded-md shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Settings</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-gray-400 mb-1">Email</label>
            <input type="email" className="w-full p-2 rounded bg-[#1f2937] text-white" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="block text-gray-400 mb-1">Password</label>
            <input type="password" className="w-full p-2 rounded bg-[#1f2937] text-white" value={password} onChange={e => setPassword(e.target.value)} />
          </div>
          <div>
            <label className="block text-gray-400 mb-1">API Key</label>
            <input type="text" className="w-full p-2 rounded bg-[#1f2937] text-white" value={apiKey} onChange={e => setApiKey(e.target.value)} />
          </div>
          <div>
            <label className="block text-gray-400 mb-1">Index Name (NIFTY/BANKNIFTY/SENSEX)</label>
            <input type="text" className="w-full p-2 rounded bg-[#1f2937] text-white" value={indexName} onChange={e => setIndexName(e.target.value)} />
          </div>
          <div>
            <label className="block text-gray-400 mb-1">Expiry (e.g. 260126)</label>
            <input type="text" className="w-full p-2 rounded bg-[#1f2937] text-white" value={expiry} onChange={e => setExpiry(e.target.value)} />
          </div>
          <div>
            <label className="block text-gray-400 mb-1">Lot Size</label>
            <input type="number" className="w-full p-2 rounded bg-[#1f2937] text-white" value={lotSize} onChange={e => setLotSize(e.target.value)} />
          </div>
        </div>
        <button className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded" onClick={handleSave}>
          Save
        </button>
        {message && <div className="mt-4 text-green-400 text-center">{message}</div>}
      </div>
    </div>
  );
}
