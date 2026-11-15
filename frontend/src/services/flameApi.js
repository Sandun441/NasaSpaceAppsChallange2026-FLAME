/**
 * NASA FLAME API Service Layer
 * Centralized, resilient HTTP client for interacting with the NASA FLAME FastAPI backend.
 * Provides request timeouts, robust error mapping, safe query construction, and graceful offline handling.
 */

const DEFAULT_TIMEOUT_MS = 10000;

// Resolve API Base URL:
// 1. If VITE_API_BASE_URL is explicitly set to empty string "", use relative path for Vite dev proxy.
// 2. If VITE_API_BASE_URL is set to a host (e.g. "http://127.0.0.1:8000"), use that host.
// 3. Fallback to empty string in DEV (proxy mode) or "http://127.0.0.1:8000".
const rawBase = import.meta.env.VITE_API_BASE_URL;
const API_BASE = (rawBase !== undefined ? rawBase : (import.meta.env.DEV ? "" : "http://127.0.0.1:8000")).replace(/\/+$/, "");

/**
 * Standardized API Error representation
 */
export class FlameApiError extends Error {
  constructor(message, status = null, detail = null, isNetworkError = false) {
    super(message);
    this.name = "FlameApiError";
    this.status = status;
    this.detail = detail;
    this.isNetworkError = isNetworkError;
  }
}

/**
 * Generic POST wrapper with timeout and error normalization
 */
async function apiRequestPost(endpoint, body = {}, timeoutMs = 25000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const fullUrl = `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  try {
    const response = await fetch(fullUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let detail = null;
      try {
        const errorData = await response.json();
        detail = errorData.detail || errorData.message || JSON.stringify(errorData);
      } catch {
        detail = response.statusText;
      }
      throw new FlameApiError(
        `Backend API returned error ${response.status}: ${detail || "Unknown error"}`,
        response.status,
        detail,
        false
      );
    }

    return await response.json();
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof FlameApiError) throw err;
    const isTimeout = err.name === "AbortError";
    throw new FlameApiError(
      isTimeout ? `Request timed out after ${timeoutMs}ms` : `Failed to connect to backend: ${err.message}`,
      null,
      err.message,
      true
    );
  }
}

/**
 * Generic fetch wrapper with timeout, parameter encoding, and error normalization
 */
async function apiRequest(endpoint, queryParams = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  // Construct safe query string
  const cleanParams = new URLSearchParams();
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      cleanParams.append(key, String(value));
    }
  });

  const queryString = cleanParams.toString();
  const fullUrl = `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}${queryString ? `?${queryString}` : ""}`;

  try {
    const response = await fetch(fullUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    clearTimeout(timer);

    if (!response.ok) {
      let detail = null;
      try {
        const errorJson = await response.json();
        detail = errorJson.detail || null;
      } catch {
        // Response wasn't JSON
      }

      const statusMessages = {
        400: "Invalid request parameters",
        404: "Requested resource or dataset not found",
        500: "FastAPI internal server error",
        503: "Scientific catalog or dataset file currently unavailable",
      };

      const message = detail || statusMessages[response.status] || `API error (${response.status} ${response.statusText})`;
      throw new FlameApiError(message, response.status, detail, false);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timer);

    if (error instanceof FlameApiError) {
      throw error;
    }

    if (error.name === "AbortError") {
      throw new FlameApiError(
        `Request to ${endpoint} timed out after ${timeoutMs / 1000}s. The backend may be overloaded or unresponsive.`,
        408,
        "Request timeout",
        true
      );
    }

    // Network error (CORS failure, connection refused, offline)
    throw new FlameApiError(
      `Cannot connect to NASA FLAME backend at ${API_BASE}. Ensure the FastAPI server is running on port 8000.`,
      0,
      error.message,
      true
    );
  }
}

export const flameApi = {
  /**
   * Base URL currently configured
   */
  baseUrl: API_BASE,

  /**
   * Health check endpoint
   * GET /api/health
   */
  getHealth: (timeoutMs = 5000) => apiRequest("/api/health", {}, timeoutMs),

  /**
   * List all available datasets with optional category/granularity filters
   * GET /api/datasets
   */
  getDatasets: (filters = {}) => apiRequest("/api/datasets", filters),

  /**
   * Get single dataset catalog information
   * GET /api/datasets/{dataset_id}
   */
  getDataset: (datasetId) => {
    if (!datasetId) throw new Error("datasetId is required");
    return apiRequest(`/api/datasets/${encodeURIComponent(datasetId)}`);
  },

  /**
   * Get scientific instrument metadata for a dataset
   * GET /api/datasets/{dataset_id}/metadata
   */
  getMetadata: (datasetId) => {
    if (!datasetId) throw new Error("datasetId is required");
    return apiRequest(`/api/datasets/${encodeURIComponent(datasetId)}/metadata`);
  },

  /**
   * Get paginated measurement records for a dataset
   * GET /api/datasets/{dataset_id}/records?offset={offset}&limit={limit}
   */
  getRecords: (datasetId, { offset = 0, limit = 50 } = {}) => {
    if (!datasetId) throw new Error("datasetId is required");
    return apiRequest(`/api/datasets/${encodeURIComponent(datasetId)}/records`, {
      offset: Math.max(0, offset),
      limit: Math.min(1000, Math.max(1, limit)),
    });
  },

  /**
   * Fetch a range of records across multiple bounded batches (max 1000 per request)
   * Designed for scientific visualization windows up to multiple thousands of records.
   */
  fetchRecordRange: async (datasetId, { offset = 0, count = 1000, maxTotal = 5000 } = {}) => {
    if (!datasetId) throw new Error("datasetId is required");
    const boundedCount = Math.min(maxTotal, Math.max(1, count));
    const BATCH_SIZE = 1000;
    let currentOffset = Math.max(0, offset);
    let remaining = boundedCount;
    let allRecords = [];
    let detectedColumns = [];
    let totalRecords = 0;
    let scientificValidation = "pending";

    while (remaining > 0) {
      const fetchLimit = Math.min(BATCH_SIZE, remaining);
      const res = await flameApi.getRecords(datasetId, {
        offset: currentOffset,
        limit: fetchLimit,
      });

      const batchRecords = res.records || [];
      if (detectedColumns.length === 0 && res.columns) {
        detectedColumns = res.columns;
      }
      totalRecords = res.total_records || 0;
      if (res.scientific_validation) {
        scientificValidation = res.scientific_validation;
      }

      allRecords = allRecords.concat(batchRecords);
      currentOffset += batchRecords.length;
      remaining -= batchRecords.length;

      // Stop if no more records available from backend
      if (!res.has_more || batchRecords.length < fetchLimit) {
        break;
      }
    }

    return {
      dataset_id: datasetId,
      records: allRecords,
      columns: detectedColumns,
      total_records: totalRecords,
      scientific_validation: scientificValidation,
      offset,
      loaded_count: allRecords.length,
    };
  },

  /**
   * Ping backend to check if it is actively listening
   */
  checkConnection: async () => {
    try {
      const health = await flameApi.getHealth(4000);
      return {
        connected: true,
        data: health,
        error: null,
      };
    } catch (err) {
      return {
        connected: false,
        data: null,
        error: err.message,
      };
    }
  },

  /**
   * Get real scientific telemetry with extrema-preserving decimation and data quality metrics
   * GET /api/datasets/{dataset_id}/telemetry
   */
  getTelemetry: (datasetId, { channels, timeChannel, startTime, endTime, downsamplePoints = 1000 } = {}) => {
    if (!datasetId) throw new Error("datasetId is required");
    const params = {};
    if (channels) params.channels = Array.isArray(channels) ? channels.join(",") : channels;
    if (timeChannel) params.time_channel = timeChannel;
    if (startTime !== undefined && startTime !== null) params.start_time = startTime;
    if (endTime !== undefined && endTime !== null) params.end_time = endTime;
    if (downsamplePoints !== undefined && downsamplePoints !== null) params.downsample_points = downsamplePoints;
    return apiRequest(`/api/datasets/${encodeURIComponent(datasetId)}/telemetry`, params);
  },

  /**
   * Export scientific telemetry dataset to browser CSV download with metadata headers
   */
  exportCsv: (filename, rows = [], columns = [], metadataComments = [], timeColumnAlias = null) => {
    if (!rows.length || !columns.length) return false;

    const lines = [];
    metadataComments.forEach((comment) => {
      lines.push(`# ${comment}`);
    });

    lines.push(columns.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","));

    rows.forEach((row) => {
      const rowVals = columns.map((col) => {
        let val = row[col];
        // If col value is undefined or empty, check whether it is a time axis column and lookup time aliases
        if (
          (val === undefined || val === null || val === "") &&
          (col.toLowerCase().includes("time") || col === timeColumnAlias)
        ) {
          if (row["time"] !== undefined && row["time"] !== null && row["time"] !== "") {
            val = row["time"];
          } else if (
            timeColumnAlias &&
            row[timeColumnAlias] !== undefined &&
            row[timeColumnAlias] !== null &&
            row[timeColumnAlias] !== ""
          ) {
            val = row[timeColumnAlias];
          }
        }
        if (val === undefined || val === null || val === "") return "";
        if (typeof val === "number") return val;
        return `"${String(val).replace(/"/g, '""')}"`;
      });
      lines.push(rowVals.join(","));
    });

    const csvContent = lines.join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename.endsWith(".csv") ? filename : `${filename}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    return true;
  },

  /**
   * Multi-mode scientific search across normalized knowledge records
   */
  searchRag: async (query, topK = 10, mode = 'hybrid', filters = {}) => {
    return await apiRequestPost('/api/rag/search', {
      query,
      top_k: topK,
      mode,
      filters: Object.keys(filters).length > 0 ? filters : null,
    });
  },

  /**
   * Grounded Scientific Assistant question answering
   */
  askAssistant: async (
    question,
    topK = 8,
    filters = {},
    conversationHistory = [],
    findingId = null,
    evidenceId = null,
    earthCategory = null,
    investigationId = null,
  ) => {
    return await apiRequestPost('/api/rag/ask', {
      question,
      top_k: topK,
      filters: Object.keys(filters).length > 0 ? filters : null,
      conversation_history: conversationHistory,
      finding_id: findingId || null,
      evidence_id: evidenceId || null,
      earth_category: earthCategory || null,
      investigation_id: investigationId || null,
    }, 30000);
  },

  /**
   * Investigate an Earth Application finding with Grounded Scientific AI
   * GET /api/earth-applications/{id}/investigate
   */
  investigateEarthApplication: (evidenceId, question = null) => {
    if (!evidenceId) throw new Error('evidenceId is required');
    const params = {};
    if (question) params.question = question;
    return apiRequest(`/api/earth-applications/${encodeURIComponent(evidenceId)}/investigate`, params, 30000);
  },

  /**
   * Directly investigate a detected research gap finding with Grounded Scientific AI
   * GET /api/research-gaps/findings/{finding_id}/investigate
   */
  investigateResearchGap: (findingId) => {
    if (!findingId) throw new Error('findingId is required');
    return apiRequest(`/api/research-gaps/findings/${encodeURIComponent(findingId)}/investigate`, {}, 30000);
  },

  /**
   * Research Gap Detection & Coverage APIs (Phases RG1, RG2, RG3)
   */

  /**
   * Get aggregate summary metrics across all detected scientific research gaps
   * GET /api/research-gaps/summary
   */
  getGapSummary: () => apiRequest('/api/research-gaps/summary'),

  /**
   * Get high-level dataset coverage summary metrics (runs, regimes, materials, raw files)
   * GET /api/research-gaps/coverage/summary
   */
  getCoverageSummary: () => apiRequest('/api/research-gaps/coverage/summary'),

  /**
   * Get coverage heatmap matrix (gravity_vs_oxygen, material_vs_airflow, or all)
   * GET /api/research-gaps/coverage/matrix?matrix_type={type}
   */
  getCoverageMatrix: (matrixType = 'all') =>
    apiRequest('/api/research-gaps/coverage/matrix', { matrix_type: matrixType }),

  /**
   * Query detected research gap findings with optional filtering and heuristic priority sorting
   * GET /api/research-gaps/findings
   */
  getGapFindings: ({ gapType = null, dimension = null, minPriority = 0.0, limit = 50, offset = 0 } = {}) => {
    const params = {};
    if (gapType && gapType !== 'all') params.gap_type = gapType;
    if (dimension && dimension !== 'all') params.dimension = dimension;
    if (minPriority && minPriority > 0) params.min_priority = minPriority;
    if (limit) params.limit = limit;
    if (offset) params.offset = offset;
    return apiRequest('/api/research-gaps/findings', params);
  },

  /**
   * Retrieve full scientific profile and heuristic scoring breakdown for a specific finding
   * GET /api/research-gaps/findings/{finding_id}
   */
  getGapFindingDetail: (findingId) => {
    if (!findingId) throw new Error('findingId is required');
    return apiRequest(`/api/research-gaps/findings/${encodeURIComponent(findingId)}`);
  },

  /**
   * Evaluate empirical dataset coverage for a research question or parameter combination
   * POST /api/research-gaps/analyze
   */
  analyzeResearchGap: async (payload = {}) => {
    return await apiRequestPost('/api/research-gaps/analyze', payload);
  },

  /**
   * Get canonical catalog of all 13 monitored combustion and spacecraft parameters
   * GET /api/research-gaps/coverage/parameters
   */
  getCoverageParameters: () => apiRequest('/api/research-gaps/coverage/parameters'),

  /**
   * Get granular coverage profiles for experiment runs with optional filters
   * GET /api/research-gaps/coverage/experiments
   */
  getCoverageExperiments: ({ investigation = null, fuelFamily = null, gravityRegime = null, oxygenRegime = null, limit = 50, offset = 0 } = {}) => {
    const params = {};
    if (investigation) params.investigation = investigation;
    if (fuelFamily && fuelFamily !== 'all') params.fuel_family = fuelFamily;
    if (gravityRegime && gravityRegime !== 'all') params.gravity_regime = gravityRegime;
    if (oxygenRegime && oxygenRegime !== 'all') params.oxygen_regime = oxygenRegime;
    if (limit) params.limit = limit;
    if (offset) params.offset = offset;
    return apiRequest('/api/research-gaps/coverage/experiments', params);
  },

  /**
   * Evaluate pairwise scientific comparability between two experiments
   * GET /api/research-gaps/coverage/comparability?exp1={id}&exp2={id}
   */
  getCoverageComparability: (exp1, exp2) => {
    if (!exp1 || !exp2) throw new Error('exp1 and exp2 are required');
    return apiRequest('/api/research-gaps/coverage/comparability', { exp1, exp2 });
  },

  // ==========================================
  // Predictive-Modeling Data Extraction APIs
  // ==========================================

  /**
   * List all NASA combustion datasets evaluated for ML modeling
   * GET /api/modeling/datasets
   */
  getModelingDatasets: () => apiRequest('/api/modeling/datasets'),

  /**
   * Retrieve schema and feature registry for a modeling dataset
   * GET /api/modeling/datasets/{dataset_id}
   */
  getModelingDatasetSchema: (datasetId) => {
    if (!datasetId) throw new Error('datasetId is required');
    return apiRequest(`/api/modeling/datasets/${encodeURIComponent(datasetId)}`);
  },

  /**
   * Interpret researcher natural-language objective
   * POST /api/modeling/interpret
   */
  interpretModelingObjective: (query) => {
    return apiRequestPost('/api/modeling/interpret', { query });
  },

  /**
   * Generate preview data rows and quality audit
   * POST /api/modeling/preview
   */
  previewModelingData: (payload) => {
    return apiRequestPost('/api/modeling/preview', payload);
  },

  /**
   * Download real exported file (CSV, JSON metadata, or Markdown report) as Blob
   * POST /api/modeling/export
   */
  exportModelingDataBlob: async (payload = {}) => {
    const fullUrl = `${API_BASE}/api/modeling/export`;
    const response = await fetch(fullUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let errDetail = response.statusText;
      try {
        const json = await response.json();
        errDetail = json.detail || errDetail;
      } catch {
        // fallback
      }
      throw new Error(`Export failed (${response.status}): ${errDetail}`);
    }
    return await response.blob();
  },

  /**
   * Validate whether datasets are compatible for cross-experiment merging
   * POST /api/modeling/validate-merge
   */
  validateModelingMerge: (datasetIds) => {
    return apiRequestPost('/api/modeling/validate-merge', { dataset_ids: datasetIds });
  },

  // ==========================================
  // Fire-Safety Equipment Research APIs
  // ==========================================

  /**
   * Retrieve overview of Fire-Safety Equipment Research module
   * GET /api/equipment-research/overview
   */
  getEquipmentOverview: () => apiRequest('/api/equipment-research/overview'),

  /**
   * Interpret natural-language fire safety inquiry into structured research package
   * POST /api/equipment-research/interpret
   */
  interpretEquipmentResearch: (query, categoryFilter = null) => {
    return apiRequestPost('/api/equipment-research/interpret', {
      query,
      category_filter: categoryFilter,
    });
  },

  /**
   * Retrieve curated deep dive for a specific fire-safety research category
   * GET /api/equipment-research/category/:categoryId
   */
  getEquipmentCategoryDetails: (categoryId) => {
    return apiRequest(`/api/equipment-research/category/${encodeURIComponent(categoryId)}`);
  },

  // ==========================================
  // Earth Applications (Phase EA1) APIs
  // ==========================================

  /**
   * Retrieve all 7 Earth Application categories
   * GET /api/earth-applications/categories
   */
  getEarthApplicationCategories: () => apiRequest('/api/earth-applications/categories'),

  /**
   * Retrieve overview of Earth Applications module
   * GET /api/earth-applications/overview
   */
  getEarthApplicationsOverview: () => apiRequest('/api/earth-applications/overview'),

  /**
   * Query filtered and paginated Earth Application evidence records
   * GET /api/earth-applications
   */
  getEarthApplications: (params = {}) => {
    const queryParts = [];
    if (params.category) queryParts.push(`category=${encodeURIComponent(params.category)}`);
    if (params.classification) queryParts.push(`classification=${encodeURIComponent(params.classification)}`);
    if (params.investigation_id) queryParts.push(`investigation_id=${encodeURIComponent(params.investigation_id)}`);
    if (params.provenance_status) queryParts.push(`provenance_status=${encodeURIComponent(params.provenance_status)}`);
    if (params.limit !== undefined) queryParts.push(`limit=${encodeURIComponent(params.limit)}`);
    if (params.offset !== undefined) queryParts.push(`offset=${encodeURIComponent(params.offset)}`);
    const qs = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
    return apiRequest(`/api/earth-applications${qs}`);
  },

  /**
   * Retrieve single Earth Application evidence record
   * GET /api/earth-applications/:id
   */
  getEarthApplicationById: (id) => {
    return apiRequest(`/api/earth-applications/${encodeURIComponent(id)}`);
  },

  /**
   * Retrieve detailed evidence model for Earth Application finding
   * GET /api/earth-applications/:id/evidence
   */
  getEarthApplicationEvidence: (id) => {
    return apiRequest(`/api/earth-applications/${encodeURIComponent(id)}/evidence`);
  },

  /**
   * Retrieve all Earth Application evidence for a specific NASA investigation
   * GET /api/earth-applications/investigations/:investigationId
   */
  getEarthApplicationsByInvestigation: (investigationId) => {
    return apiRequest(`/api/earth-applications/investigations/${encodeURIComponent(investigationId)}`);
  },

  // ==========================================
  // Shared Prompt Research System (Phase F2)
  // ==========================================

  /**
   * Submit natural-language scientific research inquiry to unified prompt system
   * POST /api/prompt/research
   */
  submitPromptResearch: (payload) => {
    return apiRequestPost('/api/prompt/research', payload, 30000);
  },

  /**
   * Retrieve supported workspace capabilities and example queries
   * GET /api/prompt/capabilities
   */
  getPromptCapabilities: () => {
    return apiRequest('/api/prompt/capabilities');
  },

  // ==========================================
  // Dynamic RAG Knowledge Base Ingestion (Phase P2)
  // ==========================================

  /**
   * Get RAG knowledge store operational status, record counts, and uploaded documents
   * GET /api/rag/knowledge-base
   */
  getKnowledgeBaseOverview: async () => {
    return await apiRequest('/api/rag/knowledge-base');
  },

  /**
   * Upload and ingest a research file into the active RAG store
   * POST /api/rag/upload
   */
  uploadKnowledgeDocument: async (formData) => {
    const res = await fetch(`${API_BASE}/api/rag/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      let detail = 'Upload failed';
      try {
        const errJson = await res.json();
        detail = errJson.detail || errJson.message || detail;
      } catch (e) {
        detail = res.statusText;
      }
      throw new Error(detail);
    }
    return await res.json();
  },

  /**
   * Test immediate retrieval against the active RAG store
   * POST /api/rag/test-search
   */
  testKnowledgeSearch: async (query, topK = 5, mode = 'hybrid') => {
    return await apiRequestPost('/api/rag/test-search', { query, top_k: topK, mode });
  },

  /**
   * Delete an uploaded document and its indexed records
   * DELETE /api/rag/documents/:documentId
   */
  deleteKnowledgeDocument: async (documentId) => {
    const res = await fetch(`${API_BASE}/api/rag/documents/${encodeURIComponent(documentId)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      let detail = 'Delete failed';
      try {
        const errJson = await res.json();
        detail = errJson.detail || detail;
      } catch (e) {
        detail = res.statusText;
      }
      throw new Error(detail);
    }
    return await res.json();
  },
};
