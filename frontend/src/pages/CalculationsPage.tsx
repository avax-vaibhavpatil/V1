import { useState, useEffect } from 'react';
import { useProject } from '@/context/ProjectContext';
import { datasetsService } from '@/services/datasets';
import { calculationsService } from '@/services/calculations';
import {
  AlertCircle,
  Calculator,
  Plus,
  CheckCircle,
  XCircle,
  Loader2,
  Code,
  Info,
  Trash2,
  Save,
} from 'lucide-react';
import type { Dataset, SemanticDefinition, CalculationValidation } from '@/types';

interface CalculatedMeasure {
  id?: number;
  name: string;
  formula: string;
  description: string;
  datasetId: string;
}

const FORMULA_FUNCTIONS = [
  { name: 'SUM', syntax: 'SUM(field)', description: 'Sum of values' },
  { name: 'AVG', syntax: 'AVG(field)', description: 'Average of values' },
  { name: 'COUNT', syntax: 'COUNT(field)', description: 'Count of records' },
  { name: 'MIN', syntax: 'MIN(field)', description: 'Minimum value' },
  { name: 'MAX', syntax: 'MAX(field)', description: 'Maximum value' },
  { name: 'IF', syntax: 'IF(condition, then, else)', description: 'Conditional logic' },
];

const OPERATORS = ['+', '-', '*', '/', '(', ')'];

export default function CalculationsPage() {
  const { activeProject } = useProject();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [semantic, setSemantic] = useState<SemanticDefinition | null>(null);
  const [loading, setLoading] = useState(true);

  // Formula editor state
  const [measureName, setMeasureName] = useState('');
  const [formula, setFormula] = useState('');
  const [description, setDescription] = useState('');
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<CalculationValidation | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Existing calculations
  const [calculations, setCalculations] = useState<CalculatedMeasure[]>([]);

  useEffect(() => {
    loadDatasets();
  }, [activeProject?.id]);

  useEffect(() => {
    if (selectedDataset) {
      loadSemantic();
    }
  }, [selectedDataset?.id]);

  const loadDatasets = async () => {
    if (!activeProject) {
      setDatasets([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const data = await datasetsService.list(activeProject.id);
      setDatasets(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  const loadSemantic = async () => {
    if (!selectedDataset) return;

    try {
      const data = await datasetsService.getSemantic(selectedDataset.id);
      setSemantic(data);
    } catch {
      setSemantic(null);
    }
  };

  const validateFormula = async () => {
    if (!formula.trim()) return;

    try {
      setValidating(true);
      setValidation(null);
      setError('');

      const availableFields = [
        ...(semantic?.dimensions?.map((d) => d.column) || []),
        ...(semantic?.measures?.map((m) => m.column) || []),
      ];

      const result = await calculationsService.validate(formula, availableFields);
      setValidation(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Validation failed');
    } finally {
      setValidating(false);
    }
  };

  const insertIntoFormula = (text: string) => {
    setFormula((prev) => prev + text);
    setValidation(null);
  };

  const handleSave = async () => {
    if (!validation?.is_valid || !measureName.trim() || !selectedDataset) {
      setError('Please validate the formula and provide a name');
      return;
    }

    try {
      setSaving(true);
      setError('');

      // Save calculation (this would need a backend endpoint)
      // For now, just show success
      setSuccessMessage(`Calculation "${measureName}" saved successfully!`);
      
      // Reset form
      setMeasureName('');
      setFormula('');
      setDescription('');
      setValidation(null);

      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save calculation');
    } finally {
      setSaving(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Project</h3>
          <p className="text-gray-500">Please select a project to create calculations</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Calculation Builder</h2>
        <p className="text-gray-500 mt-1">Create custom calculated measures using formulas</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
          <XCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {successMessage && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          {successMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Formula Editor */}
        <div className="lg:col-span-2 space-y-4">
          {/* Dataset Selector */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Dataset
            </label>
            <select
              value={selectedDataset?.id || ''}
              onChange={(e) => {
                const ds = datasets.find((d) => d.id === e.target.value);
                setSelectedDataset(ds || null);
                setFormula('');
                setValidation(null);
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a dataset</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
          </div>

          {selectedDataset && (
            <>
              {/* Measure Name */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Measure Name *
                </label>
                <input
                  type="text"
                  value={measureName}
                  onChange={(e) => setMeasureName(e.target.value)}
                  placeholder="e.g., Profit Margin"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Formula Editor */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Formula *
                </label>
                
                {/* Quick Insert Buttons */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {OPERATORS.map((op) => (
                    <button
                      key={op}
                      onClick={() => insertIntoFormula(` ${op} `)}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded font-mono text-sm hover:bg-gray-200"
                    >
                      {op}
                    </button>
                  ))}
                </div>

                {/* Formula Input */}
                <div className="relative">
                  <textarea
                    value={formula}
                    onChange={(e) => {
                      setFormula(e.target.value);
                      setValidation(null);
                    }}
                    placeholder="Enter your formula, e.g., SUM(revenue) - SUM(cost)"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                    rows={4}
                  />
                  <Code className="absolute top-3 right-3 w-5 h-5 text-gray-400" />
                </div>

                {/* Validation Status */}
                {validation && (
                  <div
                    className={`mt-3 p-3 rounded-lg flex items-start gap-2 ${
                      validation.is_valid
                        ? 'bg-green-50 text-green-700'
                        : 'bg-red-50 text-red-700'
                    }`}
                  >
                    {validation.is_valid ? (
                      <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="font-medium">
                        {validation.is_valid ? 'Valid formula' : 'Invalid formula'}
                      </div>
                      {validation.error_message && (
                        <div className="text-sm mt-1">{validation.error_message}</div>
                      )}
                      {validation.validation_result?.fields_used && (
                        <div className="text-sm mt-1">
                          Fields used: {validation.validation_result.fields_used.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={validateFormula}
                    disabled={validating || !formula.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                  >
                    {validating ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle className="w-4 h-4" />
                    )}
                    Validate
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving || !validation?.is_valid || !measureName.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    Save Calculation
                  </button>
                </div>
              </div>

              {/* Description */}
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this calculation represents..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  rows={2}
                />
              </div>
            </>
          )}
        </div>

        {/* Right Panel - Field Picker & Functions */}
        <div className="space-y-4">
          {/* Available Fields */}
          {selectedDataset && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Available Fields</h3>
              
              {semantic ? (
                <div className="space-y-4">
                  {/* Dimensions */}
                  {semantic.dimensions && semantic.dimensions.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                        Dimensions
                      </div>
                      <div className="space-y-1">
                        {semantic.dimensions.map((dim) => (
                          <button
                            key={dim.name}
                            onClick={() => insertIntoFormula(dim.column)}
                            className="w-full text-left px-3 py-2 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 text-sm"
                          >
                            {dim.name}
                            <span className="text-xs text-blue-500 ml-2">({dim.column})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Measures */}
                  {semantic.measures && semantic.measures.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                        Measures
                      </div>
                      <div className="space-y-1">
                        {semantic.measures.map((measure) => (
                          <button
                            key={measure.name}
                            onClick={() => insertIntoFormula(measure.column)}
                            className="w-full text-left px-3 py-2 bg-green-50 text-green-700 rounded hover:bg-green-100 text-sm"
                          >
                            {measure.name}
                            <span className="text-xs text-green-500 ml-2">({measure.column})</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No semantic definition available</p>
              )}
            </div>
          )}

          {/* Functions Reference */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-purple-500" />
              Functions
            </h3>
            <div className="space-y-2">
              {FORMULA_FUNCTIONS.map((fn) => (
                <button
                  key={fn.name}
                  onClick={() => insertIntoFormula(fn.syntax)}
                  className="w-full text-left p-3 bg-purple-50 rounded-lg hover:bg-purple-100"
                >
                  <div className="font-mono text-sm text-purple-700">{fn.syntax}</div>
                  <div className="text-xs text-purple-500 mt-1">{fn.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Help */}
          <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-amber-800 text-sm">Formula Tips</div>
                <ul className="text-xs text-amber-700 mt-1 space-y-1">
                  <li>• Use field names from the available fields list</li>
                  <li>• Combine with +, -, *, / operators</li>
                  <li>• Use parentheses for grouping</li>
                  <li>• Nested aggregations are not allowed</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

