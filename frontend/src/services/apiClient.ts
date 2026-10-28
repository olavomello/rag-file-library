export const API_BASE_URL = '/api/v1';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function parseError(response: Response, path: string): Promise<ApiError> {
  let detail: string | undefined;
  try {
    const body = await response.json();
    detail = typeof body?.detail === 'string' ? body.detail : undefined;
  } catch {
    detail = undefined;
  }
  return new ApiError(`${path} failed (${response.status})`, response.status, detail);
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) throw await parseError(response, `GET ${path}`);
  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) throw await parseError(response, `POST ${path}`);
  return (await response.json()) as T;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'PATCH',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw await parseError(response, `PATCH ${path}`);
  return (await response.json()) as T;
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: 'DELETE' });
  if (!response.ok && response.status !== 204) {
    throw await parseError(response, `DELETE ${path}`);
  }
}

export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE_URL}${path}`, { method: 'POST', body: form });
  if (!response.ok) throw await parseError(response, `POST ${path}`);
  return (await response.json()) as T;
}

/** Upload a file via XHR so upload progress can be reported through `onProgress`. */
export async function apiUploadWithProgress<T>(
  path: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<T> {
  const form = new FormData();
  form.append('file', file);

  return new Promise<T>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}${path}`);
    xhr.responseType = 'text';
    xhr.setRequestHeader('Accept', 'application/json');

    if (onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
    }

    const fail = (): void => {
      let detail: string | undefined;
      try {
        const body = JSON.parse(xhr.responseText) as { detail?: unknown };
        detail = typeof body.detail === 'string' ? body.detail : undefined;
      } catch {
        detail = undefined;
      }
      reject(new ApiError(`POST ${path} failed (${xhr.status})`, xhr.status, detail));
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as T);
        } catch {
          reject(new ApiError(`POST ${path} returned invalid JSON`, xhr.status));
        }
      } else {
        fail();
      }
    };
    xhr.onerror = () => reject(new ApiError(`POST ${path} failed (network error)`, 0));
    xhr.send(form);
  });
}

/** POST a JSON body and yield newline-delimited JSON events from the response. */
export async function* apiPostStream<T>(
  path: string,
  body: unknown,
  signal?: AbortSignal
): AsyncGenerator<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/x-ndjson', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) throw await parseError(response, `POST ${path}`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline = buffer.indexOf('\n');
    while (newline !== -1) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) yield JSON.parse(line) as T;
      newline = buffer.indexOf('\n');
    }
  }
  const tail = buffer.trim();
  if (tail) yield JSON.parse(tail) as T;
}
