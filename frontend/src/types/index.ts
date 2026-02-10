// Enums
export type Role = 'admin' | 'customer';
export type OrderStatus = 'pending_payment' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';

// Auth
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Categories
export interface CategoryResponse {
  id: string;
  name: string;
  slug: string;
  description: string | null;
}

export interface CategoryCreate {
  name: string;
  slug: string;
  description?: string | null;
}

export interface CategoryUpdate {
  name?: string | null;
  slug?: string | null;
  description?: string | null;
}

// Products
export interface ProductImageResponse {
  id: string;
  url: string;
  alt_text: string | null;
  sort_order: number;
}

export interface ProductListItem {
  id: string;
  name: string;
  slug: string;
  price: number;
  stock: number;
  category: CategoryResponse;
  thumbnail: string | null;
}

export interface ProductDetail {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  price: number;
  stock: number;
  is_active: boolean;
  category: CategoryResponse;
  images: ProductImageResponse[];
}

export interface ProductCreate {
  name: string;
  slug: string;
  description?: string | null;
  price: number;
  stock?: number;
  category_id: string;
  is_active?: boolean;
}

export interface ProductUpdate {
  name?: string | null;
  slug?: string | null;
  description?: string | null;
  price?: number | null;
  stock?: number | null;
  category_id?: string | null;
  is_active?: boolean | null;
}

export interface PaginatedProducts {
  items: ProductListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Cart
export interface CartItemResponse {
  id: string;
  product_id: string;
  product_name: string;
  product_price: number;
  quantity: number;
  subtotal: number;
}

export interface CartResponse {
  id: string;
  items: CartItemResponse[];
  total: number;
}

export interface CartItemAdd {
  product_id: string;
  quantity?: number;
}

export interface CartItemUpdate {
  quantity: number;
}

// Orders
export interface OrderItemResponse {
  id: string;
  product_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
}

export interface OrderResponse {
  id: string;
  status: OrderStatus;
  total: number;
  shipping_name: string;
  shipping_address: string;
  shipping_city: string;
  shipping_zip: string;
  payment_method: string;
  payment_note: string | null;
  items: OrderItemResponse[];
  created_at: string;
}

export interface OrderListItem {
  id: string;
  status: OrderStatus;
  total: number;
  created_at: string;
  item_count: number;
}

export interface PaginatedOrders {
  items: OrderListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface CreateOrderRequest {
  shipping_name: string;
  shipping_address: string;
  shipping_city: string;
  shipping_zip: string;
  payment_method?: string;
  payment_note?: string | null;
}

export interface UpdateOrderStatusRequest {
  status: OrderStatus;
}

// Common
export interface ErrorDetail {
  field: string | null;
  detail: string;
}

export interface ApiResponse<T = unknown> {
  data: T;
  message: string;
  errors: ErrorDetail[];
}

// Audit Logs
export interface AuditLog {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string | null;
  created_at: string;
}

export interface PaginatedAuditLogs {
  items: AuditLog[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
