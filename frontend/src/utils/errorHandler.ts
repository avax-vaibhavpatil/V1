// Error handling utilities

export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error
    const data = error.response.data;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (data?.detail) {
      return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    }
    return `Server error: ${error.response.status}`;
  } else if (error.request) {
    // Request made but no response
    return 'No response from server. Is the backend running?';
  } else {
    // Error setting up request
    return error.message || 'Unknown error occurred';
  }
};

