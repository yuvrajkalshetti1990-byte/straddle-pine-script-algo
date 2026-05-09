'use client'

import React, { useState } from 'react';

interface TradingPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedStrike?: string;
  optionType?: 'CE' | 'PE';
  currentLTP?: string;
}

interface TradeFormData {
  strategyTag: string;
  tickSize: string;
  quantity: string;
  qtyMultiplier: string;
  instrument: string;
  strikeCalculation: string;
  strikePriceDiff: string;
  expiryDate: string;
  productType: string;
  orderType: string;
  stopLossType: 'Points' | '%';
  targetType: 'Points' | '%';
  target: string;
  stopLoss: string;
  trailing: string;
  trailingType: 'TSL' | 'TGT';
  customPort: string;
  defaultPort: string;
}

const TradingPanel: React.FC<TradingPanelProps> = ({ 
  isOpen, 
  onClose, 
  selectedStrike = '25850',
  optionType = 'CE',
  currentLTP = '128.75'
}) => {
  const [tradeForm, setTradeForm] = useState<TradeFormData>({
    strategyTag: 'STG1',
    tickSize: '0.05',
    quantity: '65',
    qtyMultiplier: '4',
    instrument: 'Index Option',
    strikeCalculation: 'ATM',
    strikePriceDiff: '100',
    expiryDate: '01/',
    productType: 'NRML',
    orderType: 'Market',
    stopLossType: 'Points',
    targetType: 'Points',
    target: '5',
    stopLoss: '5',
    trailing: '0',
    trailingType: 'TSL',
    customPort: '',
    defaultPort: '30001'
  });

  const handleInputChange = (field: keyof TradeFormData, value: string) => {
    setTradeForm(prev => ({ ...prev, [field]: value }));
  };

  const executeTrade = (action: 'LE' | 'LX' | 'SE' | 'SX') => {
    console.log(`Executing ${action} for ${selectedStrike} ${optionType}`, tradeForm);
    // Implementation for trade execution
  };

  const saveTrade = () => {
    console.log('Saving trade configuration:', tradeForm);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-96 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-blue-600 text-white px-4 py-3 rounded-t-lg flex justify-between items-center">
          <div>
            <h3 className="font-bold">Online Help Tutorial</h3>
            <div className="text-sm opacity-90">
              Strike: {selectedStrike} | Type: {optionType} | LTP: {currentLTP}
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-white hover:text-gray-200 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Form Content */}
        <div className="p-4 space-y-4">
          {/* Strategy Tag */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Strategy tag</label>
            <input
              type="text"
              value={tradeForm.strategyTag}
              onChange={(e) => handleInputChange('strategyTag', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Tick Size */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Tick size</label>
            <input
              type="text"
              value={tradeForm.tickSize}
              onChange={(e) => handleInputChange('tickSize', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Quantity */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Quantity</label>
            <input
              type="text"
              value={tradeForm.quantity}
              onChange={(e) => handleInputChange('quantity', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* QTY Multiplier */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">QTY Multiplier</label>
            <input
              type="text"
              value={tradeForm.qtyMultiplier}
              onChange={(e) => handleInputChange('qtyMultiplier', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Instrument */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Instrument</label>
            <select
              value={tradeForm.instrument}
              onChange={(e) => handleInputChange('instrument', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="Index Option">Index Option</option>
              <option value="Stock Option">Stock Option</option>
              <option value="Futures">Futures</option>
            </select>
          </div>

          {/* Strike Calculation */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Strike Calculation</label>
            <select
              value={tradeForm.strikeCalculation}
              onChange={(e) => handleInputChange('strikeCalculation', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="ATM">ATM</option>
              <option value="ITM">ITM</option>
              <option value="OTM">OTM</option>
              <option value="Custom">Custom</option>
            </select>
          </div>

          {/* Strike Price Diff */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Strike Price Diff</label>
            <input
              type="text"
              value={tradeForm.strikePriceDiff}
              onChange={(e) => handleInputChange('strikePriceDiff', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Expiry Date */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Expiry Date</label>
            <input
              type="text"
              value={tradeForm.expiryDate}
              onChange={(e) => handleInputChange('expiryDate', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
              placeholder="DD/MM/YYYY"
            />
          </div>

          {/* Product Type */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Product Type</label>
            <select
              value={tradeForm.productType}
              onChange={(e) => handleInputChange('productType', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="NRML">NRML</option>
              <option value="MIS">MIS</option>
              <option value="CNC">CNC</option>
            </select>
          </div>

          {/* Order Type */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Order Type</label>
            <select
              value={tradeForm.orderType}
              onChange={(e) => handleInputChange('orderType', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="Market">Market</option>
              <option value="Limit">Limit</option>
              <option value="SL">SL</option>
              <option value="SL-M">SL-M</option>
            </select>
          </div>

          {/* Stoploss/Target */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Stoploss/Target</div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="stopLossType"
                  checked={tradeForm.stopLossType === 'Points'}
                  onChange={() => handleInputChange('stopLossType', 'Points')}
                  className="text-blue-600"
                />
                <span className="text-sm">Points</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="stopLossType"
                  checked={tradeForm.stopLossType === '%'}
                  onChange={() => handleInputChange('stopLossType', '%')}
                  className="text-blue-600"
                />
                <span className="text-sm">%</span>
              </label>
            </div>
          </div>

          {/* Target */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Target</label>
            <input
              type="text"
              value={tradeForm.target}
              onChange={(e) => handleInputChange('target', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Stop Loss */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Stop Loss</label>
            <input
              type="text"
              value={tradeForm.stopLoss}
              onChange={(e) => handleInputChange('stopLoss', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Trailing */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Trailing</label>
            <input
              type="text"
              value={tradeForm.trailing}
              onChange={(e) => handleInputChange('trailing', e.target.value)}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
            />
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="trailingType"
                  checked={tradeForm.trailingType === 'TSL'}
                  onChange={() => handleInputChange('trailingType', 'TSL')}
                  className="text-blue-600"
                />
                <span className="text-sm">TSL</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="trailingType"
                  checked={tradeForm.trailingType === 'TGT'}
                  onChange={() => handleInputChange('trailingType', 'TGT')}
                  className="text-blue-600"
                />
                <span className="text-sm">TGT</span>
              </label>
            </div>
          </div>

          {/* Custom Port */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Custom Port</label>
            <input
              type="text"
              value={tradeForm.customPort}
              onChange={(e) => handleInputChange('customPort', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Default Port */}
          <div className="flex items-center space-x-3">
            <label className="w-24 text-sm font-medium text-gray-700">Default Port</label>
            <input
              type="text"
              value={tradeForm.defaultPort}
              onChange={(e) => handleInputChange('defaultPort', e.target.value)}
              className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-4 gap-2 mt-6">
            <button
              onClick={() => executeTrade('LE')}
              className="px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              LE
            </button>
            <button
              onClick={() => executeTrade('LX')}
              className="px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              LX
            </button>
            <button
              onClick={() => executeTrade('SE')}
              className="px-3 py-2 bg-orange-600 text-white text-sm rounded hover:bg-orange-700"
            >
              SE
            </button>
            <button
              onClick={() => executeTrade('SX')}
              className="px-3 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
            >
              SX
            </button>
          </div>

          {/* Save Button */}
          <button
            onClick={saveTrade}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mt-4"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default TradingPanel;
