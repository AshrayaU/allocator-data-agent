// Shared TypeScript types for allocator-qa.
// Add types that are used across multiple pages or components here.

/** Generic paginated response from the backend. */
export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  size: number
}

/** Standard API error shape from the backend. */
export interface ApiErrorDetail {
  detail: string
}
