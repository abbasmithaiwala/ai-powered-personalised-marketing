// Frontend type definitions mirroring backend API schemas

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ErrorResponse {
  detail: string;
  code?: string;
}

// Brand types
export interface Brand {
  id: string;
  name: string;
  slug: string;
  cuisine_type: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BrandCreate {
  name: string;
  slug?: string;
  cuisine_type?: string;
  is_active?: boolean;
}

// Menu Item types
export interface MenuItem {
  id: string;
  brand_id: string;
  name: string;
  description: string | null;
  category: string | null;
  cuisine_type: string | null;
  price: number | null;
  dietary_tags: string[];
  flavor_tags: string[];
  is_available: boolean;
  embedding_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MenuItemCreate {
  brand_id: string;
  name: string;
  description?: string;
  category?: string;
  cuisine_type?: string;
  price?: number;
  dietary_tags?: string[];
  flavor_tags?: string[];
  is_available?: boolean;
}

// Customer types
export interface Customer {
  id: string;
  external_id: string | null;
  email: string | null;
  phone: string | null;
  first_name: string | null;
  last_name: string | null;
  city: string | null;
  total_orders: number;
  total_spend: number;
  first_order_at: string | null;
  last_order_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerPreference {
  id: string;
  customer_id: string;
  favorite_cuisines: Record<string, number>;
  favorite_categories: Record<string, number>;
  dietary_flags: Record<string, boolean>;
  price_sensitivity: 'low' | 'medium' | 'high' | null;
  order_frequency: 'daily' | 'weekly' | 'monthly' | 'occasional' | null;
  brand_affinity: Array<{ brand_id: string; score: number }>;
  preferred_order_times: Record<string, number>;
  last_computed_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

// Order types
export interface Order {
  id: string;
  external_id: string | null;
  customer_id: string;
  brand_id: string;
  order_date: string;
  total_amount: number;
  channel: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  order_id: string;
  menu_item_id: string | null;
  item_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

// Recommendation types
export interface RecommendationItem {
  menu_item_id: string;
  name: string;
  brand_name: string;
  score: number;
  reason: string;
  price: number | null;
  category: string | null;
}

export interface RecommendationResponse {
  items: RecommendationItem[];
  computed_at: string;
}

// Ingestion types
export interface IngestionJob {
  id: string;
  filename: string;
  csv_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_rows: number | null;
  processed_rows: number | null;
  failed_rows: number | null;
  validation_errors: any;
  result_summary: any;
  created_at: string;
  updated_at: string;
}

export interface IngestionUploadResponse {
  job_id: string;
  status: string;
  validation_summary: any;
  total_rows: number;
}

// Campaign types
export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  purpose: string | null;
  status: 'draft' | 'previewing' | 'ready' | 'executing' | 'completed' | 'failed';
  segment_filters: SegmentFilters;
  total_recipients: number;
  generated_count: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  purpose?: string;
  segment_filters: SegmentFilters;
}

export interface CampaignRecipient {
  id: string;
  campaign_id: string;
  customer_id: string;
  generated_message: GeneratedMessage | null;
  status: 'pending' | 'generated' | 'failed';
  error_message: string | null;
  created_at: string;
}

export interface GeneratedMessage {
  subject: string;
  body: string;
}

// Segmentation types
export interface SegmentFilters {
  last_order_after?: string;
  last_order_before?: string;
  total_spend_min?: number;
  total_spend_max?: number;
  total_orders_min?: number;
  favorite_cuisine?: string;
  dietary_flag?: string;
  city?: string;
  order_frequency?: 'daily' | 'weekly' | 'monthly' | 'occasional';
  brand_id?: string;
}

export interface SegmentCountResponse {
  count: number;
}

// Dashboard metrics
export interface DashboardMetrics {
  total_customers: number;
  total_orders_30d: number;
  active_campaigns: number;
  messages_generated: number;
}
